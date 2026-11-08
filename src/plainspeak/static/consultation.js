"use strict";

// Realtime remains open across patient/clinician turns. Only finalized text is persisted.
const consultation = {
  active: false, starting: false, stopping: false,
  ws: null, capture: null,
  recognition: null,   // Web Speech API instance (replaces Reson8 WebSocket)
  currentSpeaker: 0,   // 0 = clinician, 1 = patient
  sessionId: null, queue: Promise.resolve(), pending: new Map(), flushResolve: null,
};
const manualSessionId = `manual_${crypto.randomUUID()}`;

function renderConsultation() {
  if (!caseView) return;
  const c = caseView.case;
  const segments = c.transcriptSegments ?? [];
  const roles = c.speakerRoles ?? {};
  const keys = [...new Set(segments.map((s) => `${s.sessionId}:${s.speakerId ?? "unknown"}`))];
  $("#consult-speakers").innerHTML = keys.length ? `
    <p class="muted">Speaker IDs are anonymous. Confirm who is speaking before reviewing the draft.</p>
    <div class="speaker-mapping">${keys.map((key, i) => `
      <label>Voice ${i + 1}
        <select data-speaker-key="${esc(key)}" aria-label="Role for voice ${i + 1}">
          ${["unknown", "clinician", "patient"].map((role) =>
            `<option value="${role}" ${(roles[key] ?? "unknown") === role ? "selected" : ""}>${role === "unknown" ? "Not confirmed" : role}</option>`).join("")}
        </select>
      </label>`).join("")}</div>` : "";
  $("#consult-speakers").querySelectorAll("[data-speaker-key]").forEach((select) => {
    select.addEventListener("change", () => run(select, async () => {
      const key = select.dataset.speakerKey;
      const role = select.value;
      consultation.queue = consultation.queue.catch(() => {}).then(async () => {
        setCase(await api(`/api/cases/${CASE_ID}/transcript`, {
          method: "POST", json: { segments: [], speakerRoles: { [key]: role } },
        }));
      });
      await consultation.queue;
    }));
  });
  $("#btn-clear-transcript").hidden = segments.length === 0;
  $("#consult-transcript").innerHTML = segments.map((s) => {
    const key = `${s.sessionId}:${s.speakerId ?? "unknown"}`;
    const role = roles[key] ?? "unknown";
    const voice = keys.indexOf(key) + 1;
    const timing = s.startMs == null ? "" : ` · ${(s.startMs / 1000).toFixed(1)}s`;
    const origin = s.sessionId.startsWith("manual_") ? " · manually entered"
      : s.sessionId.startsWith("pdf_") ? " · imported from PDF" : "";
    return `<div class="transcript-line ${esc(role)}"><strong>${role === "unknown" ? `Voice ${voice} (unconfirmed)` : esc(role)}</strong><span class="muted">${timing}${origin}</span><div>${esc(s.text)}</div></div>`;
  }).join("") || '<p class="muted">No consultation transcript saved yet.</p>';
  $("#consult-transcript").scrollTop = $("#consult-transcript").scrollHeight;
  renderConsultationControls();
}

function renderConsultationControls() {
  const busy = consultation.active || consultation.starting || consultation.stopping;
  $("#btn-consult-start").disabled = busy;
  $("#btn-consult-stop").disabled = !consultation.active || consultation.stopping;
  ["#btn-reset", "#btn-create", "#btn-draft", "#btn-manual-transcript", "#btn-transcript-pdf", "#btn-upload", "#btn-clear-transcript"].forEach((id) => {
    $(id).disabled = busy || consultation.pending.size > 0;
  });
  $("#consult-consent").disabled = busy;
  $("#consult-language").disabled = busy;
  const approveButton = $("#btn-approve");
  if (approveButton) approveButton.disabled = busy || consultation.pending.size > 0;
  $("#consult-recovery").innerHTML = consultation.pending.size ? `
    <p class="error">${consultation.pending.size} finalized segment(s) are not saved. Keep this page open.</p>
    <button id="retry-transcript" class="secondary">Retry saving transcript</button>` : "";
  $("#retry-transcript")?.addEventListener("click", (e) => run(e.target, async () => {
    for (const segment of [...consultation.pending.values()]) await queueConsultationSegment(segment);
  }));

  // Speaker toggle — visible only during active Web Speech recording
  const existingToggle = document.getElementById("consult-speaker-toggle");
  if (consultation.active && consultation.recognition) {
    if (!existingToggle) {
      const toggle = document.createElement("div");
      toggle.id = "consult-speaker-toggle";
      toggle.className = "speaker-toggle-row";
      toggle.innerHTML = `
        <span class="toggle-label">Who is speaking</span>
        <button type="button" class="spk-btn${consultation.currentSpeaker === 0 ? " spk-active" : ""}" data-spk="0">◉ Clinician</button>
        <button type="button" class="spk-btn${consultation.currentSpeaker === 1 ? " spk-active" : ""}" data-spk="1">♡ Patient</button>`;
      toggle.querySelectorAll(".spk-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          consultation.currentSpeaker = Number(btn.dataset.spk);
          toggle.querySelectorAll(".spk-btn").forEach((b) => b.classList.toggle("spk-active", b === btn));
        });
      });
      document.getElementById("consult-interim")?.before(toggle);
    }
  } else if (existingToggle) {
    existingToggle.remove();
  }
}

function queueConsultationSegment(segment, roles = {}) {
  consultation.pending.set(segment.id, segment);
  renderConsultationControls();
  consultation.queue = consultation.queue.catch(() => {}).then(async () => {
    try {
      const view = await api(`/api/cases/${CASE_ID}/transcript`, {
        method: "POST", json: { segments: [segment], speakerRoles: roles },
      });
      consultation.pending.delete(segment.id);
      setCase(view);
    } catch (err) {
      showError(`Transcript save failed: ${err.message}. Use Retry saving transcript.`);
      renderConsultationControls();
      throw err;
    }
  });
  return consultation.queue;
}

function closeConsultationCapture() {
  consultation.capture?.stop();
  consultation.capture = null;
  if (consultation.recognition) {
    consultation.recognition.onend = null;  // prevent auto-restart loop
    try { consultation.recognition.stop(); } catch {}
    consultation.recognition = null;
  }
  const ws = consultation.ws;
  consultation.ws = null;
  consultation.active = false;
  consultation.starting = false;
  window.stopWaveform?.();
  window.stopRecordingTimer?.();
  if (ws && ws.readyState < WebSocket.CLOSING) ws.close(1000);
  $("#consult-interim").textContent = "";
  renderConsultationControls();
}

async function startConsultation() {
  if (!$("#consult-consent").checked) throw new Error("Confirm participant consent before recording.");
  if (mic.active) throw new Error("Finish the caregiver question first.");
  if (consultation.active || consultation.starting || consultation.stopping) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    $("#consult-status").textContent = "Live capture unavailable — use transcript upload or manual entry below.";
    return;
  }

  consultation.starting = true;
  renderConsultationControls();
  consultation.sessionId = crypto.randomUUID();

  try {
    const recognition = new SpeechRecognition();
    const lang = $("#consult-language").value;
    recognition.lang = lang === "de" || lang === "de,en" ? "de-DE" : "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const interim = Array.from(event.results)
        .slice(event.resultIndex)
        .map((r) => r[0].transcript)
        .join("");
      $("#consult-interim").textContent = interim;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          const text = event.results[i][0].transcript.trim();
          if (!text) continue;
          const speakerId = consultation.currentSpeaker;
          const roles = {
            [`${consultation.sessionId}:0`]: "clinician",
            [`${consultation.sessionId}:1`]: "patient",
          };
          queueConsultationSegment({
            id: `seg_${crypto.randomUUID()}`,
            sessionId: consultation.sessionId,
            text,
            speakerId,
            startMs: null,
            durationMs: null,
          }, roles).catch(() => {});
          $("#consult-interim").textContent = "";
        }
      }
    };

    recognition.onerror = (event) => {
      if (event.error === "no-speech" || event.error === "aborted") return;
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        closeConsultationCapture();
        $("#consult-status").textContent = "Microphone access denied. Check browser permissions and try again.";
        return;
      }
      closeConsultationCapture();
      showError(`Voice error: ${event.error}. Use manual entry below.`);
    };

    // Browser stops after silence — restart to stay continuous
    recognition.onend = () => {
      if (consultation.active && !consultation.stopping) {
        try { consultation.recognition?.start(); } catch {}
      }
    };

    // Set recognition reference before .start() so the onend auto-restart has it
    consultation.recognition = recognition;
    recognition.start();
    consultation.active = true;
    consultation.starting = false;

    window.startRecordingTimer?.();
    window.toast?.("Recording started — tap Clinician or Patient below to mark who is speaking", "info", 5000);
    $("#consult-status").textContent = "Listening. Tap Clinician or Patient below to mark who is speaking.";
    renderConsultationControls();
  } catch (err) {
    closeConsultationCapture();
    throw err;
  }
}

async function endConsultation() {
  if (!consultation.active || consultation.stopping) return;
  consultation.stopping = true;
  renderConsultationControls();
  $("#consult-status").textContent = "Saving transcript…";
  try {
    if (consultation.recognition) {
      consultation.recognition.onend = null;
      try { consultation.recognition.stop(); } catch {}
      consultation.recognition = null;
    }
    await consultation.queue;
    if (consultation.pending.size) throw new Error("Some transcript lines still need saving. Use Retry saving transcript.");
    window.toast?.("Consultation saved — confirm speaker roles, then generate a draft", "success");
    $("#consult-status").textContent = "Consultation saved. Confirm speaker roles, then add the document and generate a draft.";
  } finally {
    closeConsultationCapture();
    consultation.stopping = false;
    renderConsultationControls();
  }
}

$("#btn-consult-start").addEventListener("click", () => run(null, startConsultation));
$("#btn-consult-stop").addEventListener("click", () => run(null, endConsultation));
$("#btn-manual-transcript").addEventListener("click", (event) => run(event.target, async () => {
  const input = $("#manual-transcript");
  if (!input.value.trim()) throw new Error("Enter a transcript line first.");
  if (!$("#consult-consent").checked) throw new Error("Confirm participant consent first.");
  const speakerId = Number($("#manual-speaker").value);
  await queueConsultationSegment({
    id: `seg_${crypto.randomUUID()}`, sessionId: manualSessionId,
    speakerId, text: input.value.trim(), startMs: null, durationMs: null,
  }, { [`${manualSessionId}:${speakerId}`]: speakerId === 0 ? "clinician" : "patient" });
  input.value = "";
}));
$("#btn-transcript-pdf").addEventListener("click", (event) => run(event.target, async () => {
  const file = $("#transcript-file").files[0];
  if (!file) throw new Error("Choose a transcript PDF first.");
  if (!$("#consult-consent").checked) throw new Error("Confirm participant consent first.");
  const before = new Set((caseView?.case.transcriptSegments ?? []).map((s) => s.id));
  const form = new FormData();
  form.append("file", file);
  const view = await api(`/api/cases/${CASE_ID}/transcript/document`, { method: "POST", body: form });
  setCase(view);
  const segments = view.case.transcriptSegments ?? [];
  const fresh = segments.filter((s) => !before.has(s.id)).length;
  const dropped = before.size - segments.filter((s) => before.has(s.id)).length;
  const voices = new Set(segments.map((s) => `${s.sessionId}:${s.speakerId ?? "unknown"}`)).size;
  const replaced = dropped ? `, replacing ${dropped} previously captured line(s)` : "";
  const statusMsg = fresh
    ? `Imported ${fresh} line(s) from ${file.name} across ${voices} voice(s)${replaced}. Confirm each voice before reviewing the draft.`
    : `${file.name} was already imported; nothing changed.`;
  $("#consult-status").textContent = statusMsg;
  window.toast?.(fresh ? `${fresh} transcript lines imported from ${file.name}` : `${file.name} already imported — nothing changed`, fresh ? "success" : "warning");
}));
$("#btn-clear-transcript").addEventListener("click", (event) => run(event.target, async () => {
  if (!confirm("Clear the saved consultation transcript? This cannot be undone.")) return;
  setCase(await api(`/api/cases/${CASE_ID}/transcript/clear`, { method: "POST" }));
  $("#consult-status").textContent = "";
  window.toast?.("Transcript cleared", "warning");
}));
window.addEventListener("beforeunload", (event) => {
  if (consultation.active || consultation.starting || consultation.stopping || consultation.pending.size) {
    event.preventDefault();
    event.returnValue = "";
  }
});

// ---------- paste full conversation + auto-split ----------

let parsedSegments = [];

function parseFullConversation(raw) {
  const LABEL_RE = /^([^:\n]{1,40})\s*:\s*/;
  const PATIENT_RE = /\b(patient|caregiver|mr|mrs|ms|family)\b/i;
  const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);

  // Count labeled lines — if most have labels, use label mode
  const labeledCount = lines.filter(l => LABEL_RE.test(l)).length;
  const useLabels = labeledCount >= Math.ceil(lines.length / 2);
  const result = [];

  if (useLabels) {
    for (const line of lines) {
      const m = line.match(LABEL_RE);
      if (m) {
        const label = m[1].trim();
        const text  = line.slice(m[0].length).trim();
        if (!text) continue;
        const role = PATIENT_RE.test(label) ? 'patient' : 'clinician';
        result.push({ text, role, label });
      } else if (line && result.length) {
        // Continuation of previous turn
        result[result.length - 1].text += ' ' + line;
      } else if (line) {
        result.push({ text: line, role: 'clinician', label: null });
      }
    }
  } else {
    // No labels — use question-mark heuristic, then alternating
    lines.forEach((line, i) => {
      const hasQuestion = (line.match(/\?/g) ?? []).length >= 1;
      // Questions → clinician; statements after an odd position → patient
      const role = hasQuestion || i % 2 === 0 ? 'clinician' : 'patient';
      result.push({ text: line, role, label: null });
    });
  }
  return result;
}

function renderParsedPreview(segments) {
  const preview = document.getElementById('parsed-preview');
  const saveBtn = document.getElementById('btn-save-parsed');
  if (!preview) return;
  if (!segments.length) {
    preview.hidden = true;
    if (saveBtn) saveBtn.hidden = true;
    return;
  }
  preview.hidden = false;
  if (saveBtn) saveBtn.hidden = false;

  preview.innerHTML = segments.map((seg, i) => `
    <div class="parsed-seg" data-role="${seg.role}" data-idx="${i}">
      <select class="parsed-role-sel" data-idx="${i}" aria-label="Role for line ${i + 1}">
        <option value="clinician" ${seg.role === 'clinician' ? 'selected' : ''}>◉ Doctor / Clinician</option>
        <option value="patient"   ${seg.role === 'patient'   ? 'selected' : ''}>♡ Patient</option>
      </select>
      <div class="parsed-text">${esc(seg.text)}</div>
    </div>`).join('');

  preview.querySelectorAll('.parsed-role-sel').forEach(sel => {
    sel.addEventListener('change', () => {
      const idx = Number(sel.dataset.idx);
      parsedSegments[idx].role = sel.value;
      sel.closest('.parsed-seg').dataset.role = sel.value;
    });
  });
}

document.getElementById('btn-parse-convo')?.addEventListener('click', () => {
  const raw = (document.getElementById('full-convo-input')?.value ?? '').trim();
  if (!raw) { window.toast?.('Paste a conversation first', 'warning'); return; }
  parsedSegments = parseFullConversation(raw);
  renderParsedPreview(parsedSegments);
  window.toast?.(`${parsedSegments.length} turns detected — review roles then save`, 'info', 4000);
});

document.getElementById('btn-save-parsed')?.addEventListener('click', (e) => run(e.target, async () => {
  if (!document.getElementById('consult-consent')?.checked) {
    throw new Error('Confirm participant consent before saving.');
  }
  if (!parsedSegments.length) return;

  const sessionId = `manual_${crypto.randomUUID()}`;
  const roles = {
    [`${sessionId}:0`]: 'clinician',
    [`${sessionId}:1`]: 'patient',
  };

  for (const seg of parsedSegments) {
    await queueConsultationSegment({
      id: `seg_${crypto.randomUUID()}`,
      sessionId,
      speakerId: seg.role === 'patient' ? 1 : 0,
      text: seg.text,
      startMs: null,
      durationMs: null,
    }, roles);
  }

  window.toast?.(`${parsedSegments.length} segments saved with speaker roles`, 'success');
  document.getElementById('full-convo-input').value = '';
  const preview = document.getElementById('parsed-preview');
  if (preview) preview.hidden = true;
  const saveBtn = document.getElementById('btn-save-parsed');
  if (saveBtn) saveBtn.hidden = true;
  parsedSegments = [];
}));
