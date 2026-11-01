"""
Seed the demo case with an intentionally ambiguous fictional discharge scenario.

Creates:
  fixtures/ambiguous_discharge.pdf  — discharge document with vague and
                                       conflicting instructions
  data/cases/demo-patient.json      — case pre-approved and ready for
                                       immediate caregiver testing

Run:  uv run python scripts/seed_test_case.py
Reset the live app after running: just reload the browser (Load demo case
button is not needed — the JSON is already in place).

DESIGNED AMBIGUITIES (see test guide printed at end):
  1. NSAID not named — doctor said "the blue ones"
  2. Aspirin/NSAID interaction explicitly noted as not reviewed
  3. Conflicting mobility guidance (bed rest vs. walk to prevent DVT)
  4. Follow-up date given as a range, no specific appointment
  5. Physiotherapy start has no timeline
  6. Alcohol and stairs not addressed in document
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "fixtures"
DATA_DIR = ROOT / "data" / "cases"

SESSION_ID = "seed-session-ambiguous-001"


# ─── Utilities ────────────────────────────────────────────────────────────────

def utc(ts: str = "2026-10-24T09:00:00+00:00") -> str:
    return ts


# ─── Transcript ───────────────────────────────────────────────────────────────
#
# speakerId 1 = clinician (Dr. Nkosi, fictional)
# speakerId 0 = patient   (Robert Ellis, fictional)
#
RAW_SEGMENTS = [
    (0, 1,   2_000, "Good morning Mr Ellis, how are you feeling after the procedure?"),
    (1, 0,   8_000, "Better, thank you. The hip still aches quite a bit though."),
    (2, 1,  14_000, "That is expected after a total hip replacement. We will manage the pain with the anti-inflammatories."),
    (3, 0,  21_000, "Which ones exactly? The paperwork was not very clear on that."),
    (4, 1,  27_000, "The blue ones you were given on discharge. Take them as needed when the pain is bad."),
    (5, 0,  35_000, "And how many can I take in a day?"),
    (6, 1,  40_000, "Just follow the packet instructions — it should say on the box."),
    (7, 0,  46_000, "I also take a low-dose aspirin every morning for my heart. Is that still okay?"),
    (8, 1,  53_000, "Hmm. We should check that. I will leave a note for the team."),
    (9, 0,  59_000, "Can I shower? The nurse said to keep the wound dry."),
    (10, 1, 65_000, "Yes, avoid getting the wound wet for now. Cover the area and you can shower otherwise."),
    (11, 0, 72_000, "When can I start moving around more?"),
    (12, 1, 78_000, "Do not stay in bed too long — blood clots are a real risk. Short gentle walks. But do not overdo it either."),
    (13, 0, 87_000, "My wife asked about the stairs at home."),
    (14, 1, 93_000, "Stairs are fine eventually. Take it slowly, use the handrail."),
    (15, 0, 100_000, "And when should I come back to see you?"),
    (16, 1, 106_000, "In a few weeks. The ward will send you a letter with the date. Call us if anything worries you before then."),
    (17, 0, 114_000, "What kind of things should worry me?"),
    (18, 1, 120_000, "Redness or discharge at the wound, fever, severe pain not responding to the medication. Those are the main warning signs."),
]

SEG_IDS = [f"seg-seed-{i:03d}" for i in range(len(RAW_SEGMENTS))]

SPEAKER_ROLES = {
    f"{SESSION_ID}:1": "clinician",
    f"{SESSION_ID}:0": "patient",
}


def build_segments() -> list[dict]:
    return [
        {
            "id": SEG_IDS[i],
            "sessionId": SESSION_ID,
            "text": text,
            "speakerId": spk,
            "startMs": start_ms,
            "durationMs": None,
            "recordedAt": "2026-10-24T08:15:00+00:00",
        }
        for i, spk, start_ms, text in RAW_SEGMENTS
    ]


def build_consultation_source(segments: list[dict]) -> dict:
    passages = []
    for seg in segments:
        role = SPEAKER_ROLES.get(f"{seg['sessionId']}:{seg['speakerId']}", "unknown")
        label = role if role != "unknown" else f"unconfirmed speaker {seg['speakerId']}"
        offset = f" at {seg['startMs']}ms"
        passages.append({"id": seg["id"], "page": 0, "text": f"[{label}{offset}] {seg['text']}"})
    return {
        "id": "consultation_001",
        "filename": "Consultation transcript",
        "uploadedAt": "2026-10-24T08:22:00+00:00",
        "passages": passages,
        "kind": "consultation",
    }


# ─── Discharge document passages ──────────────────────────────────────────────
#
# Intentional ambiguities are marked with *** in comments.

DISCHARGE_PASSAGES = [
    # Page 1
    ("page_1_p1", 1,
     "Patient: Robert Ellis (fictional). DOB: 14 March 1957. MRN: FICTIONAL-001. "
     "Procedure: Left total hip arthroplasty. Surgeon: Dr. A. Nkosi (fictional)."),

    ("page_1_p2", 1,
     "Diagnosis: Primary osteoarthritis of the left hip, end-stage, requiring surgical replacement."),

    # Page 2 — Medications *** NSAID unnamed; aspirin interaction unresolved
    ("page_2_p1", 2,
     "Medications: Continue prescribed NSAID (non-steroidal anti-inflammatory) for pain management "
     "as required. Dosage and frequency per product labelling. "
     "NOTE: patient reports concurrent daily low-dose aspirin for a cardiac condition. "
     "Potential interaction with prescribed NSAID was NOT reviewed at time of discharge."),

    ("page_2_p2", 2,
     "Do not exceed the stated daily maximum NSAID dose. "
     "If pain is inadequately controlled, contact the surgical team rather than increasing dose."),

    # Page 3 — Mobility *** Conflicting: bed rest vs. must walk (DVT); no PT start date
    ("page_3_p1", 3,
     "Mobility — Rest: Bed rest is advised during the initial recovery period to protect the surgical site."),

    ("page_3_p2", 3,
     "Mobility — DVT Prevention: Patients must not remain immobile for extended periods. "
     "Deep vein thrombosis is a significant post-operative risk. Short, gentle walks are strongly encouraged."),

    ("page_3_p3", 3,
     "Physical therapy: A physiotherapy referral has been submitted. "
     "Begin gentle range-of-motion exercises when comfortable. Weight-bearing as tolerated. "
     "No specific start date is defined — patient should begin when they feel ready."),

    # Page 4 — Wound care *** No guidance after 48 h beyond 'daily changes'
    ("page_4_p1", 4,
     "Wound care: Keep the wound site completely dry for 48 hours post-discharge. "
     "Do not shower water directly over the wound."),

    ("page_4_p2", 4,
     "After 48 hours: daily dressing changes are recommended until the wound is fully healed. "
     "Dressing materials have been provided in the discharge pack. "
     "No further wound-care technique is specified in this document."),

    ("page_4_p3", 4,
     "Monitor the wound for redness, increasing swelling, warmth, or any discharge. "
     "Return to the emergency department or contact the surgical team immediately if concerned."),

    # Page 5 — Follow-up *** Date range only, no confirmed appointment
    ("page_5_p1", 5,
     "Follow-up appointment: Attend a follow-up clinic in approximately 4 to 6 weeks post-discharge. "
     "A written appointment confirmation will be sent by post. "
     "No specific date or time was confirmed at the point of discharge."),

    ("page_5_p2", 5,
     "Return IMMEDIATELY to the emergency department if experiencing: "
     "high fever (above 38.5 °C), severe or worsening pain not responding to medication, "
     "sudden significant swelling of the operated limb, signs of wound infection, "
     "or calf pain and swelling (possible DVT)."),
]


def build_discharge_source() -> dict:
    return {
        "id": "discharge_001",
        "filename": "ambiguous_discharge.pdf",
        "uploadedAt": "2026-10-24T08:25:00+00:00",
        "passages": [{"id": pid, "page": pg, "text": txt} for pid, pg, txt in DISCHARGE_PASSAGES],
        "kind": "document",
    }


# ─── Care tasks ───────────────────────────────────────────────────────────────

CARE_TASKS = [
    {
        "id": "task_001",
        "instruction": "Administer prescribed NSAID for pain relief as needed, following product labelling for dosage and frequency — specific drug name not recorded in documentation",
        "timing": "As needed; do not exceed stated daily maximum",
        "responsibleParty": "caregiver",
        "sourceRefs": [
            {"sourceId": "discharge_001", "passageId": "page_2_p1"},
            {"sourceId": "discharge_001", "passageId": "page_2_p2"},
            {"sourceId": "consultation_001", "passageId": SEG_IDS[4]},
            {"sourceId": "consultation_001", "passageId": SEG_IDS[6]},
        ],
    },
    {
        "id": "task_002",
        "instruction": "Perform daily wound dressing changes until the wound is fully healed",
        "timing": "Daily, beginning 48 hours after discharge",
        "responsibleParty": "caregiver",
        "sourceRefs": [
            {"sourceId": "discharge_001", "passageId": "page_4_p1"},
            {"sourceId": "discharge_001", "passageId": "page_4_p2"},
        ],
    },
    {
        "id": "task_003",
        "instruction": "Encourage short gentle walks to prevent DVT; balance rest with mobility — discharge document contains conflicting guidance on bed rest vs. walking",
        "timing": "Begin when comfortable; no specific frequency defined",
        "responsibleParty": "caregiver",
        "sourceRefs": [
            {"sourceId": "discharge_001", "passageId": "page_3_p1"},
            {"sourceId": "discharge_001", "passageId": "page_3_p2"},
            {"sourceId": "consultation_001", "passageId": SEG_IDS[12]},
        ],
    },
    {
        "id": "task_004",
        "instruction": "Schedule and attend follow-up clinic appointment",
        "timing": "Approximately 4 to 6 weeks post-discharge; written confirmation expected by post — no specific date given",
        "responsibleParty": "caregiver",
        "sourceRefs": [
            {"sourceId": "discharge_001", "passageId": "page_5_p1"},
            {"sourceId": "consultation_001", "passageId": SEG_IDS[16]},
        ],
    },
    {
        "id": "task_005",
        "instruction": "Monitor wound site daily and contact surgical team if redness, swelling, discharge or fever develops",
        "timing": "Daily",
        "responsibleParty": "caregiver",
        "sourceRefs": [
            {"sourceId": "discharge_001", "passageId": "page_4_p3"},
            {"sourceId": "discharge_001", "passageId": "page_5_p2"},
            {"sourceId": "consultation_001", "passageId": SEG_IDS[18]},
        ],
    },
]

APPROVED_SUMMARY = """\
Robert Ellis (fictional) was discharged following a left total hip arthroplasty performed by Dr. A. Nkosi (fictional).

APPROVED CARE INSTRUCTIONS:
Pain is to be managed with the prescribed NSAID as needed, following the product labelling. Daily wound dressing changes should begin 48 hours after discharge and continue until the wound is healed. Robert should take short gentle walks to prevent DVT while avoiding overexertion. A follow-up appointment has been requested for 4 to 6 weeks post-discharge and will be confirmed by post. The wound should be monitored daily for signs of infection.

FLAGGED AMBIGUITIES — clinical review recommended before caregiver questions are answered:
1. The NSAID prescribed is not named in either the transcript or the discharge document. The doctor referred to "the blue ones" without specifying drug, dose, or maximum daily frequency beyond "follow the packet".
2. The patient's daily low-dose aspirin was acknowledged ("we should check that") but the potential NSAID interaction is explicitly noted as NOT reviewed at discharge. No resolution is documented.
3. The discharge document advises bed rest (page 3, paragraph 1) and simultaneously warns against immobility due to DVT risk (page 3, paragraph 2). Priority and reconciliation of these instructions is not stated.
4. The follow-up appointment is specified as "approximately 4 to 6 weeks" with no confirmed date. The caregiver should expect a letter.
5. No start date or minimum frequency is given for physiotherapy. The instruction is to begin "when ready".\
"""


def build_case(segments: list[dict], consult_src: dict, discharge_src: dict) -> dict:
    sources = [consult_src, discharge_src]
    version = {
        "version": 1,
        "summary": APPROVED_SUMMARY,
        "careTasks": CARE_TASKS,
        "sourceIds": ["consultation_001", "discharge_001"],
        "approvedBy": "Dr. A. Nkosi (fictional — demo only)",
        "approvedAt": "2026-10-24T09:00:00+00:00",
        "inputRevision": 2,
        "sourcesSnapshot": sources,
    }
    return {
        "caseId": "demo-patient",
        "workflowState": "approved",
        "sources": sources,
        "draftSummary": None,
        "summaryVersions": [version],
        "approvedSummaryVersion": 1,
        "careTasks": CARE_TASKS,
        "messages": [],
        "pendingUpdates": [],
        "progressEvents": [],
        "unresolvedQuestions": [],
        "transcriptSegments": segments,
        "speakerRoles": SPEAKER_ROLES,
        "inputRevision": 2,
    }


# ─── PDF generation ───────────────────────────────────────────────────────────

def make_pdf() -> None:
    try:
        from fpdf import FPDF  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        print("fpdf2 not installed — skipping PDF. Run: uv sync --group dev")
        return

    class Doc(FPDF):
        def header(self):
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 6, "FICTIONAL TRAINING DATA ONLY - NOT FOR CLINICAL USE", align="C")
            self.ln(4)
            self.set_text_color(0, 0, 0)

    pdf = Doc()
    pdf.set_auto_page_break(True, 18)
    pdf.set_margins(22, 22, 22)

    def h1(txt: str) -> None:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(18, 50, 79)
        pdf.cell(0, 10, txt, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def h2(txt: str) -> None:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, txt, new_x="LMARGIN", new_y="NEXT")

    def body(txt: str) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, txt)
        pdf.ln(2)

    def warning(txt: str) -> None:
        pdf.set_font("Helvetica", "BI", 10)
        pdf.set_text_color(163, 38, 42)
        pdf.multi_cell(0, 6, txt)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(2)

    # Page 1 — cover
    pdf.add_page()
    h1("DISCHARGE SUMMARY")
    body("This document is entirely fictional and generated for software testing. "
         "No real patient data is used.")
    pdf.ln(3)
    h2("Patient")
    body("Robert Ellis (fictional)  |  DOB: 14 March 1957  |  MRN: FICTIONAL-001")
    h2("Procedure")
    body("Left total hip arthroplasty")
    h2("Surgeon")
    body("Dr. A. Nkosi (fictional), Orthopaedic Surgery")
    h2("Diagnosis")
    body("Primary osteoarthritis of the left hip, end-stage, requiring surgical joint replacement.")

    # Page 2 — Medications
    pdf.add_page()
    h1("Medications")
    h2("Pain management")
    body("Continue prescribed NSAID (non-steroidal anti-inflammatory) for pain management as "
         "required. Dosage and frequency as per product labelling. Do not exceed the stated "
         "daily maximum dose.")
    warning("NOTE: Patient reports concurrent daily low-dose aspirin for a cardiac condition. "
            "Potential interaction with prescribed NSAID was NOT reviewed at time of discharge.")
    h2("If pain is uncontrolled")
    body("Contact the surgical team. Do not increase dose without medical advice.")

    # Page 3 — Mobility
    pdf.add_page()
    h1("Mobility and Activity")
    h2("Rest")
    body("Bed rest is advised during the initial recovery period to protect the surgical site.")
    h2("DVT Prevention - Important")
    body("Patients must NOT remain immobile for extended periods. Deep vein thrombosis is a "
         "significant post-operative risk. Short, gentle walks are strongly encouraged.")
    h2("Physical therapy")
    body("A physiotherapy referral has been submitted. Begin gentle range-of-motion exercises "
         "when comfortable. Weight-bearing as tolerated. No specific start date is defined - "
         "begin when the patient feels ready.")
    h2("Stairs")
    body("May be used with caution once the patient has adequate strength. Always use the handrail.")

    # Page 4 — Wound care
    pdf.add_page()
    h1("Wound Care")
    h2("First 48 hours")
    body("Keep the wound site completely dry for 48 hours post-discharge. "
         "Do not shower water directly over the wound.")
    h2("After 48 hours")
    body("Daily dressing changes are recommended until the wound is fully healed. "
         "Dressing materials have been provided in the discharge pack. "
         "No further wound-care technique is specified in this document.")
    h2("Monitor for")
    body("Redness, increasing swelling, warmth, or discharge from the wound site. "
         "Return to the emergency department or contact the surgical team immediately if concerned.")

    # Page 5 — Follow-up
    pdf.add_page()
    h1("Follow-up and Emergency Guidance")
    h2("Follow-up appointment")
    warning("Attend follow-up clinic in approximately 4 to 6 weeks post-discharge. "
            "A written appointment confirmation will be sent by post. "
            "No specific date or time was confirmed at discharge.")
    h2("Return immediately to the emergency department if:")
    body("- High fever above 38.5 C\n"
         "- Severe or worsening pain not responding to prescribed medication\n"
         "- Sudden significant swelling of the operated limb\n"
         "- Signs of wound infection (redness, heat, discharge, odour)\n"
         "- Calf pain or swelling (possible DVT)")

    FIXTURE_DIR.mkdir(exist_ok=True)
    out = FIXTURE_DIR / "ambiguous_discharge.pdf"
    pdf.output(str(out))
    print(f"PDF  -> {out}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    make_pdf()

    segments = build_segments()
    consult_src = build_consultation_source(segments)
    discharge_src = build_discharge_source()
    case = build_case(segments, consult_src, discharge_src)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "demo-patient.json"
    out.write_text(json.dumps(case, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON -> {out}")

    print()
    print("=" * 62)
    print("  TEST SCENARIO GUIDE")
    print("=" * 62)
    print("Case is pre-approved. Open Caregiver view and ask these:")
    print()
    print("1. UNNAMED MEDICATION")
    print("   Ask: 'What medication should Robert take for pain, and")
    print("         how often?'")
    print("   Expect: Agent cites page_2_p1 + seg-seed-004/006, flags")
    print("           that specific drug is not named. Cannot invent it.")
    print()
    print("2. ASPIRIN DRUG INTERACTION (unresolved)")
    print("   Ask: 'He takes his daily aspirin - is that safe with the")
    print("         new medicine?'")
    print("   Expect: Agent quotes 'interaction NOT reviewed at discharge'")
    print("           and marks question as unresolved for the care team.")
    print()
    print("3. CONFLICTING MOBILITY GUIDANCE")
    print("   Ask: 'Should he stay in bed or go for walks?'")
    print("   Expect: Agent surfaces both page_3_p1 (bed rest) and")
    print("           page_3_p2 (DVT walks), explicitly names the conflict,")
    print("           does not pick a side.")
    print()
    print("4. SUPPORTED PROGRESS UPDATE")
    print("   Say:  'I changed his wound dressing this morning.'")
    print("   Expect: Agent proposes update for task_002 (Daily wound")
    print("           dressing). Confirm to save the event.")
    print()
    print("5. OUT-OF-SCOPE QUESTION")
    print("   Ask: 'Can he drink alcohol?'")
    print("   Expect: No evidence in any source. Agent records as")
    print("           unresolved question for care team. Does NOT invent.")
    print()
    print("6. VAGUE FOLLOW-UP DATE")
    print("   Ask: 'When exactly is the follow-up appointment?'")
    print("   Expect: Agent quotes '4 to 6 weeks, confirmation by post'")
    print("           and notes no specific date was confirmed.")
    print()
    print("7. STAIR SAFETY (partial evidence)")
    print("   Ask: 'Can Robert use the stairs at home?'")
    print("   Expect: Agent cites page_3_p3 + seg-seed-014 - 'fine")
    print("           eventually, slowly, use handrail'. Qualifies timing.")
    print("=" * 62)


if __name__ == "__main__":
    main()
