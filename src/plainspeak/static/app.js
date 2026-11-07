"use strict";

let CASE_ID = localStorage.getItem('ps-active-case') || 'default';
let caseView = null;   // last CaseView from the backend
let draftEdit = null;  // doctor's working copy of the draft

const CLINICIAN_KEY = 'ps-clinician-name';

// ── helpers ───────────────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function showError(message) {
  const box = $("#error");
  box.textContent = message;
  box.hidden = !message;
  if (message) window.toast?.(message, 'error');
}

async function api(path, options = {}) {
  const opts = { ...options };
  if (opts.json !== undefined) {
    opts.body = JSON.stringify(opts.json);
    opts.headers = { "Content-Type": "application/json" };
    delete opts.json;
  }
  window.tpbStart?.();
  try {
    const res = await fetch(path, opts);
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      window.tpbDone?.(false);
      const detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      throw new Error(detail || `Request failed (${res.status})`);
    }
    window.tpbDone?.(true);
    return body;
  } catch (err) {
    window.tpbDone?.(false);
    throw err;
  }
}

async function run(button, fn) {
  showError("");
  if (button) { button.disabled = true; button.classList.add('loading'); }
  try {
    await fn();
  } catch (err) {
    showError(err.message);
  } finally {
    if (button) { button.disabled = false; button.classList.remove('loading'); }
  }
}

function passageText(ref) {
  const source = caseView?.case.sources.find((s) => s.id === ref.sourceId);
  return source?.passages.find((p) => p.id === ref.passageId)?.text ?? "";
}

function refChips(refs = [], eventRefs = []) {
  const sources = refs.map((r) =>
    `<span class="chip" title="${esc(passageText(r))}">${esc(r.sourceId)} · ${esc(r.passageId)}</span>`);
  const events = eventRefs.map((id) => {
    const ev = caseView?.case.progressEvents.find((e) => e.id === id);
    const title = ev ? `${ev.actor} at ${ev.timestamp}: ${ev.note}` : id;
    return `<span class="chip event" title="${esc(title)}">event · ${esc(id)}</span>`;
  });
  return sources.concat(events).join("");
}

function taskInstruction(taskId) {
  return caseView?.case.careTasks.find((t) => t.id === taskId)?.instruction ?? taskId;
}

// ── clinician identity ────────────────────────────────────────────────────────

function getClinician() {
  return localStorage.getItem(CLINICIAN_KEY) || '';
}

function setClinician(name) {
  const trimmed = (name || '').trim();
  if (trimmed) localStorage.setItem(CLINICIAN_KEY, trimmed);
  else localStorage.removeItem(CLINICIAN_KEY);
  updateClinicianUI();
}

function updateClinicianUI() {
  const name = getClinician();
  const el = document.getElementById('clinician-name-display');
  if (el) el.textContent = name || 'Set clinician name ›';
}

// ── case UI ───────────────────────────────────────────────────────────────────

function updateCaseUI() {
  const el1 = document.getElementById('sidebar-case-id');
  const el2 = document.getElementById('journey-case-id');
  const el3 = document.getElementById('ccb-case-id');
  if (el1) el1.textContent = CASE_ID;
  if (el2) el2.textContent = CASE_ID;
  if (el3) el3.textContent = CASE_ID;
}

// ── care journey ──────────────────────────────────────────────────────────────

const JOURNEY = [
  { title: "Consultation", detail: "Capture what was said" },
  { title: "Clinician review", detail: "Approve the instructions" },
  { title: "At-home support", detail: "Ask questions, track tasks" },
];

function approvedVersion() {
  const c = caseView.case;
  return c.summaryVersions.find((v) => v.version === c.approvedSummaryVersion);
}

/** True once an approval covers the current inputs, which is what unlocks the at-home view. */
function postCareOpen() {
  const c = caseView.case;
  const approved = approvedVersion();
  return !!approved && c.workflowState !== "awaiting_review" && approved.inputRevision === c.inputRevision;
}

function journeyStage() {
  if (postCareOpen()) return 3;
  return caseView.case.sources.some((s) => s.kind === "document" || s.kind === "consultation") ? 2 : 1;
}

function renderJourney() {
  const stage = journeyStage();
  $("#journey-steps").innerHTML = JOURNEY.map((step, i) => {
    const n = i + 1;
    const state = n < stage ? "done" : n === stage ? "active" : "";
    return `<div class="journey-step">
      <span class="journey-marker ${state}">${n < stage ? "✓" : n}</span>
      <div><strong>${esc(step.title)}</strong><small>${esc(step.detail)}</small></div>
      ${n === stage ? `<span class="journey-status">CURRENT</span>` : ""}
    </div>`;
  }).join("");
  document.querySelectorAll(".workflow-step").forEach((el, i) => {
    el.classList.toggle("active", i === stage - 1);
  });
}

// ── patient identity ──────────────────────────────────────────────────────────

/** Fills every [data-patient] slot from the name found in the discharge document. */
function renderPatient() {
  const name = caseView.case.patientName;
  const first = name?.split(" ")[0];
  const text = {
    full: name ?? "Patient not yet identified",
    first: first ?? "the patient",
    possessive: first ? `${first}'s` : "Patient's",
    initial: (first ?? "P")[0].toUpperCase(),
  };
  document.querySelectorAll("[data-patient]").forEach((el) => {
    el.textContent = text[el.dataset.patient];
  });
}

// ── rendering ─────────────────────────────────────────────────────────────────

function setCase(view) {
  caseView = view;
  const c = view.case;
  if (c.draftSummary) {
    if (!draftEdit || draftEdit.createdAt !== c.draftSummary.createdAt) {
      draftEdit = structuredClone(c.draftSummary);
    }
  } else {
    draftEdit = null;
  }
  renderPatient();
  renderJourney();
  renderDoctor();
  renderCaregiver();
  renderReport();
  if (typeof renderConsultation === "function") renderConsultation();
  // Broadcast to UI panels (case context bar, intel rail)
  document.dispatchEvent(new CustomEvent('ps:case', { detail: view }));
}

function renderDoctor() {
  const c = caseView.case;
  const draft = $("#draft");
  if (!draftEdit) {
    draft.innerHTML = `<p class="muted">${c.sources.length ? "Generate a draft to review." : "Upload a document first."}</p>`;
  } else {
    draft.innerHTML = `
      <h3>Summary</h3>
      <textarea id="draft-summary">${esc(draftEdit.summary)}</textarea>
      <div class="char-counter" id="draft-char-count"></div>
      <h3>Care tasks</h3>
      ${draftEdit.careTasks.map((t, i) => `
        <div class="task-edit" data-index="${i}">
          <input type="text" data-field="instruction" value="${esc(t.instruction)}" placeholder="Instruction">
          <input type="text" data-field="timing" value="${esc(t.timing ?? "")}" placeholder="Timing (optional)">
          <select data-field="responsibleParty">
            ${["patient", "caregiver", "care_team", "unspecified"].map((p) =>
              `<option ${p === t.responsibleParty ? "selected" : ""}>${p}</option>`).join("")}
          </select>
          <button class="danger" data-remove="${i}">Remove</button>
        </div>`).join("")}
      <button id="btn-add-task" class="secondary">Add task</button>
      <h3>Approve</h3>
      <div class="row">
        <input type="text" id="approved-by" value="${esc(getClinician())}" placeholder="Your name (clinician)" style="max-width:260px">
        <button id="btn-approve">Approve this version</button>
      </div>`;
    draft.querySelectorAll(".task-edit").forEach((row) => {
      const task = draftEdit.careTasks[Number(row.dataset.index)];
      row.querySelectorAll("[data-field]").forEach((el) => {
        el.addEventListener("input", () => {
          const v = el.value;
          task[el.dataset.field] = el.dataset.field === "timing" ? (v.trim() || null) : v;
        });
      });
    });
    const draftTA = $("#draft-summary");
    const charCount = document.getElementById("draft-char-count");
    function updateCharCount() {
      const len = draftTA.value.length;
      const words = draftTA.value.trim() ? draftTA.value.trim().split(/\s+/).length : 0;
      if (charCount) charCount.textContent = `${words} words · ${len} chars`;
      draftTA.style.height = "auto";
      draftTA.style.height = draftTA.scrollHeight + "px";
    }
    updateCharCount();
    draftTA.addEventListener("input", (e) => { draftEdit.summary = e.target.value; updateCharCount(); });
    draft.querySelectorAll("[data-remove]").forEach((b) => b.addEventListener("click", () => {
      draftEdit.careTasks.splice(Number(b.dataset.remove), 1);
      renderDoctor();
    }));
    $("#btn-add-task").addEventListener("click", () => {
      draftEdit.careTasks.push({ id: null, instruction: "", timing: null, responsibleParty: "unspecified", sourceRefs: [] });
      renderDoctor();
    });
    $("#btn-approve").addEventListener("click", (e) => run(e.target, approveDraft));
  }

  const approved = approvedVersion();
  $("#approved").innerHTML = approved ? `
    <div class="approved-actions">
      <button class="button-secondary btn-sm" id="btn-export-pdf">↓ Export PDF</button>
      <button class="button-secondary btn-sm" id="btn-read-aloud">▶ Read aloud</button>
      <button class="button-secondary btn-sm" id="btn-copy-plan">⧉ Copy</button>
    </div>
    <p class="muted">Version ${approved.version} approved by ${esc(approved.approvedBy)} at ${esc(approved.approvedAt)}
      ${c.summaryVersions.length > 1 ? ` · ${c.summaryVersions.length} versions preserved` : ""}</p>
    <p>${esc(approved.summary)}</p>
    <ul class="plain">${approved.careTasks.map((t) => `<li>${esc(t.instruction)}</li>`).join("")}</ul>
  ` : `<p class="muted">Nothing approved yet.</p>`;

  if (approved) {
    document.getElementById('btn-export-pdf')?.addEventListener('click', () => {
      window.exportCarePlanPDF?.({
        patientName: c.patientName,
        summary: approved.summary,
        careTasks: approved.careTasks,
        approvedBy: approved.approvedBy,
        approvedAt: approved.approvedAt,
        version: approved.version,
      });
    });
    const readBtn = document.getElementById('btn-read-aloud');
    readBtn?.addEventListener('click', () => {
      if (window.isReading?.()) {
        window.stopReading?.();
        readBtn.innerHTML = '▶ Read aloud';
        readBtn.classList.remove('btn-reading');
        window.setAIState?.('idle');
      } else {
        const txt = `${approved.summary}. Care tasks: ${approved.careTasks.map((t, i) => `Task ${i + 1}: ${t.instruction}`).join('. ')}`;
        readBtn.innerHTML = '■ Stop reading';
        readBtn.classList.add('btn-reading');
        window.setAIState?.('speaking');
        window.readAloud?.(txt, () => {
          readBtn.innerHTML = '▶ Read aloud';
          readBtn.classList.remove('btn-reading');
          window.setAIState?.('idle');
        });
      }
    });
    const copyBtn = document.getElementById('btn-copy-plan');
    copyBtn?.addEventListener('click', () => {
      const txt = `CARE PLAN — ${c.patientName || 'Patient'} — Version ${approved.version}\nApproved by ${approved.approvedBy} on ${approved.approvedAt}\n\nSUMMARY\n${approved.summary}\n\nCARE TASKS\n${approved.careTasks.map((t, i) => `${i + 1}. ${t.instruction}${t.timing ? ` (${t.timing})` : ''} [${t.responsibleParty}]`).join('\n')}`;
      navigator.clipboard.writeText(txt).then(() => {
        copyBtn.innerHTML = '✓ Copied';
        setTimeout(() => { copyBtn.innerHTML = '⧉ Copy'; }, 2000);
        window.toast?.('Care plan copied to clipboard', 'success', 2500);
      }).catch(() => window.toast?.('Copy failed — please copy manually', 'error'));
    });
  }
}

function statusBadge(status) {
  return `<span class="status ${esc(status)}">${esc(status.replace("_", " "))}</span>`;
}

function renderChecklist() {
  const rows = caseView.checklist.map((t) => `
    <tr>
      <td>${esc(t.instruction)}</td>
      <td>${esc(t.timing ?? "")}</td>
      <td>${esc(t.responsibleParty)}</td>
      <td>${statusBadge(t.status)}${t.lastEvent ? `<div class="muted">${esc(t.lastEvent.actor)}<br>${esc(t.lastEvent.timestamp)}</div>` : ""}</td>
    </tr>`).join("");
  return `<table><tr><th>Task</th><th>Timing</th><th>Who</th><th>Status</th></tr>${rows}</table>`;
}

function generateSuggestedQuestions(careTasks, summary) {
  const full = (careTasks.map(t => t.instruction).join(' ') + ' ' + (summary || '')).toLowerCase();
  const qs = ['What are the most important things I need to do today?'];
  if (/medication|medicine|drug|tablet|pill|dose|mg|prescribed/.test(full))
    qs.push('What medications do I need to take, and when?');
  if (/diet|food|eat|drink|nutrition|fluid|water|avoid/.test(full))
    qs.push('Are there any food or drink restrictions?');
  if (/exercise|walk|activity|rest|physical|movement/.test(full))
    qs.push('What physical activity is safe for me right now?');
  if (/wound|dressing|bandage|scar|incision|stitch/.test(full))
    qs.push('How should I care for the wound or dressing?');
  if (/appointment|follow.?up|visit|return|clinic|next/.test(full))
    qs.push('When is my next follow-up appointment?');
  if (/pain|discomfort|ache|hurt/.test(full))
    qs.push('What should I do if the pain gets worse?');
  if (/emergency|warning|sign|symptom|urgent/.test(full))
    qs.push('What warning signs should I watch out for?');
  return [...new Set(qs)].slice(0, 4);
}

function renderCaregiver() {
  const c = caseView.case;
  const open = postCareOpen();
  $("#cg-locked").hidden = open;
  $("#cg-body").hidden = !open;
  if (!open) return;

  // Care plan summary strip
  const approved = approvedVersion();
  const summaryEl = $("#cg-care-summary");
  if (summaryEl && approved) {
    const tasks = approved.careTasks.slice(0, 5);
    summaryEl.innerHTML = `
      <div class="cg-summary-inner">
        <div class="cg-summary-left">
          <span class="cg-summary-icon">✦</span>
          <div>
            <div class="cg-summary-label">APPROVED CARE PLAN · v${approved.version}</div>
            <div class="cg-summary-patient">${esc(c.patientName || 'Patient')} · approved by ${esc(approved.approvedBy)}</div>
          </div>
        </div>
        <div class="cg-summary-tasks">
          ${tasks.map(t => `<span class="cg-task-chip" title="${esc(t.instruction)}">${esc(t.instruction)}</span>`).join('')}
          ${approved.careTasks.length > 5 ? `<span class="cg-task-more">+${approved.careTasks.length - 5} more</span>` : ''}
        </div>
      </div>`;
  }

  // Suggested questions
  const suggestEl = $("#cg-suggested");
  if (suggestEl && approved) {
    const questions = generateSuggestedQuestions(approved.careTasks, approved.summary);
    if (questions.length) {
      suggestEl.innerHTML = `
        <div class="cg-suggest-label">Try asking</div>
        <div class="cg-suggest-chips">
          ${questions.map(q => `<button type="button" class="suggest-chip">${esc(q)}</button>`).join('')}
        </div>`;
      suggestEl.querySelectorAll('.suggest-chip').forEach(btn => {
        btn.addEventListener('click', () => {
          const input = $("#chat-input");
          if (input) { input.value = btn.textContent; input.focus(); }
        });
      });
    }
  }

  // Tab notification badge — show when pending task confirmations exist
  const notifBadge = document.getElementById('notif-caregiver');
  if (notifBadge) {
    const pending = c.pendingUpdates?.filter(u => u.status === 'pending').length ?? 0;
    notifBadge.textContent = pending || '';
    notifBadge.hidden = !pending;
  }

  // Today's care spotlight
  const todayEl = document.getElementById('cg-today');
  if (todayEl && approved) {
    const hour   = new Date().getHours();
    const period = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
    const periodLabel = { morning: '🌅 Morning', afternoon: '☀ Afternoon', evening: '🌙 Evening' }[period];
    const relevant = approved.careTasks.filter(t => {
      if (!t.timing) return false;
      const tim = t.timing.toLowerCase();
      return /daily|every day|each day|once a day|twice a day/.test(tim)
        || (period === 'morning'   && /morning|breakfast|wake|am\b/.test(tim))
        || (period === 'afternoon' && /afternoon|lunch|midday|noon/.test(tim))
        || (period === 'evening'   && /evening|dinner|night|bed|pm\b/.test(tim));
    });
    if (relevant.length) {
      todayEl.hidden = false;
      todayEl.innerHTML = `
        <div class="today-inner">
          <span class="today-label">${periodLabel} · Today's care</span>
          <div class="today-tasks">
            ${relevant.map(t => `
              <div class="today-task">
                <span class="today-check">○</span>
                <span>${esc(t.instruction)}</span>
              </div>`).join('')}
          </div>
        </div>`;
    } else {
      todayEl.hidden = true;
    }
  }

  // Quick-action report buttons
  const qaEl = document.getElementById('cg-quick-actions');
  if (qaEl && approved) {
    const actions = window.generateQuickActions?.(approved.careTasks, approved.summary) ?? [];
    if (actions.length) {
      qaEl.hidden = false;
      qaEl.innerHTML = `
        <div class="qa-label">Quick report</div>
        <div class="qa-chips">
          ${actions.map(a => `<button type="button" class="qa-chip">${esc(a)}</button>`).join('')}
        </div>`;
      qaEl.querySelectorAll('.qa-chip').forEach(btn => {
        btn.addEventListener('click', () => {
          const input = document.getElementById('chat-input');
          if (input) {
            input.value = btn.textContent;
            document.getElementById('chat-form')?.requestSubmit();
          }
        });
      });
    }
  }

  // Progress stats card
  const progressCard = document.getElementById('cg-progress-card');
  if (progressCard && caseView) {
    const totalTasks = caseView.checklist.length;
    const doneTasks  = caseView.checklist.filter(t => t.status === 'done').length;
    const questionsAsked = c.messages.filter(m => m.role === 'caregiver').length;
    const pct = totalTasks ? Math.round(doneTasks / totalTasks * 100) : 0;
    let daysLabel = '—';
    if (approved?.approvedAt) {
      const d = Math.floor((Date.now() - new Date(approved.approvedAt).getTime()) / 86400000);
      daysLabel = d === 0 ? 'Today' : `${d}d`;
    }
    progressCard.hidden = false;
    document.getElementById('pr-pct').textContent   = `${pct}%`;
    document.getElementById('pr-tasks').textContent  = `${doneTasks}/${totalTasks}`;
    document.getElementById('pr-questions').textContent = String(questionsAsked);
    document.getElementById('pr-days').textContent   = daysLabel;
    const ring = document.getElementById('pr-ring');
    if (ring) {
      const circ = 2 * Math.PI * 30;
      ring.style.strokeDasharray  = circ;
      ring.style.strokeDashoffset = circ - (pct / 100) * circ;
    }
  }

  $("#conversation").innerHTML = c.messages.map((m) => {
    if (m.role === "caregiver") return `
      <div class="msg-row msg-row-user">
        <div class="msg caregiver">${esc(m.text)}</div>
        <div class="msg-avatar msg-avatar-user" title="Caregiver">CG</div>
      </div>`;
    const r = m.reply ?? { kind: "answer", sourceRefs: [], eventRefs: [] };
    const grounded = r.sourceRefs?.length > 0
      ? `<span class="grounded-badge">✓ Sourced from care plan</span>` : '';
    let confirm = "";
    if (r.pendingUpdateId) {
      const u = c.pendingUpdates.find((p) => p.id === r.pendingUpdateId);
      if (u) {
        const label = `${taskInstruction(u.taskId)} → ${u.reportedStatus.replace("_", " ")}`;
        confirm = u.status === "pending" ? `
          <div class="confirm-card">
            <div><strong>Confirm update:</strong> ${esc(label)}</div>
            <div class="muted">${esc(u.note)}</div>
            <div class="row" style="margin:8px 0 0">
              <button data-confirm="${esc(u.id)}">Confirm</button>
              <button class="secondary" data-reject="${esc(u.id)}">Not right</button>
            </div>
          </div>` : `<div class="confirm-card muted">Update ${esc(u.status)}: ${esc(label)}</div>`;
      }
    }
    return `
      <div class="msg-row msg-row-ai">
        <div class="msg-avatar msg-avatar-ai" title="PlainSpeak AI">✦</div>
        <div class="msg assistant">
          <div class="kind ${esc(r.kind)}">${esc(r.kind.replace("_", " "))}</div>
          <div class="msg-text">${esc(m.text)}</div>
          ${grounded}
          <div class="msg-footer-row">
            <button type="button" class="msg-listen-btn" data-msg-text="${esc(m.text)}" title="Read aloud">
              <span class="listen-icon">🔊</span><span class="listen-label">Listen</span>
            </button>
            <button type="button" class="msg-copy-btn" data-copy-text="${esc(m.text)}" title="Copy answer">⧉</button>
          </div>
          ${confirm}
        </div>
      </div>`;
  }).join("") || `<p class="empty-state">Your conversation will appear here. Ask about the approved care plan to get started.</p>`;

  $("#conversation").querySelectorAll("[data-confirm]").forEach((b) => b.addEventListener("click", () =>
    run(b, async () => setCase(await api(`/api/cases/${CASE_ID}/updates/${b.dataset.confirm}/confirm`, { method: "POST" })))));
  $("#conversation").querySelectorAll("[data-reject]").forEach((b) => b.addEventListener("click", () =>
    run(b, async () => setCase(await api(`/api/cases/${CASE_ID}/updates/${b.dataset.reject}/reject`, { method: "POST" })))));

  // Listen buttons
  $("#conversation").querySelectorAll(".msg-listen-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const allBtns = document.querySelectorAll(".msg-listen-btn");
      if (btn.classList.contains("listening")) {
        window.stopReading?.();
        btn.classList.remove("listening");
        btn.querySelector(".listen-label").textContent = "Listen";
        window.setAIState?.("idle");
      } else {
        allBtns.forEach(b => { b.classList.remove("listening"); b.querySelector(".listen-label").textContent = "Listen"; });
        btn.classList.add("listening");
        btn.querySelector(".listen-label").textContent = "Stop";
        window.setAIState?.("speaking");
        window.readAloud?.(btn.dataset.msgText, () => {
          btn.classList.remove("listening");
          btn.querySelector(".listen-label").textContent = "Listen";
          window.setAIState?.("idle");
        });
      }
    });
  });

  // Copy buttons on AI messages
  $("#conversation").querySelectorAll(".msg-copy-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(btn.dataset.copyText).then(() => {
        btn.textContent = '✓';
        setTimeout(() => { btn.textContent = '⧉'; }, 1800);
      }).catch(() => {});
    });
  });

  // Conversation search
  const searchInput = document.getElementById('convo-search');
  if (searchInput) {
    searchInput.oninput = () => {
      const q = searchInput.value.toLowerCase().trim();
      document.querySelectorAll('#conversation .msg-row').forEach(row => {
        row.style.display = (!q || row.textContent.toLowerCase().includes(q)) ? '' : 'none';
      });
    };
  }

  // Scroll to latest message
  const convEl = document.getElementById('conversation');
  if (convEl) {
    convEl.scrollTo({ top: convEl.scrollHeight, behavior: 'smooth' });
    const scrollFab = document.getElementById('scroll-to-bottom');
    if (scrollFab) {
      scrollFab.onclick = () => convEl.scrollTo({ top: convEl.scrollHeight, behavior: 'smooth' });
      convEl.addEventListener('scroll', () => {
        const nearBottom = convEl.scrollHeight - convEl.scrollTop - convEl.clientHeight < 100;
        scrollFab.hidden = nearBottom || c.messages.length === 0;
      }, { passive: true });
    }
  }

  $("#checklist").innerHTML = renderChecklist();
}

// ── session history ───────────────────────────────────────────────────────────

const HIST_KEY = 'ps-session-history';
const HIST_MAX = 10;

function saveToHistory() {
  const approved = approvedVersion();
  if (!approved || !caseView) return;
  const entry = {
    id: Date.now().toString(),
    savedAt: new Date().toISOString(),
    patientName: caseView.case.patientName || 'Unknown patient',
    version: approved.version,
    approvedBy: approved.approvedBy,
    approvedAt: approved.approvedAt,
    summary: approved.summary,
    careTasks: approved.careTasks,
  };
  let history = loadHistoryEntries();
  history = history.filter(h => !(h.patientName === entry.patientName && h.version === entry.version));
  history.unshift(entry);
  if (history.length > HIST_MAX) history.length = HIST_MAX;
  try { localStorage.setItem(HIST_KEY, JSON.stringify(history)); } catch (_) {}
  renderHistoryPanel();
}

function loadHistoryEntries() {
  try { return JSON.parse(localStorage.getItem(HIST_KEY) || '[]'); } catch (_) { return []; }
}

function renderHistoryPanel() {
  const panel = document.getElementById('history-list');
  if (!panel) return;
  const entries = loadHistoryEntries();
  const badge = document.getElementById('hist-badge');
  if (badge) {
    badge.textContent = entries.length;
    badge.classList.toggle('visible', entries.length > 0);
  }
  if (!entries.length) {
    panel.innerHTML = '<p class="hist-empty">Approve a care plan to save it here.</p>';
    return;
  }
  panel.innerHTML = entries.map(e => {
    const d = new Date(e.savedAt);
    const ds = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const ts = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    return `<button class="hist-item" data-hist-id="${esc(e.id)}">
      <div class="hist-item-top">
        <span class="hist-patient">${esc(e.patientName)}</span>
        <span class="hist-version">v${esc(String(e.version))}</span>
      </div>
      <div class="hist-item-meta">${esc(ds)} · ${esc(ts)}</div>
    </button>`;
  }).join('');
  panel.querySelectorAll('.hist-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const entry = loadHistoryEntries().find(e => e.id === btn.dataset.histId);
      if (entry) openHistoryModal(entry);
    });
  });
}

function openHistoryModal(entry) {
  const modal   = document.getElementById('history-modal');
  const content = document.getElementById('history-modal-content');
  if (!modal || !content) return;
  content.innerHTML = `
    <div class="hist-modal-header">
      <div>
        <div class="hist-modal-patient">${esc(entry.patientName)}</div>
        <div class="hist-modal-meta">Version ${esc(String(entry.version))} · Approved by ${esc(entry.approvedBy)} · ${esc(entry.approvedAt)}</div>
      </div>
      <div class="hist-modal-actions">
        <button class="button-secondary btn-sm" id="hm-export">↓ Export PDF</button>
        <button class="button-secondary btn-sm" id="hm-read">▶ Read aloud</button>
      </div>
    </div>
    <div class="hist-modal-body">
      <h3>Summary</h3>
      <p>${esc(entry.summary)}</p>
      <h3>Care tasks</h3>
      <ul class="plain">
        ${entry.careTasks.map(t =>
          `<li>${esc(t.instruction)}${t.timing ? ` <span class="muted">· ${esc(t.timing)}</span>` : ''}</li>`
        ).join('')}
      </ul>
    </div>`;
  document.getElementById('hm-export')?.addEventListener('click', () => {
    window.exportCarePlanPDF?.(entry);
  });
  const readBtn = document.getElementById('hm-read');
  readBtn?.addEventListener('click', () => {
    if (window.isReading?.()) {
      window.stopReading?.();
      readBtn.innerHTML = '▶ Read aloud';
      readBtn.classList.remove('btn-reading');
    } else {
      const text = `${entry.summary}. Care tasks: ${entry.careTasks.map((t, i) => `Task ${i + 1}: ${t.instruction}`).join('. ')}`;
      readBtn.innerHTML = '■ Stop';
      readBtn.classList.add('btn-reading');
      window.readAloud?.(text, () => {
        readBtn.innerHTML = '▶ Read aloud';
        readBtn.classList.remove('btn-reading');
      });
    }
  });
  modal.classList.add('open');
}

function renderReport() {
  const c = caseView.case;
  const approved = approvedVersion();
  if (!approved) {
    $("#report").innerHTML = `<h2>Central report</h2><p class="muted">No approved instructions yet.</p>`;
    return;
  }
  const openTasks = caseView.checklist.filter((t) => t.status !== "done");
  const openQs = c.unresolvedQuestions.filter((q) => q.status === "open");
  $("#report").innerHTML = `
    <h2>Central report${caseView.case.patientName ? ` · ${esc(caseView.case.patientName)}` : ""}</h2>
    <p class="muted">Derived from saved approved instructions and attributed events. Self-reported progress does not indicate clinical outcome.</p>
    <h3>Approved instructions (v${approved.version}, ${esc(approved.approvedBy)}, ${esc(approved.approvedAt)})</h3>
    <p>${esc(approved.summary)}</p>
    ${renderChecklist()}
    <h3>Self-reported updates</h3>
    ${c.progressEvents.length ? `<table><tr><th>When</th><th>Who</th><th>Plan</th><th>Task</th><th>Status</th><th>Note</th></tr>
      ${c.progressEvents.map((e) => {
        const version = c.summaryVersions.find((v) => v.version === e.approvedSummaryVersion);
        const instruction = version?.careTasks.find((t) => t.id === e.taskId)?.instruction ?? e.taskId;
        return `<tr><td>${esc(e.timestamp)}</td><td>${esc(e.actor)}</td><td>v${esc(e.approvedSummaryVersion)}</td><td>${esc(instruction)}</td><td>${statusBadge(e.status)}</td><td>${esc(e.note)}</td></tr>`;
      }).join("")}
      </table>` : `<p class="muted">None yet.</p>`}
    <h3>Open tasks</h3>
    ${openTasks.length ? `<ul class="plain">${openTasks.map((t) => `<li>${esc(t.instruction)}</li>`).join("")}</ul>` : `<p class="muted">None.</p>`}
    <h3>Unresolved questions for the care team</h3>
    ${openQs.length ? `<ul class="plain">${openQs.map((q) => `<li>${esc(q.question)} <span class="muted">(${esc(q.createdAt)})</span></li>`).join("")}</ul>` : `<p class="muted">None.</p>`}
  `;
}

// ── case management ───────────────────────────────────────────────────────────

async function loadCase(reset = false, caseId = CASE_ID) {
  const view = await api('/api/cases', { method: 'POST', json: { caseId, reset } });
  CASE_ID = view.case.caseId;
  localStorage.setItem('ps-active-case', CASE_ID);
  setCase(view);
  updateCaseUI();
  renderCaseList();
}

async function switchCase(caseId) {
  const view = await api(`/api/cases/${caseId}`);
  CASE_ID = view.case.caseId;
  localStorage.setItem('ps-active-case', CASE_ID);
  setCase(view);
  updateCaseUI();
  renderCaseList();
}

const AVATAR_COLORS = ['color-0','color-1','color-2','color-3','color-4'];

function caseStatusClass(state) {
  if (state === 'approved' || state === 'post_care_active') return 'st-approved';
  if (state === 'awaiting_review') return 'st-active';
  return 'st-empty';
}

function nameInitials(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function colorIndex(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h % AVATAR_COLORS.length;
}

async function renderCaseList() {
  const container = document.getElementById('case-list');
  if (!container) return;
  try {
    const cases = await api('/api/cases');
    if (!cases.length) {
      container.innerHTML = '<p class="hist-empty">No cases yet.</p>';
      return;
    }
    container.innerHTML = cases.map(c => {
      const name     = c.patientName || 'Unknown';
      const initials = nameInitials(name);
      const color    = AVATAR_COLORS[colorIndex(c.caseId)];
      const stCls    = caseStatusClass(c.workflowState || c.state || '');
      const active   = c.caseId === CASE_ID ? ' active' : '';
      return `<button class="case-list-item${active}" type="button" data-case-id="${esc(c.caseId)}">
        <span class="cli-avatar ${color}">${esc(initials)}</span>
        <span class="cli-body">
          <span class="cli-name">${esc(name)}</span>
          <span class="cli-id">${esc(c.caseId)}</span>
        </span>
        <span class="cli-status ${stCls}"></span>
      </button>`;
    }).join('');
    container.querySelectorAll('.case-list-item').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.caseId !== CASE_ID) run(null, () => switchCase(btn.dataset.caseId));
      });
    });
  } catch (_) {
    container.innerHTML = '<p class="hist-empty">—</p>';
  }
}

// ── actions ───────────────────────────────────────────────────────────────────

async function approveDraft() {
  const approvedBy = ($("#approved-by")?.value || '').trim() || getClinician();
  if (!approvedBy) throw new Error("Enter the approving clinician's name.");
  const body = {
    summary: draftEdit.summary,
    careTasks: draftEdit.careTasks.map((t) => ({
      id: t.id, instruction: t.instruction, timing: t.timing,
      responsibleParty: t.responsibleParty, sourceRefs: t.sourceRefs,
    })),
    approvedBy,
    inputRevision: draftEdit.inputRevision,
  };
  setCase(await api(`/api/cases/${CASE_ID}/approve`, { method: "POST", json: body }));
  setClinician(approvedBy);
  saveToHistory();
  window.toast?.('Care plan approved ✓ — at-home view is now unlocked', 'success', 6000);
}

async function sendQuestion(text) {
  text = text.trim();
  if (!text) return;
  window.setAIState?.('thinking');
  $("#interim").textContent = "";

  const conv = document.getElementById('conversation');
  if (conv) {
    const existing = conv.innerHTML.includes('empty-state') ? '' : conv.innerHTML;
    conv.innerHTML = existing + `
      <div class="msg-row msg-row-user">
        <div class="msg caregiver">${esc(text)}</div>
        <div class="msg-avatar msg-avatar-user" title="Caregiver">CG</div>
      </div>
      <div id="typing-indicator" class="msg-row msg-row-ai">
        <div class="msg-avatar msg-avatar-ai">✦</div>
        <div class="msg assistant typing-msg">
          <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
        </div>
      </div>`;
    conv.scrollTo({ top: conv.scrollHeight, behavior: 'smooth' });
  }

  try {
    await api(`/api/cases/${CASE_ID}/chat`, { method: "POST", json: { text } });
    document.getElementById('typing-indicator')?.remove();
    window.setAIState?.('speaking');
    setCase(await api(`/api/cases/${CASE_ID}`));
    setTimeout(() => window.setAIState?.('idle'), 3500);
  } catch (err) {
    document.getElementById('typing-indicator')?.remove();
    window.setAIState?.('idle');
    throw err;
  }
}

// ── speech (Reson8 Turns) ─────────────────────────────────────────────────────

const WORKLET = `
class Pcm16Downsampler extends AudioWorkletProcessor {
  constructor() {
    super(); this.ratio = sampleRate / 16000; this.pos = 0; this.out = [];
    this.port.onmessage = (e) => {
      if (e.data === "flush") { this.emit(); this.port.postMessage({ flushed: true }); }
    };
  }
  emit() {
    if (this.out.length) this.port.postMessage(Int16Array.from(this.out).buffer, []);
    this.out = [];
  }
  process(inputs) {
    const input = inputs[0][0];
    if (!input) return true;
    for (; this.pos < input.length; this.pos += this.ratio) {
      const s = Math.max(-1, Math.min(1, input[Math.floor(this.pos)]));
      this.out.push(s < 0 ? s * 0x8000 : s * 0x7fff);
    }
    this.pos -= input.length;
    if (this.out.length >= 1600) {
      this.emit();
    }
    return true;
  }
}
registerProcessor("pcm16-downsampler", Pcm16Downsampler);`;

// ── Voice via browser Web Speech API (free, no API key needed) ────────────────
const mic = { recognition: null, active: false };
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function startMic() {
  if (!SpeechRecognition) {
    throw new Error("Voice input is not supported in this browser. Try Chrome or Edge.");
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    mic.active = true;
    mic.recognition = recognition;
    $("#btn-mic").textContent = "■ Stop listening";
    $("#btn-mic").classList.add("recording");
    $("#mic-status").textContent = "Listening… speak your question.";
  };

  recognition.onresult = (event) => {
    const interim = Array.from(event.results).map(r => r[0].transcript).join("");
    $("#interim").textContent = interim;
    if (event.results[event.results.length - 1].isFinal) {
      const finalText = interim.trim();
      stopMic();
      if (finalText) run(null, () => sendQuestion(finalText));
    }
  };

  recognition.onerror = (event) => {
    stopMic();
    if (event.error !== "no-speech") showError(`Voice error: ${event.error}. Try typing instead.`);
  };

  recognition.onend = () => { if (mic.active) stopMic(); };

  recognition.start();
}

function stopMic() {
  mic.active = false;
  mic.recognition?.stop();
  mic.recognition = null;
  $("#btn-mic").textContent = "🎙 Start speaking";
  $("#btn-mic").classList.remove("recording");
  $("#mic-status").textContent = "";
  $("#interim").textContent = "";
}

function finishTurn() { stopMic(); }

// ── wiring ────────────────────────────────────────────────────────────────────

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tab.dataset.tab}`));
}));

// CCB new case button
document.getElementById('ccb-new-case-btn')?.addEventListener('click', () => {
  document.getElementById('new-patient-name').value = '';
  document.getElementById('new-clinician-name').value = getClinician();
  document.getElementById('new-patient-modal').classList.add('open');
  document.getElementById('new-patient-name').focus();
});

// New case button opens the new patient modal (no auto-reset)
$("#btn-reset").addEventListener("click", () => {
  document.getElementById('new-patient-name').value = '';
  document.getElementById('new-clinician-name').value = getClinician();
  document.getElementById('new-patient-modal').classList.add('open');
  document.getElementById('new-patient-name').focus();
});

$("#btn-upload").addEventListener("click", (e) => run(e.target, async () => {
  const file = $("#file").files[0];
  if (!file) throw new Error("Choose a PDF first.");
  const previous = caseView?.case.sources.find((s) => s.kind === "document");
  const form = new FormData();
  form.append("file", file);
  const view = await api(`/api/cases/${CASE_ID}/document`, { method: "POST", body: form });
  setCase(view);
  const current = view.case.sources.find((s) => s.kind === "document");
  const replaced = previous && previous.filename !== current.filename
    ? ` It replaced ${previous.filename}.` : "";
  $("#upload-status").textContent =
    `Loaded ${current.filename} · ${current.passages.length} passage(s).${replaced}`;
  window.toast?.(`Document ready — ${current.passages.length} passages extracted`, 'success');
}));

$("#btn-draft").addEventListener("click", (e) => run(e.target, async () => {
  e.target.innerHTML = "Drafting…";
  const badgeText = document.getElementById('ai-badge-text')?.textContent || 'AI';
  const label = `${badgeText} is generating your care draft…`;
  const tid = window.toast?.(label, 'info', 0);
  try {
    setCase(await api(`/api/cases/${CASE_ID}/summary`, { method: "POST" }));
    window.toast?.('Draft ready — review and approve before sharing', 'success');
  } finally {
    const btnLabel = '<span>✦</span> Generate draft with AI';
    e.target.innerHTML = btnLabel;
    window.dismissToast?.(tid);
  }
}));

$("#chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#chat-input");
  const text = input.value;
  input.value = "";
  run(e.submitter, () => sendQuestion(text));
});

$("#btn-mic").addEventListener("click", (e) => {
  if (mic.active) { stopMic(); return; }
  try { startMic(); } catch (err) { showError(err.message); }
});

// History modal
document.getElementById('hist-modal-close')?.addEventListener('click', () => {
  document.getElementById('history-modal')?.classList.remove('open');
  window.stopReading?.();
});
document.getElementById('history-modal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    e.currentTarget.classList.remove('open');
    window.stopReading?.();
  }
});

// New patient modal
document.getElementById('btn-new-case')?.addEventListener('click', () => {
  document.getElementById('new-patient-name').value = '';
  document.getElementById('new-clinician-name').value = getClinician();
  document.getElementById('new-patient-modal').classList.add('open');
  document.getElementById('new-patient-name').focus();
});
document.getElementById('new-patient-close')?.addEventListener('click', () => {
  document.getElementById('new-patient-modal').classList.remove('open');
});
document.getElementById('new-patient-cancel')?.addEventListener('click', () => {
  document.getElementById('new-patient-modal').classList.remove('open');
});
document.getElementById('new-patient-confirm')?.addEventListener('click', (e) => {
  run(e.target, async () => {
    const patientName = document.getElementById('new-patient-name')?.value.trim();
    const clinicianName = document.getElementById('new-clinician-name')?.value.trim();
    if (!patientName) throw new Error('Enter a patient name.');
    if (clinicianName) setClinician(clinicianName);
    const slug = patientName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 64) || 'patient';
    document.getElementById('new-patient-modal').classList.remove('open');
    await loadCase(false, slug);
    window.toast?.(`New case created for ${patientName}`, 'success');
  });
});
document.getElementById('new-patient-modal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
});

// Clinician identity modal
document.getElementById('btn-set-clinician')?.addEventListener('click', () => {
  const input = document.getElementById('clinician-name-input');
  if (input) input.value = getClinician();
  document.getElementById('clinician-modal')?.classList.add('open');
  input?.focus();
});
document.getElementById('clinician-modal-close')?.addEventListener('click', () => {
  document.getElementById('clinician-modal').classList.remove('open');
});
document.getElementById('clinician-modal-cancel')?.addEventListener('click', () => {
  document.getElementById('clinician-modal').classList.remove('open');
});
document.getElementById('clinician-modal-save')?.addEventListener('click', () => {
  const name = document.getElementById('clinician-name-input')?.value.trim();
  if (!name) { window.toast?.('Enter your name first.', 'error'); return; }
  setClinician(name);
  document.getElementById('clinician-modal').classList.remove('open');
  window.toast?.('Clinician name saved', 'success');
});
document.getElementById('clinician-modal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
});

// ── keyboard shortcuts ────────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    const input = document.getElementById('chat-input');
    if (input) { e.preventDefault(); input.focus(); input.select(); }
  }
  if (e.key === 'Escape') {
    document.getElementById('history-modal')?.classList.remove('open');
    document.getElementById('new-patient-modal')?.classList.remove('open');
    document.getElementById('clinician-modal')?.classList.remove('open');
    window.stopReading?.();
  }
});

document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    document.getElementById('chat-form')?.requestSubmit();
  }
});

// ── backend info + demo ───────────────────────────────────────────────────────

async function fetchBackendInfo() {
  try {
    const info = await fetch('/api/info').then(r => r.json());
    const badge = document.getElementById('ai-badge');
    const text = document.getElementById('ai-badge-text');
    const draftBtn = document.getElementById('btn-draft');
    if (!badge || !text || !info.backend) return;
    badge.dataset.backend = info.backend;
    if (info.backend === 'gemini') {
      const short = (info.model || 'gemini').replace('gemini-', '');
      text.textContent = `Gemini · ${short}`;
      badge.title = `Google Gemini · ${info.model} · free tier`;
      if (draftBtn) draftBtn.innerHTML = '<span>✦</span> Generate draft with AI';
    } else if (info.backend === 'openrouter') {
      const short = (info.model || 'openrouter').split('/').pop()?.replace(/:free$/, '') || 'openrouter';
      text.textContent = `OpenRouter · ${short}`;
      badge.title = `OpenRouter · ${info.model} · free`;
      if (draftBtn) draftBtn.innerHTML = '<span>✦</span> Generate draft with AI';
    } else if (info.backend === 'groq') {
      const short = (info.model || 'groq').replace('-versatile', '').replace('-instant', '');
      text.textContent = `Groq · ${short}`;
      badge.title = `Groq Cloud · ${info.model} · free tier`;
      if (draftBtn) draftBtn.innerHTML = '<span>✦</span> Generate draft with AI';
    } else if (info.backend === 'ollama') {
      const short = (info.model || 'ollama').replace(/:latest$/, '');
      text.textContent = `Ollama · ${short}`;
      badge.title = `Local AI · Ollama · ${info.model}`;
      if (draftBtn) draftBtn.innerHTML = '<span>✦</span> Generate draft with AI';
    } else {
      const short = (info.model || 'ai').replace('claude-', '').replace(/-\d{4}-\d{2}-\d{2}$/, '');
      text.textContent = `AI · ${short}`;
      badge.title = `AI · ${info.model}`;
      if (draftBtn) draftBtn.innerHTML = '<span>✦</span> Generate draft with AI';
    }
    // If browser doesn't support Web Speech API, disable the mic button
    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
      const micBtn = document.getElementById('btn-mic');
      if (micBtn) {
        micBtn.disabled = true;
        micBtn.title = 'Voice not supported in this browser — use Chrome or Edge';
        micBtn.style.opacity = '0.45';
        micBtn.style.cursor = 'not-allowed';
      }
    }
  } catch (_) {}
}

async function loadDemoCase() {
  const btn = document.getElementById('btn-demo-seed');
  if (btn) { btn.disabled = true; btn.querySelector('.demo-seed-text strong').textContent = 'Loading…'; }
  try {
    const view = await api('/api/demo/seed', { method: 'POST' });
    CASE_ID = view.case.caseId;
    localStorage.setItem('ps-active-case', CASE_ID);
    setCase(view);
    updateCaseUI();
    await renderCaseList();
    window.toast?.('Demo patient loaded — Emily Carter · approved care plan ready', 'success', 4000);
    // Switch to caregiver tab to show the live plan
    const cgTab = document.querySelector('[data-tab="caregiver"]');
    cgTab?.click();
  } catch (err) {
    window.toast?.(err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.querySelector('.demo-seed-text strong').textContent = 'Load Demo Patient'; }
  }
}

document.getElementById('btn-demo-seed')?.addEventListener('click', loadDemoCase);

// ── startup ───────────────────────────────────────────────────────────────────

updateClinicianUI();
renderHistoryPanel();

(async () => {
  fetchBackendInfo(); // fire-and-forget — badge updates asynchronously
  try {
    const savedId = localStorage.getItem('ps-active-case');
    if (savedId) {
      try {
        const view = await api(`/api/cases/${savedId}`);
        CASE_ID = view.case.caseId;
        localStorage.setItem('ps-active-case', CASE_ID);
        setCase(view);
        updateCaseUI();
        await renderCaseList();
      } catch (_) {
        // Case not found (server restarted and cleared /data) — re-seed the demo
        try {
          const demoView = await api('/api/demo/seed', { method: 'POST' });
          CASE_ID = demoView.case.caseId;
          localStorage.setItem('ps-active-case', CASE_ID);
          setCase(demoView);
          updateCaseUI();
          await renderCaseList();
        } catch (_2) {
          await loadCase(false, 'default');
        }
      }
    } else {
      // First visit — seed the demo so the app starts with a working example
      try {
        const view = await api('/api/demo/seed', { method: 'POST' });
        CASE_ID = view.case.caseId;
        localStorage.setItem('ps-active-case', CASE_ID);
        setCase(view);
        updateCaseUI();
        await renderCaseList();
      } catch (_) {
        await loadCase(false, 'default');
      }
    }
  } catch (err) {
    showError(err.message);
  } finally {
    const overlay = document.getElementById('app-loading');
    if (overlay) {
      overlay.style.transition = 'opacity .5s ease';
      overlay.style.opacity = '0';
      setTimeout(() => { overlay.hidden = true; }, 520);
    }
  }
})();
