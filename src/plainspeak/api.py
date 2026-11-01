"""HTTP JSON API. The backend owns workflow state, validation and all writes."""

import hashlib
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from plainspeak import voice
from plainspeak.ai import tools
from plainspeak.ai.agent import run_chat
from plainspeak.ai.client import LLM, AIError
from plainspeak.ai.summary import generate_draft
from plainspeak.config import Settings, get_settings
from plainspeak.contracts import (
    ApproveRequest,
    ApproveTask,
    CareTask,
    Case,
    CaseView,
    ChatRequest,
    ChatResponse,
    CreateCaseRequest,
    Message,
    Passage,
    Source,
    SpeakerRole,
    SummaryVersion,
    TaskView,
    TranscriptRequest,
    TranscriptSegment,
    UnresolvedQuestion,
    utc_now,
)
from plainspeak.pdf_extract import (
    NoTextError,
    extract_lines,
    extract_passages,
    extract_patient_name,
)
from plainspeak.storage import CaseNotFoundError, CaseStore, new_id
from plainspeak.transcript_import import TranscriptFormatError, parse_transcript

DEFAULT_CASE_ID = "default"
DOCUMENT_SOURCE_ID = "discharge_001"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_TASK_ID = re.compile(r"^task_\d{3}$")
_SAFE_SLUG = re.compile(r"[^a-z0-9]+")

router = APIRouter(prefix="/api")


def get_store(request: Request) -> CaseStore:
    return request.app.state.store


def get_llm(request: Request) -> LLM:
    return request.app.state.llm


Store = Annotated[CaseStore, Depends(get_store)]
Claude = Annotated[LLM, Depends(get_llm)]


def _slug(raw: str) -> str:
    """Turn a free-form string into a safe, lowercase case-ID slug."""
    return _SAFE_SLUG.sub("-", raw.lower().strip()).strip("-")[:64] or DEFAULT_CASE_ID


def _load(store: CaseStore, case_id: str) -> Case:
    try:
        return store.load(case_id)
    except CaseNotFoundError as e:
        raise HTTPException(404, "Case not found.") from e


def _view(case: Case) -> CaseView:
    tasks = []
    for task in case.care_tasks:
        events = [
            e
            for e in case.progress_events
            if e.task_id == task.id and e.approved_summary_version == case.approved_summary_version
        ]
        tasks.append(
            TaskView(
                **task.model_dump(),
                status=case.task_status(task.id),
                last_event=events[-1] if events else None,
            )
        )
    return CaseView(case=case, checklist=tasks)


# ── Health & meta ──────────────────────────────────────────────────────────────


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — returns 200 when the service is up."""
    return {"status": "ok", "service": "plainspeak", "version": "1.0.0"}


@router.get("/info")
def runtime_info(request: Request) -> dict[str, str]:
    """Returns active AI backend and model — consumed by the topbar badge."""
    from plainspeak.ai.client import GroqClient, OllamaClient, OpenRouterClient
    llm = request.app.state.llm
    if isinstance(llm, OpenRouterClient):
        backend = "openrouter"
    elif isinstance(llm, GroqClient):
        backend = "groq"
    elif isinstance(llm, OllamaClient):
        backend = "ollama"
    else:
        backend = "claude"
    model = getattr(llm, "_model", "unknown")
    return {"backend": backend, "model": model, "version": "1.0.0"}


# ── Cases ──────────────────────────────────────────────────────────────────────


@router.get("/cases")
def list_cases(store: Store) -> list[dict]:
    """Return summary metadata for all cases, newest first."""
    results = []
    for path in sorted(store.cases_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            case = store.load(path.stem)
            results.append(
                {
                    "caseId": case.case_id,
                    "patientName": case.patient_name,
                    "workflowState": case.workflow_state,
                    "hasSources": bool(case.sources),
                    "approvedVersion": case.approved_summary_version,
                }
            )
        except Exception:  # noqa: BLE001
            pass
    return results


@router.post("/cases")
def create_case(store: Store, body: CreateCaseRequest | None = None) -> CaseView:
    reset = body.reset if body else False
    raw_id = (body.case_id or "").strip() if body else ""
    case_id = _slug(raw_id) if raw_id else DEFAULT_CASE_ID
    return _view(store.create(case_id, reset=reset))


@router.get("/cases/{case_id}")
def get_case(case_id: str, store: Store) -> CaseView:
    return _view(_load(store, case_id))


# ── Voice ──────────────────────────────────────────────────────────────────────


@router.post("/voice/token")
def voice_token(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    try:
        return voice.request_token(settings.reson8_api_key)
    except voice.VoiceError as e:
        raise HTTPException(503, str(e)) from e


# ── Documents ──────────────────────────────────────────────────────────────────


def _read_pdf_upload(file: UploadFile) -> bytes:
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF is larger than 10 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Upload a text-based PDF file.")
    return data


@router.post("/cases/{case_id}/document")
def upload_document(case_id: str, file: UploadFile, store: Store) -> CaseView:
    """Replace the case's discharge document. One document per patient case."""
    _load(store, case_id)
    data = _read_pdf_upload(file)
    filename = (file.filename or "document.pdf")[:120]
    path = store.upload_path(case_id, DOCUMENT_SOURCE_ID)
    path.write_bytes(data)
    try:
        passages = extract_passages(path)
    except NoTextError as e:
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(e)) from e
    patient_name = extract_patient_name(path)

    with store.update(case_id) as case:
        case.patient_name = patient_name
        current = next((s for s in case.sources if s.kind == "document"), None)
        if current and current.filename == filename and current.passages == passages:
            return _view(case)
        for stale in (s for s in case.sources if s.kind == "document"):
            if stale.id != DOCUMENT_SOURCE_ID:
                store.upload_path(case_id, stale.id).unlink(missing_ok=True)
        case.sources = [s for s in case.sources if s.kind != "document"] + [
            Source(
                id=DOCUMENT_SOURCE_ID,
                filename=filename,
                uploaded_at=utc_now(),
                passages=passages,
            )
        ]
        case.draft_summary = None
        case.workflow_state = "awaiting_review"
        case.input_revision += 1
    return _view(case)


# ── Transcript ─────────────────────────────────────────────────────────────────


def _apply_transcript(
    store: CaseStore,
    case_id: str,
    segments: list[TranscriptSegment],
    speaker_roles: dict[str, SpeakerRole],
    *,
    replace: bool = False,
) -> Case:
    """Append final consultation segments; retries cannot duplicate or silently edit them."""
    with store.update(case_id) as case:
        changed = False
        if replace and {s.id for s in case.transcript_segments} != {s.id for s in segments}:
            case.transcript_segments = []
            case.speaker_roles = {}
            changed = True
        existing = {segment.id: segment for segment in case.transcript_segments}
        for segment in segments:
            if not segment.text.strip():
                raise HTTPException(422, "Transcript text must not be empty.")
            previous = existing.get(segment.id)
            if previous:
                fields = {"recorded_at"}
                if previous.model_dump(exclude=fields) != segment.model_dump(exclude=fields):
                    raise HTTPException(409, "A saved segment cannot be overwritten.")
                continue
            saved = segment.model_copy(update={"recorded_at": utc_now()})
            case.transcript_segments.append(saved)
            existing[saved.id] = saved
            changed = True
        known_speakers = {segment.speaker_key() for segment in case.transcript_segments}
        for key, role in speaker_roles.items():
            if key not in known_speakers:
                raise HTTPException(422, "Speaker mapping must reference a saved speaker.")
            if case.speaker_roles.get(key, "unknown") != role:
                case.speaker_roles[key] = role
                changed = True
        if changed:
            passages = []
            for segment in case.transcript_segments:
                role = case.speaker_roles.get(segment.speaker_key(), "unknown")
                label = (
                    role if role != "unknown" else f"unconfirmed speaker {segment.speaker_key()}"
                )
                offset = f" at {segment.start_ms}ms" if segment.start_ms is not None else ""
                passages.append(
                    Passage(
                        id=segment.id,
                        page=0,
                        text=f"[{label}{offset}] {segment.text.strip()}",
                    )
                )
            source = Source(
                id="consultation_001",
                filename="Consultation transcript",
                kind="consultation",
                uploaded_at=utc_now(),
                passages=passages,
            )
            case.sources = [s for s in case.sources if s.id != source.id] + [source]
            case.input_revision += 1
            case.draft_summary = None
            case.workflow_state = "awaiting_review"
    return case


@router.post("/cases/{case_id}/transcript")
def save_transcript(case_id: str, body: TranscriptRequest, store: Store) -> CaseView:
    _load(store, case_id)
    return _view(_apply_transcript(store, case_id, body.segments, body.speaker_roles))


@router.post("/cases/{case_id}/transcript/document")
def upload_transcript(case_id: str, file: UploadFile, store: Store) -> CaseView:
    """Import a written transcript PDF as consultation segments."""
    case = _load(store, case_id)
    data = _read_pdf_upload(file)
    digest = hashlib.sha256(data).hexdigest()[:16]
    session_id = f"pdf_{digest}"
    path = store.upload_path(case_id, f"transcript_{digest}")
    path.write_bytes(data)
    try:
        segments, roles = parse_transcript(extract_lines(path), session_id)
    except (NoTextError, TranscriptFormatError) as e:
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(e)) from e
    roles = {k: v for k, v in roles.items() if case.speaker_roles.get(k, "unknown") == "unknown"}
    return _view(_apply_transcript(store, case_id, segments, roles, replace=True))


@router.post("/cases/{case_id}/transcript/clear")
def clear_transcript(case_id: str, store: Store) -> CaseView:
    """Remove all transcript segments. Only available before approval."""
    _load(store, case_id)
    with store.update(case_id) as case:
        if case.approved_summary_version is not None:
            raise HTTPException(409, "Cannot clear the transcript after a version has been approved.")
        case.transcript_segments = []
        case.speaker_roles = {}
        case.sources = [s for s in case.sources if s.kind != "consultation"]
        case.draft_summary = None
        case.workflow_state = "awaiting_review"
        case.input_revision += 1
    return _view(case)


# ── Summary & approval ─────────────────────────────────────────────────────────


@router.post("/cases/{case_id}/summary")
def create_summary(case_id: str, store: Store, llm: Claude) -> CaseView:
    case = _load(store, case_id)
    try:
        draft = generate_draft(llm, case)
    except AIError as e:
        raise HTTPException(502, str(e)) from e
    with store.update(case_id) as case:
        if case.input_revision != draft.input_revision:
            raise HTTPException(409, "Sources changed while drafting. Generate again.")
        case.draft_summary = draft
        case.workflow_state = "awaiting_review"
    return _view(case)


@router.post("/cases/{case_id}/approve")
def approve(case_id: str, body: ApproveRequest, store: Store) -> CaseView:
    if not body.summary.strip():
        raise HTTPException(422, "Summary must not be empty.")
    if not body.care_tasks:
        raise HTTPException(422, "Approve at least one care task.")
    if not body.approved_by.strip():
        raise HTTPException(422, "Approving clinician name must not be empty.")
    _load(store, case_id)
    with store.update(case_id) as case:
        if not case.sources:
            raise HTTPException(409, "Capture a consultation or upload a document first.")
        if body.input_revision is not None and body.input_revision != case.input_revision:
            raise HTTPException(409, "Inputs changed. Generate and review a fresh draft.")
        known = case.passage_index()
        used_ids = {t.id for t in body.care_tasks if t.id and _TASK_ID.match(t.id)}
        next_number = 1
        seen: set[str] = set()
        tasks: list[CareTask] = []
        for task in body.care_tasks:
            if not task.instruction.strip():
                raise HTTPException(422, "Care task instructions must not be empty.")
            bad = [r for r in task.source_refs if (r.source_id, r.passage_id) not in known]
            if bad:
                raise HTTPException(422, f"Unknown source reference {bad[0].passage_id!r}.")
            task_id = task.id if task.id and _TASK_ID.match(task.id) else None
            if task_id is None or task_id in seen:
                while f"task_{next_number:03d}" in used_ids | seen:
                    next_number += 1
                task_id = f"task_{next_number:03d}"
            seen.add(task_id)
            tasks.append(CareTask(**task.model_dump(exclude={"id"}), id=task_id))

        version = SummaryVersion(
            version=len(case.summary_versions) + 1,
            summary=body.summary.strip(),
            care_tasks=tasks,
            source_ids=[s.id for s in case.sources],
            approved_by=body.approved_by.strip()[:80],
            approved_at=utc_now(),
            input_revision=case.input_revision,
            sources_snapshot=[source.model_copy(deep=True) for source in case.sources],
        )
        case.summary_versions.append(version)
        case.approved_summary_version = version.version
        case.care_tasks = tasks
        case.draft_summary = None
        case.workflow_state = "approved"
    return _view(case)


# ── Chat ───────────────────────────────────────────────────────────────────────


@router.post("/cases/{case_id}/chat")
def chat(case_id: str, body: ChatRequest, store: Store, llm: Claude) -> ChatResponse:
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Message must not be empty.")
    if len(text) > 2000:
        raise HTTPException(422, "Message is too long.")
    case = _load(store, case_id)
    if not case.post_care_ready():
        raise HTTPException(409, "Post-care questions open once a clinician approves the summary.")

    question = Message(id=new_id("msg"), role="caregiver", text=text, created_at=utc_now())
    with store.update(case_id) as case:
        case.messages.append(question)

    try:
        reply = run_chat(llm, store, case_id, text)
    except AIError as e:
        raise HTTPException(502, str(e)) from e

    answer = Message(
        id=new_id("msg"), role="assistant", text=reply.text, created_at=utc_now(), reply=reply
    )
    with store.update(case_id) as case:
        case.messages.append(answer)
        if reply.kind == "unresolved":
            case.unresolved_questions.append(
                UnresolvedQuestion(
                    id=new_id("q"), question=text, message_id=question.id, created_at=utc_now()
                )
            )
        if case.workflow_state == "approved":
            case.workflow_state = "post_care_active"
    return ChatResponse(message=question, reply=answer)


# ── Progress updates ───────────────────────────────────────────────────────────


@router.post("/cases/{case_id}/updates/{update_id}/confirm")
def confirm_update(case_id: str, update_id: str, store: Store) -> CaseView:
    _load(store, case_id)
    try:
        tools.record_progress_update(store, case_id, update_id, actor="caregiver")
    except tools.ToolError as e:
        raise HTTPException(409, str(e)) from e
    return _view(store.load(case_id))


@router.post("/cases/{case_id}/updates/{update_id}/reject")
def reject_update(case_id: str, update_id: str, store: Store) -> CaseView:
    _load(store, case_id)
    try:
        tools.reject_progress_update(store, case_id, update_id)
    except tools.ToolError as e:
        raise HTTPException(409, str(e)) from e
    return _view(store.load(case_id))


# ── Demo seed ──────────────────────────────────────────────────────────────────

_DEMO_SEGMENTS: list[TranscriptSegment] = [
    TranscriptSegment(id="ds001", session_id="demo_session", speaker_id=0, text="Good morning. How are you feeling after the procedure?"),
    TranscriptSegment(id="ds002", session_id="demo_session", speaker_id=1, text="A bit sore and tired, but relieved it's over."),
    TranscriptSegment(id="ds003", session_id="demo_session", speaker_id=0, text="Completely normal. The laparoscopic cholecystectomy went very well — no complications at all. We successfully removed the gallbladder."),
    TranscriptSegment(id="ds004", session_id="demo_session", speaker_id=1, text="When can I eat normally again?"),
    TranscriptSegment(id="ds005", session_id="demo_session", speaker_id=0, text="Start with clear fluids today — water, broth, diluted juice. Move to soft foods like soup and yoghurt tomorrow. Avoid fatty, fried, or spicy food for at least two weeks while your liver adjusts."),
    TranscriptSegment(id="ds006", session_id="demo_session", speaker_id=1, text="What should I take for the pain?"),
    TranscriptSegment(id="ds007", session_id="demo_session", speaker_id=0, text="Take paracetamol one gram every six hours as needed — maximum four times a day, always with food or water. If that's insufficient, you can add ibuprofen 400mg up to three times a day, but only with meals and only if you have no stomach problems."),
    TranscriptSegment(id="ds008", session_id="demo_session", speaker_id=1, text="How long before I can drive?"),
    TranscriptSegment(id="ds009", session_id="demo_session", speaker_id=0, text="No driving for at least 48 hours after your last dose of strong pain medicine. Only resume once you can perform an emergency stop comfortably without abdominal pain. Most patients are back to driving within a week."),
    TranscriptSegment(id="ds010", session_id="demo_session", speaker_id=0, text="Keep the wound dressings dry for the first 48 hours. After that you can shower normally — just pat the area dry gently afterwards. Watch for redness, swelling, discharge, or an unusual smell around the wounds."),
    TranscriptSegment(id="ds011", session_id="demo_session", speaker_id=1, text="When do I need to come back?"),
    TranscriptSegment(id="ds012", session_id="demo_session", speaker_id=0, text="I want to see you at the outpatient clinic in two weeks for a wound check. If before then you develop a fever above 38 degrees Celsius, severe abdominal pain not relieved by paracetamol, yellowing of your skin or eyes, or you cannot keep fluids down, please go straight to A&E."),
    TranscriptSegment(id="ds013", session_id="demo_session", speaker_id=1, text="That's very clear, thank you."),
    TranscriptSegment(id="ds014", session_id="demo_session", speaker_id=0, text="Great. Our nurse will provide a printed copy of these instructions. Any other questions?"),
]

_DEMO_ROLES: dict[str, str] = {
    "demo_session:0": "clinician",
    "demo_session:1": "patient",
}

_DEMO_APPROVE = ApproveRequest(
    summary=(
        "Emily Carter underwent an uncomplicated laparoscopic cholecystectomy (keyhole gallbladder removal). "
        "The procedure was completed without complications. She can expect mild abdominal soreness and fatigue for up to two weeks. "
        "She should start clear fluids today and progress gradually to a normal diet, avoiding fatty and spicy foods for two weeks. "
        "Pain can be managed with paracetamol, and ibuprofen added if needed. "
        "Wound dressings should remain dry for 48 hours, then normal showering can resume with gentle drying. "
        "She should not drive until fully comfortable performing emergency stops. "
        "A follow-up wound check is booked in two weeks at the surgical outpatient clinic. "
        "She should go to A&E immediately if she develops fever above 38°C, severe abdominal pain, jaundice, or is unable to keep fluids down."
    ),
    care_tasks=[
        ApproveTask(
            instruction="Take paracetamol 1000mg every 6 hours as needed for pain (maximum 4 doses per day). Always take with food or water.",
            timing="Every 6 hours as needed",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="Start with clear fluids today (water, broth). Move to soft foods tomorrow. Avoid fatty, fried, or spicy food for 2 weeks.",
            timing="Starting today, 2-week restriction",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="If paracetamol is insufficient, take ibuprofen 400mg up to 3 times per day with meals (only if no stomach problems).",
            timing="As needed after paracetamol",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="Keep wound dressings completely dry for 48 hours. After that, shower normally and pat wounds dry gently.",
            timing="First 48 hours strict, then daily",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="Watch wounds for redness, swelling, discharge, or unusual smell — contact the clinic if any of these develop.",
            timing="Daily for 2 weeks",
            responsible_party="caregiver",
        ),
        ApproveTask(
            instruction="Do not drive until 48 hours after last strong pain medication and able to perform an emergency stop comfortably.",
            timing="Within the first week",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="Attend follow-up wound check at the surgical outpatient clinic.",
            timing="In 2 weeks",
            responsible_party="patient",
        ),
        ApproveTask(
            instruction="Go to A&E immediately if: fever above 38°C, severe abdominal pain not controlled by medication, yellowing of skin or eyes, or unable to keep fluids down.",
            timing="If any symptom develops",
            responsible_party="caregiver",
        ),
    ],
    approved_by="Dr. Sarah Chen (Consultant Surgeon)",
)


@router.post("/demo/seed")
def seed_demo(store: Store) -> CaseView:
    """Create or reset the built-in demo patient case with a fully approved care plan. No AI call needed."""
    store.create("demo-patient", reset=True)
    _apply_transcript(store, "demo-patient", _DEMO_SEGMENTS, _DEMO_ROLES, replace=True)  # type: ignore[arg-type]
    with store.update("demo-patient") as case:
        case.patient_name = "Emily Carter"
    return approve("demo-patient", _DEMO_APPROVE, store)
