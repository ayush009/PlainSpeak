#!/usr/bin/env python3
"""Append Design System v3 CSS block to styles.css"""
import os

css_path = r'c:\Users\aayus\Desktop\PlainsSpeak\src\plainspeak\static\styles.css'

v3_block = r"""

/* ============================================================
   DESIGN SYSTEM v3 -- PREMIUM ENTERPRISE VISUAL OVERHAUL
   Targeted overrides for hospital-network polish
   ============================================================ */

/* -- A. Topbar -- premium glass panel ----------------------- */
.topbar {
  background: rgba(5, 8, 18, 0.95) !important;
  border-bottom: 1px solid rgba(139, 126, 245, 0.15) !important;
  -webkit-backdrop-filter: blur(32px) !important;
  backdrop-filter: blur(32px) !important;
  box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset, 0 4px 24px rgba(0,0,0,0.4) !important;
}
.topbar-compliance {
  height: 24px;
  background: rgba(139, 126, 245, 0.04);
  display: flex;
  align-items: center;
  padding: 0 36px;
  border-bottom: 1px solid rgba(139,126,245,0.07);
}
.topbar-main {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 36px;
  gap: 20px;
}
.tc-badge {
  font-size: 8.5px;
  letter-spacing: 1.4px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--muted);
  padding: 0 8px;
  border-right: 1px solid rgba(255,255,255,0.05);
}
.tc-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--mint);
  box-shadow: 0 0 5px rgba(13,214,168,0.5);
  display: inline-block;
}

/* -- B. Sidebar -- premium dark panel ----------------------- */
.brand-mark {
  width: 48px !important;
  height: 48px !important;
  border-radius: 16px !important;
  background: linear-gradient(145deg, #9B8FF7, #6558D8) !important;
  box-shadow:
    0 0 0 1px rgba(255,255,255,0.12),
    0 0 0 3px rgba(139,126,245,0.2),
    0 8px 28px rgba(101,88,216,0.55) !important;
}
.brand-mark svg {
  width: 26px !important;
}
.side-nav .tab.active {
  background: linear-gradient(135deg, rgba(139,126,245,0.16), rgba(100,89,220,0.08)) !important;
  border-color: rgba(139,126,245,0.25) !important;
  box-shadow: inset 0 0 24px rgba(139,126,245,0.06) !important;
}
.side-nav .tab.active::before {
  width: 3px !important;
  background: linear-gradient(to bottom, #B3A8FF, #7C6FE8) !important;
  box-shadow: 0 0 14px rgba(139,126,245,0.8) !important;
}
.case-card {
  background: rgba(139,126,245,0.05) !important;
  border: 1px solid rgba(139,126,245,0.12) !important;
  border-radius: 14px !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset !important;
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s !important;
}
.case-card:hover {
  background: rgba(139,126,245,0.09) !important;
  border-color: rgba(139,126,245,0.22) !important;
  box-shadow: 0 0 20px rgba(139,126,245,0.1) !important;
}
.profile-row {
  background: linear-gradient(135deg, rgba(139,126,245,0.04), rgba(13,21,37,0.6));
  border-radius: 10px;
  padding: 12px 8px !important;
  margin: 0 -4px;
}
.privacy-card {
  border-left: 3px solid rgba(13,214,168,0.5) !important;
  border-color: rgba(255,255,255,0.07) !important;
  background: rgba(13,214,168,0.03) !important;
}
.privacy-icon {
  color: var(--mint) !important;
}

/* -- C. Hero section -- compact & data-focused -------------- */
.page-intro {
  min-height: 300px !important;
  padding: 40px 48px !important;
}
.vital-float {
  background: linear-gradient(135deg,
    rgba(13,21,37,0.9) 0%,
    rgba(8,14,28,0.95) 100%) !important;
  border: 1px solid rgba(139,126,245,0.18) !important;
  box-shadow:
    0 8px 32px rgba(0,0,0,0.4),
    0 0 0 1px rgba(255,255,255,0.04) inset,
    0 0 20px rgba(139,126,245,0.08) !important;
  backdrop-filter: blur(20px) !important;
  padding: 12px 16px !important;
  border-radius: 14px !important;
}
.vf-val {
  font-size: 24px !important;
  font-weight: 800 !important;
  font-family: 'Manrope', sans-serif !important;
  line-height: 1 !important;
  color: var(--ink) !important;
}
.vf-icon {
  font-size: 18px !important;
  filter: drop-shadow(0 0 6px currentColor);
}
.ekg-path {
  filter: drop-shadow(0 0 4px rgba(139,126,245,0.7)) drop-shadow(0 0 2px rgba(13,214,168,0.5));
  stroke-width: 2.5 !important;
}

/* -- C2. Hero stats -- bigger numbers ----------------------- */
.hero-stats {
  background: linear-gradient(135deg, rgba(13,21,37,0.8), rgba(8,14,28,0.9)) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(20px) !important;
}
.hstat-n, .hstat-big {
  font-size: 38px !important;
  font-weight: 900 !important;
  font-family: 'Manrope', sans-serif !important;
  background: linear-gradient(135deg, var(--ink) 30%, var(--violet));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1 !important;
}
.hstat-top > span:not(.hstat-n):not(.hstat-big) {
  font-size: 22px !important;
  font-weight: 800 !important;
  color: var(--ink-2) !important;
  opacity: 0.7;
}
.hstat small {
  font-size: 10px !important;
  letter-spacing: 1.2px !important;
  text-transform: uppercase !important;
  font-weight: 700 !important;
}

/* -- D. Workflow cards -- magazine quality ------------------ */
.card {
  border: 1px solid rgba(255,255,255,0.06) !important;
  background: linear-gradient(145deg, rgba(13,21,37,0.9), rgba(8,14,28,0.95)) !important;
  backdrop-filter: blur(20px) !important;
  box-shadow:
    0 1px 0 rgba(255,255,255,0.04) inset,
    0 20px 60px rgba(0,0,0,0.4) !important;
  border-radius: 16px !important;
}
.step-icon.violet {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  box-shadow: 0 0 20px rgba(99,102,241,0.4) !important;
  color: #fff !important;
}
.step-icon.mint {
  background: linear-gradient(135deg, #0DD6A8, #059669) !important;
  box-shadow: 0 0 20px rgba(13,214,168,0.35) !important;
  color: #fff !important;
}
.step-icon.amber {
  background: linear-gradient(135deg, #F59E0B, #EF4444) !important;
  box-shadow: 0 0 20px rgba(245,158,11,0.35) !important;
  color: #fff !important;
}
.step-icon.green {
  background: linear-gradient(135deg, #22D3A0, #0DD6A8) !important;
  box-shadow: 0 0 20px rgba(34,211,160,0.35) !important;
  color: #fff !important;
}

/* -- E. Upload zone -- inviting and premium ----------------- */
.upload-zone {
  background: linear-gradient(135deg, rgba(13,21,37,0.8), rgba(8,14,28,0.9)) !important;
  border: 2px dashed rgba(139,126,245,0.3) !important;
  border-radius: 12px !important;
  padding: 28px 20px !important;
  text-align: center !important;
  transition: all 0.3s ease !important;
  position: relative !important;
  overflow: hidden !important;
}
.upload-zone::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(139,126,245,0.06), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
  pointer-events: none;
}
.upload-zone:hover::before {
  transform: translateX(100%);
}
.upload-zone:hover {
  border-color: rgba(139,126,245,0.6) !important;
  box-shadow: 0 0 30px rgba(139,126,245,0.12), inset 0 0 30px rgba(139,126,245,0.04) !important;
}
.upload-icon {
  font-size: 32px !important;
  color: var(--violet) !important;
  margin-bottom: 12px !important;
  display: block !important;
  filter: drop-shadow(0 0 8px rgba(139,126,245,0.5));
}

/* -- F. AI note box -- more prominent ----------------------- */
.ai-note {
  background: linear-gradient(135deg, rgba(139,126,245,0.08), rgba(13,214,168,0.04)) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  border-left: 3px solid var(--violet) !important;
  border-radius: 10px !important;
  padding: 14px 16px !important;
}
.ai-note strong { color: var(--violet); }

/* -- G. Buttons -- more premium ----------------------------- */
.button-primary {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  box-shadow:
    0 4px 20px rgba(99,102,241,0.35),
    0 1px 0 rgba(255,255,255,0.15) inset !important;
  border: none !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  border-radius: 10px !important;
}
.button-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #7C7FF5, #9D6BFA) !important;
  box-shadow:
    0 6px 28px rgba(99,102,241,0.5),
    0 1px 0 rgba(255,255,255,0.2) inset !important;
  transform: translateY(-1px) !important;
}
.button-secondary {
  background: rgba(139,126,245,0.08) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  color: var(--ink-2) !important;
  border-radius: 10px !important;
}
.button-secondary:hover:not(:disabled) {
  background: rgba(139,126,245,0.14) !important;
  border-color: rgba(139,126,245,0.4) !important;
  color: var(--ink) !important;
}

/* -- H. Journey card and side cards ------------------------- */
.journey-card {
  border-left: 3px solid var(--violet) !important;
}
.principles-card .principle-icon {
  color: var(--violet) !important;
  background: rgba(139,126,245,0.12) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
}
.quote-card {
  background: linear-gradient(135deg, rgba(13,21,37,0.9), rgba(8,14,28,0.95)) !important;
  border: 1px solid rgba(139,126,245,0.15) !important;
  border-left: 3px solid var(--mint) !important;
}

/* -- I. Report tab -- real dashboard feel ------------------- */
.report-card {
  min-height: 300px;
}
.empty-report {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 16px !important;
  padding: 60px 20px !important;
  text-align: center !important;
}
.empty-report > span {
  font-size: 48px !important;
  background: linear-gradient(135deg, var(--violet), var(--mint));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 16px rgba(139,126,245,0.4));
  display: block;
}
.empty-report h3 {
  font-size: 20px !important;
  font-weight: 700 !important;
  color: var(--ink) !important;
  margin: 0 !important;
}
.empty-report p {
  color: var(--muted) !important;
  max-width: 360px !important;
  margin: 0 !important;
}

/* -- J. Caregiver locked state ------------------------------ */
.locked-card {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 280px !important;
  text-align: center !important;
  gap: 16px !important;
  padding: 48px 32px !important;
  border: 1px solid rgba(240,169,75,0.15) !important;
  background: linear-gradient(135deg, rgba(240,169,75,0.04), rgba(13,21,37,0.8)) !important;
}
.locked-icon {
  font-size: 40px !important;
  color: var(--amber) !important;
  filter: drop-shadow(0 0 12px rgba(240,169,75,0.4));
}
.locked-tag {
  font-size: 9px !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  padding: 4px 12px !important;
  border-radius: 20px !important;
  background: rgba(240,169,75,0.1) !important;
  border: 1px solid rgba(240,169,75,0.25) !important;
  color: var(--amber) !important;
}

/* -- K. Chat input area -- premium -------------------------- */
.chat-input-row {
  display: flex !important;
  gap: 10px !important;
  align-items: center !important;
  background: rgba(13,21,37,0.8) !important;
  border: 1px solid rgba(139,126,245,0.15) !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  margin: 0 !important;
}
.chat-input-row:focus-within {
  border-color: rgba(139,126,245,0.4) !important;
  box-shadow: 0 0 0 3px rgba(139,126,245,0.08) !important;
}
#chat-input {
  flex: 1;
  background: transparent !important;
  border: none !important;
  outline: none !important;
  color: var(--ink) !important;
  font-size: 14px !important;
  padding: 0 !important;
}
.chat-input-row .button-primary {
  flex-shrink: 0 !important;
  padding: 8px 18px !important;
  height: 38px !important;
}

/* -- L. Conversation messages -- premium bubbles ------------ */
.message-user {
  background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,126,245,0.1)) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  align-self: flex-end !important;
  max-width: 75% !important;
  border-radius: 16px 16px 4px 16px !important;
  padding: 12px 16px !important;
}
.message-assistant {
  background: rgba(13,21,37,0.8) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  align-self: flex-start !important;
  max-width: 85% !important;
  border-radius: 4px 16px 16px 16px !important;
  padding: 12px 16px !important;
}

/* -- M. Notification drawer -- more premium ----------------- */
.notif-drawer {
  background: linear-gradient(135deg, rgba(8,14,28,0.98), rgba(13,21,37,0.98)) !important;
  border: 1px solid rgba(139,126,245,0.15) !important;
  border-radius: 14px !important;
  box-shadow:
    0 20px 60px rgba(0,0,0,0.6),
    0 0 0 1px rgba(255,255,255,0.04) inset !important;
  backdrop-filter: blur(24px) !important;
}
.nd-header {
  border-bottom: 1px solid rgba(255,255,255,0.05) !important;
  padding: 14px 16px !important;
}
.nd-title {
  font-weight: 700 !important;
  font-family: 'Manrope', sans-serif !important;
  font-size: 13px !important;
  color: var(--ink) !important;
}
.nd-clear-btn {
  font-size: 11px !important;
  color: var(--violet) !important;
  background: transparent !important;
  border: none !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
}
.nd-clear-btn:hover { opacity: 0.8; }
.notif-btn {
  position: relative;
  width: 36px; height: 36px;
  border-radius: 10px;
  background: rgba(139,126,245,0.07) !important;
  border: 1px solid rgba(139,126,245,0.12) !important;
  color: var(--ink-3) !important;
  display: grid; place-items: center;
  transition: all 0.2s !important;
}
.notif-btn:hover {
  background: rgba(139,126,245,0.14) !important;
  border-color: rgba(139,126,245,0.3) !important;
  color: var(--ink) !important;
}
.notif-count {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  box-shadow: 0 0 8px rgba(99,102,241,0.5) !important;
}

/* -- N. Case Context Bar -- elegant pipeline ---------------- */
.case-context-bar {
  background: linear-gradient(135deg, rgba(8,14,28,0.95), rgba(13,21,37,0.9)) !important;
  border-bottom: 1px solid rgba(139,126,245,0.1) !important;
  backdrop-filter: blur(20px) !important;
}
.ccb-pipe-step.done .ccb-pipe-n,
.ccb-pipe-step.active .ccb-pipe-n {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  color: #fff !important;
  box-shadow: 0 0 14px rgba(99,102,241,0.45) !important;
}
.ccb-pipe-fill {
  background: linear-gradient(90deg, #6366F1, #8B5CF6, #0DD6A8) !important;
}
.ccb-pipe-track {
  background: rgba(255,255,255,0.05) !important;
  border-radius: 2px !important;
}
.ccb-state-pill {
  font-size: 9px !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  padding: 3px 10px !important;
  border-radius: 20px !important;
  background: rgba(139,126,245,0.1) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  color: var(--violet) !important;
}
.ccb-new-btn {
  background: rgba(139,126,245,0.1) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  color: var(--violet) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  padding: 5px 12px !important;
}
.ccb-new-btn:hover {
  background: rgba(139,126,245,0.18) !important;
  border-color: rgba(139,126,245,0.4) !important;
}

/* -- O. Global input field styling -------------------------- */
input[type="text"]:not(#chat-input),
input[type="search"],
select,
textarea {
  background: rgba(13,21,37,0.8);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  color: var(--ink);
  padding: 10px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
  width: 100%;
}
input[type="text"]:not(#chat-input):focus,
input[type="search"]:focus,
select:focus,
textarea:focus {
  outline: none;
  border-color: rgba(139,126,245,0.45);
  box-shadow: 0 0 0 3px rgba(139,126,245,0.1);
}

/* -- P. Section headings -- more authoritative -------------- */
.section-heading h2 {
  font-family: 'Manrope', sans-serif !important;
  font-size: 26px !important;
  font-weight: 800 !important;
  background: linear-gradient(135deg, var(--ink) 0%, var(--ink-2) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.eyebrow {
  font-size: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  color: var(--violet) !important;
  text-transform: uppercase !important;
}

/* -- Q. Workflow strip -- more dramatic --------------------- */
.workflow-strip {
  background: linear-gradient(135deg, rgba(13,21,37,0.9), rgba(8,14,28,0.95)) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(20px) !important;
  padding: 16px 24px !important;
}
.workflow-step.active {
  background: rgba(139,126,245,0.1) !important;
  border-radius: 10px !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  padding: 8px 12px !important;
}
.workflow-step.active > span {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  color: white !important;
  box-shadow: 0 0 16px rgba(99,102,241,0.5) !important;
}

/* -- R. Page title -- gradient text ------------------------- */
#page-title {
  font-family: 'Manrope', sans-serif !important;
  font-size: clamp(36px, 4.2vw, 54px) !important;
  font-weight: 900 !important;
  line-height: 1.1 !important;
}
#page-title em {
  font-style: normal !important;
  background: linear-gradient(135deg, var(--violet), var(--mint)) !important;
  background-size: 200% auto !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}
.gradient-text {
  background: linear-gradient(135deg, #fff 40%, var(--violet) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* -- S. Hero tags -- pill redesign -------------------------- */
.hero-tag {
  background: rgba(13,21,37,0.8) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 20px !important;
  padding: 6px 14px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  backdrop-filter: blur(12px) !important;
}
.hero-tag:hover {
  background: rgba(139,126,245,0.14) !important;
  border-color: rgba(139,126,245,0.4) !important;
}

/* -- T. App footer -- richer -------------------------------- */
.app-footer {
  border-top: 1px solid rgba(139,126,245,0.08) !important;
  background: linear-gradient(90deg, rgba(139,126,245,0.03), transparent, rgba(13,214,168,0.02)) !important;
  padding: 20px 0 !important;
  margin-top: 32px !important;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.3px;
}

/* -- U. Scrollbar -- styled throughout ---------------------- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(5,8,18,0.8); }
::-webkit-scrollbar-thumb { background: rgba(139,126,245,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139,126,245,0.4); }

/* -- V. Consent checkbox -- premium ------------------------- */
.custom-check {
  width: 18px !important;
  height: 18px !important;
  border-radius: 5px !important;
  border: 2px solid rgba(139,126,245,0.3) !important;
  background: rgba(13,21,37,0.8) !important;
  flex-shrink: 0 !important;
  transition: all 0.2s !important;
  position: relative !important;
  display: inline-block;
  vertical-align: middle;
  cursor: pointer;
}
input[type="checkbox"]:checked ~ .custom-check,
input[type="checkbox"]:checked + .custom-check {
  background: linear-gradient(135deg, var(--violet), var(--violet-dark)) !important;
  border-color: var(--violet) !important;
  box-shadow: 0 0 10px rgba(139,126,245,0.3) !important;
}
.custom-check::after {
  content: '';
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -55%) rotate(45deg) scale(0);
  width: 5px; height: 9px;
  border: 2px solid #fff;
  border-top: none; border-left: none;
  transition: transform 0.18s ease;
}
input[type="checkbox"]:checked ~ .custom-check::after,
input[type="checkbox"]:checked + .custom-check::after {
  transform: translate(-50%, -55%) rotate(45deg) scale(1);
}

/* -- W. Loading overlay -- more impressive ------------------ */
.app-loading {
  background: linear-gradient(135deg, #050810 0%, #080D1E 50%, #04090F 100%) !important;
}
.loading-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.loading-logo {
  width: 52px !important;
  height: 52px !important;
  filter: drop-shadow(0 0 20px rgba(139,126,245,0.7));
  animation: loadingPulse 1.8s ease-in-out infinite !important;
}
@keyframes loadingPulse {
  0%,100% { filter: drop-shadow(0 0 16px rgba(139,126,245,0.6)); transform: scale(1); }
  50%      { filter: drop-shadow(0 0 32px rgba(13,214,168,0.7)); transform: scale(1.05); }
}
.loading-wordmark {
  font-family: 'Manrope', sans-serif !important;
  font-size: 22px !important;
  font-weight: 800 !important;
  letter-spacing: -0.5px !important;
  background: linear-gradient(135deg, #fff 30%, var(--violet)) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}
.loading-bar {
  width: 180px !important;
  height: 3px !important;
  background: rgba(255,255,255,0.06) !important;
  border-radius: 2px !important;
  overflow: hidden;
}
.loading-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--violet), var(--mint)) !important;
  border-radius: 2px !important;
  box-shadow: 0 0 8px rgba(139,126,245,0.6) !important;
}

/* -- X. Light theme -- comprehensive overrides -------------- */
[data-theme="light"] .topbar {
  background: rgba(250,251,255,0.97) !important;
  border-bottom: 1px solid rgba(60,90,180,0.12) !important;
  box-shadow: 0 2px 16px rgba(0,0,0,0.08) !important;
}
[data-theme="light"] .topbar-compliance {
  background: rgba(60,90,180,0.03) !important;
  border-bottom-color: rgba(60,90,180,0.08) !important;
}
[data-theme="light"] .card {
  background: linear-gradient(145deg, rgba(255,255,255,0.98), rgba(248,250,255,0.99)) !important;
  border-color: rgba(60,90,180,0.1) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07), 0 1px 0 rgba(255,255,255,0.9) inset !important;
}
[data-theme="light"] .button-primary {
  box-shadow: 0 4px 20px rgba(99,102,241,0.25), 0 1px 0 rgba(255,255,255,0.3) inset !important;
}
[data-theme="light"] .button-secondary {
  background: rgba(60,90,180,0.06) !important;
  border-color: rgba(60,90,180,0.2) !important;
  color: #2A3A5E !important;
}
[data-theme="light"] .button-secondary:hover:not(:disabled) {
  background: rgba(60,90,180,0.12) !important;
  border-color: rgba(60,90,180,0.4) !important;
  color: #1A2A4E !important;
}
[data-theme="light"] .hero-stats {
  background: linear-gradient(135deg, rgba(248,250,255,0.97), rgba(240,244,255,0.98)) !important;
  border-color: rgba(60,90,180,0.1) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
}
[data-theme="light"] .hstat-n, [data-theme="light"] .hstat-big {
  background: linear-gradient(135deg, #1a2a5e 30%, #6366F1) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}
[data-theme="light"] .ai-note {
  background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(13,214,168,0.03)) !important;
  border-color: rgba(99,102,241,0.2) !important;
  border-left-color: #6366F1 !important;
}
[data-theme="light"] .chat-input-row {
  background: rgba(248,250,255,0.95) !important;
  border-color: rgba(60,90,180,0.18) !important;
}
[data-theme="light"] .chat-input-row:focus-within {
  border-color: rgba(99,102,241,0.45) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}
[data-theme="light"] #chat-input {
  color: #1A2A4E !important;
}
[data-theme="light"] input[type="text"]:not(#chat-input),
[data-theme="light"] input[type="search"],
[data-theme="light"] select,
[data-theme="light"] textarea {
  background: rgba(248,250,255,0.95);
  border-color: rgba(60,90,180,0.16);
  color: #1A2A4E;
}
[data-theme="light"] input[type="text"]:not(#chat-input):focus,
[data-theme="light"] input[type="search"]:focus,
[data-theme="light"] select:focus,
[data-theme="light"] textarea:focus {
  border-color: rgba(99,102,241,0.45);
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
}
[data-theme="light"] .upload-zone {
  border-color: rgba(99,102,241,0.3) !important;
}
[data-theme="light"] .upload-zone:hover {
  border-color: rgba(99,102,241,0.6) !important;
  box-shadow: 0 0 24px rgba(99,102,241,0.1), inset 0 0 20px rgba(99,102,241,0.03) !important;
}
[data-theme="light"] .message-user {
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,126,245,0.07)) !important;
  border-color: rgba(99,102,241,0.2) !important;
}
[data-theme="light"] .message-assistant {
  background: rgba(248,250,255,0.97) !important;
  border-color: rgba(60,90,180,0.1) !important;
}
[data-theme="light"] .notif-drawer {
  background: linear-gradient(135deg, rgba(255,255,255,0.99), rgba(248,250,255,0.99)) !important;
  border-color: rgba(60,90,180,0.15) !important;
  box-shadow: 0 16px 50px rgba(0,0,0,0.15) !important;
}
[data-theme="light"] .locked-card {
  background: linear-gradient(135deg, rgba(240,169,75,0.04), rgba(255,255,255,0.97)) !important;
}
[data-theme="light"] .section-heading h2 {
  background: linear-gradient(135deg, #0D1525 0%, #3A4A6E 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}
[data-theme="light"] .journey-card {
  border-left-color: #6366F1 !important;
}
[data-theme="light"] .quote-card {
  background: linear-gradient(135deg, rgba(248,250,255,0.98), rgba(240,244,255,0.99)) !important;
  border-left-color: var(--mint) !important;
}
[data-theme="light"] .app-footer {
  background: linear-gradient(90deg, rgba(99,102,241,0.04), transparent, rgba(13,214,168,0.02)) !important;
  border-top-color: rgba(60,90,180,0.1) !important;
}
[data-theme="light"] ::-webkit-scrollbar-track { background: rgba(240,244,255,0.8); }
[data-theme="light"] ::-webkit-scrollbar-thumb { background: rgba(60,90,180,0.25); }
[data-theme="light"] ::-webkit-scrollbar-thumb:hover { background: rgba(60,90,180,0.45); }
[data-theme="light"] .workflow-step.active {
  background: rgba(99,102,241,0.08) !important;
  border-color: rgba(99,102,241,0.2) !important;
}
[data-theme="light"] .workflow-step.active > span {
  box-shadow: 0 0 16px rgba(99,102,241,0.4) !important;
}

/* -- Side cards base premium treatment ---------------------- */
.side-card {
  border: 1px solid rgba(255,255,255,0.06) !important;
  background: linear-gradient(145deg, rgba(13,21,37,0.9), rgba(8,14,28,0.95)) !important;
  backdrop-filter: blur(20px) !important;
  border-radius: 16px !important;
}
[data-theme="light"] .side-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.98), rgba(248,250,255,0.99)) !important;
  border-color: rgba(60,90,180,0.1) !important;
}

/* -- Intelligence rail -- more premium ---------------------- */
.intel-rail {
  background: linear-gradient(180deg, rgba(5,8,18,0.98), rgba(8,12,24,0.96)) !important;
  border-left: 1px solid rgba(139,126,245,0.12) !important;
  backdrop-filter: blur(24px) !important;
}
.ir-header {
  border-bottom: 1px solid rgba(139,126,245,0.1) !important;
  padding: 16px !important;
}
.ir-title {
  font-family: 'Manrope', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
}
.ir-label {
  font-size: 8.5px !important;
  letter-spacing: 1.6px !important;
  font-weight: 800 !important;
  color: var(--muted) !important;
}
.ir-stat-n {
  font-family: 'Manrope', sans-serif !important;
  font-weight: 800 !important;
  font-size: 20px !important;
  color: var(--ink) !important;
}
[data-theme="light"] .intel-rail {
  background: linear-gradient(180deg, rgba(252,253,255,0.98), rgba(248,250,255,0.97)) !important;
  border-left-color: rgba(60,90,180,0.12) !important;
}

/* -- Command palette -- more premium ------------------------ */
.cmd-palette {
  background: linear-gradient(135deg, rgba(8,14,28,0.99), rgba(13,21,37,0.98)) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  border-radius: 16px !important;
  box-shadow: 0 24px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04) inset !important;
  backdrop-filter: blur(32px) !important;
}
[data-theme="light"] .cmd-palette {
  background: linear-gradient(135deg, rgba(255,255,255,0.99), rgba(248,250,255,0.99)) !important;
  border-color: rgba(60,90,180,0.2) !important;
  box-shadow: 0 20px 60px rgba(0,0,0,0.18) !important;
}

/* -- Top progress bar -- more vivid ------------------------- */
.tpb { background: transparent !important; }
.tpb-fill {
  background: linear-gradient(90deg, #6366F1, #8B5CF6, #0DD6A8) !important;
  box-shadow: 0 0 12px rgba(139,126,245,0.6) !important;
}

/* -- Holo container refinements ----------------------------- */
.holo-container {
  border: 1px solid rgba(139,126,245,0.12) !important;
  border-radius: 20px !important;
  background: linear-gradient(135deg, rgba(8,14,28,0.97), rgba(13,21,37,0.95)) !important;
  box-shadow: 0 0 40px rgba(139,126,245,0.08) inset !important;
}

/* -- Card hover elevations ---------------------------------- */
.card:hover {
  box-shadow:
    0 1px 0 rgba(255,255,255,0.05) inset,
    0 28px 80px rgba(0,0,0,0.5),
    0 0 0 1px rgba(139,126,245,0.08) !important;
  border-color: rgba(255,255,255,0.09) !important;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.side-card:hover {
  box-shadow:
    0 1px 0 rgba(255,255,255,0.05) inset,
    0 16px 50px rgba(0,0,0,0.45),
    0 0 0 1px rgba(139,126,245,0.1) !important;
}

/* -- Consent line -- cleaner -------------------------------- */
.consent-line {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  line-height: 1.5;
  font-size: 13px;
  color: var(--ink-3);
  padding: 10px 0;
}
.consent-line input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0; height: 0;
  margin: 0; padding: 0;
}

/* -- Feature pill -- more premium --------------------------- */
.feature-pill {
  background: rgba(139,126,245,0.1) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  border-radius: 20px !important;
  padding: 4px 12px !important;
  font-size: 9px !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  color: var(--violet) !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  flex-shrink: 0 !important;
  white-space: nowrap !important;
}
.pulse-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--mint);
  display: inline-block;
  box-shadow: 0 0 6px rgba(13,214,168,0.7);
  animation: pulseDot 2s ease-in-out infinite;
}
@keyframes pulseDot {
  0%,100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.4); opacity: 0.7; }
}

/* -- Draft content area ------------------------------------- */
.draft-content {
  background: rgba(8,14,28,0.5) !important;
  border: 1px solid rgba(255,255,255,0.05) !important;
  border-radius: 10px !important;
  padding: 16px !important;
  margin-top: 12px !important;
  min-height: 80px;
}

/* -- Report tag -- live badge ------------------------------- */
.report-tag {
  font-size: 9px !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  padding: 4px 12px !important;
  border-radius: 20px !important;
  background: rgba(13,214,168,0.1) !important;
  border: 1px solid rgba(13,214,168,0.25) !important;
  color: var(--mint) !important;
  flex-shrink: 0;
  align-self: flex-start;
}

/* -- New case btn in sidebar -------------------------------- */
.new-case-btn {
  width: 20px; height: 20px;
  border-radius: 6px;
  background: rgba(139,126,245,0.15) !important;
  border: 1px solid rgba(139,126,245,0.25) !important;
  color: var(--violet) !important;
  font-size: 14px !important;
  line-height: 1 !important;
  display: inline-grid;
  place-items: center;
  padding: 0 !important;
  margin-left: auto;
}
.new-case-btn:hover {
  background: rgba(139,126,245,0.25) !important;
}

/* -- Sidebar labels -- more visible ------------------------- */
.workspace-label, .sidebar-label {
  color: rgba(139,126,245,0.45) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
}

/* -- Sidebar history badge ---------------------------------- */
.hist-badge {
  background: rgba(139,126,245,0.15) !important;
  color: var(--violet) !important;
  border: 1px solid rgba(139,126,245,0.2) !important;
  font-size: 9px !important;
  font-weight: 700 !important;
  padding: 1px 7px !important;
  border-radius: 10px !important;
}

/* ============================================================
   END DESIGN SYSTEM v3
   ============================================================ */
"""

with open(css_path, 'a', encoding='utf-8') as f:
    f.write(v3_block)

with open(css_path, 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.count('\n')
print(f"Done. File now has {lines} lines ({len(content)} chars)")
print("Last 5 lines:")
for line in content.splitlines()[-5:]:
    print(repr(line))
