'use strict';

/* ═══════════════════════════════════════════════════════════════
   DARK / LIGHT THEME TOGGLE
   window.toggleTheme()
═══════════════════════════════════════════════════════════════ */
(function () {
  const THEME_KEY = 'ps-theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.textContent = theme === 'light' ? '☾' : '☀';
      btn.title = theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
    });
  }

  const saved = localStorage.getItem(THEME_KEY) ?? 'dark';
  applyTheme(saved);

  window.toggleTheme = function () {
    const cur  = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  };
})();

/* ═══════════════════════════════════════════════════════════════
   QUICK-ACTION PRESET BUTTONS
   window.generateQuickActions(careTasks, summary) → string[]
═══════════════════════════════════════════════════════════════ */
window.generateQuickActions = function (careTasks, summary) {
  const full = (careTasks.map(t => t.instruction).join(' ') + ' ' + (summary || '')).toLowerCase();
  const actions = [];
  if (/medication|medicine|drug|tablet|pill|dose/.test(full))   actions.push('I took my medication ✓');
  if (/exercise|walk|physio|therapy|activity/.test(full))        actions.push('I completed my exercises ✓');
  if (/dressing|wound|bandage|incision/.test(full))              actions.push('I changed the dressing ✓');
  if (/rest|sleep|lying|bed/.test(full))                         actions.push('I rested as instructed ✓');
  if (/diet|food|fluid|drink|water/.test(full))                  actions.push('I followed my diet today ✓');
  actions.push("I'm feeling better today");
  actions.push('I have a question for my doctor');
  return [...new Set(actions)].slice(0, 5);
};

/* ═══════════════════════════════════════════════════════════════
   AI AVATAR STATE CONTROLLER
   window.setAIState(state)
   state: 'idle' | 'thinking' | 'speaking'
═══════════════════════════════════════════════════════════════ */
(function () {
  const TEXTS = { idle: 'Ready to help', thinking: 'Thinking…', speaking: 'Speaking…' };
  const STATUS_COLORS = { idle: '', thinking: 'var(--violet)', speaking: 'var(--mint)' };

  window.setAIState = function (state) {
    // Holographic face avatar
    const holo    = document.getElementById('holo-container');
    const holoTxt = document.getElementById('holo-status-text');
    if (holo)    holo.setAttribute('data-state', state);
    if (holoTxt) holoTxt.textContent = TEXTS[state] ?? state;

    // Legacy orb (graceful no-op if removed)
    const orb    = document.getElementById('ai-orb');
    const bars   = document.getElementById('ai-wave-bars');
    const status = document.getElementById('ai-avatar-status');
    if (orb)    orb.className = `ai-orb ai-orb-${state}`;
    if (bars)   bars.classList.toggle('active', state !== 'idle');
    if (status) {
      status.textContent = TEXTS[state] ?? state;
      status.style.color = STATUS_COLORS[state] ?? '';
    }
  };
})();

/* ═══════════════════════════════════════════════════════════════
   TOAST SYSTEM
   window.toast(message, type, duration)
   type    : 'success' | 'error' | 'info' | 'warning'
   duration: ms — 0 = persistent until window.dismissToast(id)
   returns : toast element id (string)
═══════════════════════════════════════════════════════════════ */
(function () {
  const container = document.getElementById('toast-container');
  if (!container) return;
  let seq = 0;
  const ICONS = { success: '✓', error: '✕', info: '◉', warning: '!' };

  function dismiss(el) {
    if (!el || el._out) return;
    el._out = true;
    el.classList.remove('toast-enter');
    el.classList.add('toast-exit');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
  }

  window.toast = function (message, type = 'info', duration = 4000) {
    const id = `toast-${++seq}`;
    const el = document.createElement('div');
    el.id = id;
    el.className = `toast toast-${type}`;
    el.setAttribute('role', 'alert');
    el.innerHTML = `
      <span class="toast-icon">${ICONS[type] ?? '◉'}</span>
      <span class="toast-msg">${message}</span>
      <button class="toast-close" aria-label="Dismiss">✕</button>`;
    el.querySelector('.toast-close').addEventListener('click', () => dismiss(el));
    container.appendChild(el);
    /* double rAF guarantees the browser paints the initial state first */
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('toast-enter')));
    if (duration > 0) setTimeout(() => dismiss(el), duration);
    return id;
  };

  window.dismissToast = function (id) { dismiss(document.getElementById(id)); };
})();

/* ═══════════════════════════════════════════════════════════════
   VOICE WAVEFORM VISUALISER
   window.startWaveform(analyserNode)
   window.stopWaveform()
═══════════════════════════════════════════════════════════════ */
(function () {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let raf = null;

  function stop() {
    if (raf) { cancelAnimationFrame(raf); raf = null; }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.display = 'none';
  }

  window.startWaveform = function (analyser) {
    stop();
    analyser.fftSize = 128;
    const bufLen = analyser.frequencyBinCount;
    const buf    = new Uint8Array(bufLen);
    canvas.style.display = 'block';

    function frame() {
      raf = requestAnimationFrame(frame);
      analyser.getByteFrequencyData(buf);

      const W = canvas.width  = canvas.offsetWidth  || 400;
      const H = canvas.height = canvas.offsetHeight || 54;
      ctx.clearRect(0, 0, W, H);

      const gap  = 3;
      const barW = Math.max(2, W / bufLen * 2.2 - gap);
      const startX = (W - bufLen * (barW + gap)) / 2;

      for (let i = 0; i < bufLen; i++) {
        const ratio = buf[i] / 255;
        const bh    = Math.max(3, ratio * H * 0.88);
        /* gradient from violet (#8B7EF5) → mint (#0DD6A8) */
        const t = i / bufLen;
        const r = Math.round(139 * (1 - t) + 13  * t);
        const g = Math.round(126 * (1 - t) + 214 * t);
        const b = Math.round(245 * (1 - t) + 168 * t);
        ctx.fillStyle = `rgba(${r},${g},${b},${0.45 + ratio * 0.55})`;
        const x = startX + i * (barW + gap);
        const y = (H - bh) / 2;
        if (ctx.roundRect) {
          ctx.beginPath(); ctx.roundRect(x, y, barW, bh, barW / 2); ctx.fill();
        } else {
          ctx.fillRect(x, y, barW, bh);
        }
      }
    }
    frame();
  };

  window.stopWaveform = stop;
})();

/* ═══════════════════════════════════════════════════════════════
   RECORDING TIMER
   window.startRecordingTimer()
   window.stopRecordingTimer()
═══════════════════════════════════════════════════════════════ */
(function () {
  let interval = null;
  let secs = 0;

  function stop() {
    if (interval) { clearInterval(interval); interval = null; }
    const el = document.getElementById('record-timer');
    if (el) el.style.display = 'none';
  }

  window.startRecordingTimer = function () {
    stop();
    secs = 0;
    const el  = document.getElementById('record-timer');
    const val = el?.querySelector('.rtimer-val');
    if (!el || !val) return;
    el.style.display = 'inline-flex';
    val.textContent  = '00:00';
    interval = setInterval(() => {
      secs++;
      val.textContent =
        `${String(Math.floor(secs / 60)).padStart(2, '0')}:${String(secs % 60).padStart(2, '0')}`;
    }, 1000);
  };

  window.stopRecordingTimer = stop;
})();

/* ═══════════════════════════════════════════════════════════════
   PDF EXPORT
   window.exportCarePlanPDF(data)
   data: { patientName, summary, careTasks, approvedBy, approvedAt, version }
═══════════════════════════════════════════════════════════════ */
(function () {
  window.exportCarePlanPDF = function (data) {
    if (!window.jspdf) {
      window.toast?.('PDF library not loaded yet — please try again', 'warning');
      return;
    }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const W = 210, M = 18;
    let y = 0;

    // Header bar
    doc.setFillColor(7, 12, 24);
    doc.rect(0, 0, W, 44, 'F');
    // Gradient accent line at header base
    doc.setFillColor(139, 126, 245);
    doc.rect(0, 42.5, W * 0.45, 1.5, 'F');
    doc.setFillColor(13, 214, 168);
    doc.rect(W * 0.45, 42.5, W * 0.55, 1.5, 'F');

    // Brand
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(20);
    doc.setTextColor(255, 255, 255);
    doc.text('PlainSpeak', M, 18);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor(99, 112, 144);
    doc.text('CARE INTELLIGENCE', M, 24);
    doc.setFontSize(10);
    doc.setTextColor(152, 171, 202);
    doc.text('Approved Care Instructions', M, 35);

    // Approved badge
    doc.setFillColor(22, 163, 100);
    doc.roundedRect(W - M - 46, 10, 46, 14, 3, 3, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(255, 255, 255);
    doc.text('CLINICIAN APPROVED', W - M - 46 + 5, 18.5);

    y = 56;

    // Patient info block
    doc.setFillColor(240, 244, 252);
    doc.setDrawColor(210, 222, 245);
    doc.setLineWidth(0.4);
    doc.roundedRect(M, y, W - M * 2, 26, 4, 4, 'FD');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(20, 30, 55);
    doc.text(data.patientName || 'Patient', M + 8, y + 10);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    doc.setTextColor(80, 100, 140);
    doc.text('Case PS-2048', M + 8, y + 17);
    doc.text(`Version ${data.version}  ·  Approved by ${data.approvedBy}  ·  ${data.approvedAt}`, M + 8, y + 23);

    y += 36;

    // Summary section
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(107, 95, 224);
    doc.text('SUMMARY', M, y);
    doc.setDrawColor(107, 95, 224);
    doc.setLineWidth(0.4);
    doc.line(M, y + 2.5, W - M, y + 2.5);
    y += 9;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(30, 40, 65);
    const summaryLines = doc.splitTextToSize(data.summary || '', W - M * 2);
    doc.text(summaryLines, M, y);
    y += summaryLines.length * 5.5 + 12;

    // Care tasks section
    if (data.careTasks && data.careTasks.length > 0) {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(11, 163, 128);
      doc.text('CARE TASKS', M, y);
      doc.setDrawColor(11, 163, 128);
      doc.setLineWidth(0.4);
      doc.line(M, y + 2.5, W - M, y + 2.5);
      y += 10;

      data.careTasks.forEach((task, i) => {
        if (y > 265) { doc.addPage(); y = 20; }
        if (i % 2 === 0) {
          doc.setFillColor(246, 248, 255);
          doc.rect(M, y - 4, W - M * 2, 13, 'F');
        }
        doc.setFillColor(139, 126, 245);
        doc.circle(M + 3.5, y + 1.5, 2.5, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(255, 255, 255);
        doc.text(String(i + 1), M + 3.5 - (i >= 9 ? 1.5 : 0.8), y + 2.3);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9.5);
        doc.setTextColor(30, 40, 65);
        const tLines = doc.splitTextToSize(task.instruction, W - M * 2 - 12);
        doc.text(tLines, M + 10, y + 2);

        let rowH = tLines.length * 5 + 4;
        if (task.timing) {
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(7.5);
          doc.setTextColor(110, 130, 180);
          doc.text(`Timing: ${task.timing}`, M + 10, y + tLines.length * 5 + 4);
          rowH += 5;
        }
        if (task.responsibleParty && task.responsibleParty !== 'unspecified') {
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(7);
          doc.setTextColor(11, 163, 128);
          doc.text(`→ ${task.responsibleParty.replace('_', ' ')}`, W - M - 26, y + 2);
        }
        y += rowH + 2;
      });
    }

    // Footer on every page
    const pageCount = doc.internal.getNumberOfPages();
    for (let p = 1; p <= pageCount; p++) {
      doc.setPage(p);
      doc.setFillColor(245, 247, 252);
      doc.rect(0, 284, W, 13, 'F');
      doc.setDrawColor(210, 220, 240);
      doc.setLineWidth(0.3);
      doc.line(0, 284, W, 284);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7);
      doc.setTextColor(130, 150, 180);
      doc.text(`PlainSpeak Lab  ·  Generated ${new Date().toLocaleString()}  ·  Synthetic demo only`, M, 291);
      doc.text(`Page ${p} of ${pageCount}`, W - M - 18, 291);
    }

    const fname = `plainspeak-care-plan-${(data.patientName || 'patient').toLowerCase().replace(/\s+/g, '-')}-v${data.version}.pdf`;
    doc.save(fname);
    window.toast?.('↓ Care plan PDF downloaded', 'success');
  };
})();

/* ═══════════════════════════════════════════════════════════════
   TEXT-TO-SPEECH READBACK
   window.readAloud(text, onDone)
   window.stopReading()
   window.isReading() → boolean
═══════════════════════════════════════════════════════════════ */
(function () {
  let current = null;

  function getVoice() {
    const voices = window.speechSynthesis?.getVoices() ?? [];
    return voices.find(v => v.lang.startsWith('en') && /samantha|zira|karen|female/i.test(v.name))
      || voices.find(v => v.lang.startsWith('en'))
      || voices[0]
      || null;
  }

  window.readAloud = function (text, onDone) {
    if (!window.speechSynthesis) {
      window.toast?.('Text-to-speech is not supported in this browser', 'warning');
      return;
    }
    window.stopReading();
    const utt = new SpeechSynthesisUtterance(text);
    utt.rate  = 0.93;
    utt.pitch = 1.02;
    // Voices may load async
    const voice = getVoice();
    if (voice) utt.voice = voice;
    else speechSynthesis.addEventListener('voiceschanged', () => {
      const v2 = getVoice(); if (v2) utt.voice = v2;
    }, { once: true });

    utt.onend   = () => { current = null; onDone?.(); };
    utt.onerror = () => { current = null; onDone?.(); };
    current = utt;
    speechSynthesis.speak(utt);
  };

  window.stopReading = function () {
    if (window.speechSynthesis?.speaking) speechSynthesis.cancel();
    current = null;
  };

  window.isReading = function () {
    return window.speechSynthesis?.speaking ?? false;
  };
})();
