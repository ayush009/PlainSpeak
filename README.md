# PlainSpeak — AI-Powered Care Intelligence

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ayush009/PlainSpeak)

> **Bridging clinical expertise and everyday understanding — from the consultation room all the way home.**

PlainSpeak is a full-stack clinical AI platform that transforms discharge instructions into grounded, voice-accessible care guidance. It captures the consultation, combines it with the discharge document, and generates a clinician-approved care plan that patients and caregivers can ask questions about at home — in plain language, 24/7.

**Multiple free AI backends supported — GPT-4o via TU Braunschweig KI-Toolbox, Gemini, Groq, Ollama, and more.**

---

## The Problem It Solves

Patients leave hospital with dense discharge documents they don't fully understand. Research shows **40–80% of medical information is forgotten immediately** after a clinical appointment. PlainSpeak closes this gap:

| Without PlainSpeak | With PlainSpeak |
|---|---|
| Patient reads a 6-page PDF alone | Consultation + document unified into one approved plan |
| "Take medication as directed" | "Take paracetamol 1000mg every 6 hours, max 4x/day, with food" |
| No way to ask follow-up questions | Live AI chat grounded strictly in the approved care plan |
| Clinician has no visibility post-discharge | Unresolved questions flagged back to the care team |

---

## Live Demo (no API key needed)

The app ships with a built-in demo patient — **no AI backend required** to explore the full UI:

1. Start the server: `python -m plainspeak.main`
2. Open [http://localhost:3001](http://localhost:3001)
3. Click **"Load Demo Patient"** in the sidebar

This loads **Emily Carter** — a post-cholecystectomy patient — with 14 consultation transcript segments and a fully approved 8-task care plan signed by Dr. Sarah Chen. You can immediately explore the Care @ Home chat, task tracking, and the full UI without any AI backend.

---

## Features

### Care @ Clinic — Doctor's Workspace

Three-step clinician workflow:

**Step 1 — Capture the Consultation**
- **Live voice transcription** via browser Web Speech API — no API key or server needed; works in Chrome, Edge, and Safari
- Speaker toggle during recording (Clinician / Patient) so each captured line gets the correct role
- Upload a written transcript PDF — auto-parsed and split into speaker turns
- Manual line-by-line entry for offline environments
- Paste a full conversation and auto-detect speakers (Clinician / Patient)

**Step 2 — Add the Discharge Document**
- Upload a PDF discharge summary (max 10 MB)
- Automatic text extraction with passage-level indexing
- Patient name auto-detected from the document

**Step 3 — AI-Assisted Review & Approval**
- One-click draft generation (Claude, GPT-4o via TUBS, Gemini, Groq, or Ollama)
- AI produces a plain-language summary + source-linked care checklist
- Clinician edits the draft: modify tasks, adjust timing, add/remove steps
- Clinician approval signs the version with their name — stored immutably
- Export approved plan as PDF, copy to clipboard, or read aloud (TTS)

### Care @ Home — Caregiver Experience

Unlocks only after a clinician approves the care plan:

- **Contextual Q&A chat** — answers grounded strictly in the approved plan with source citations
- **Voice input** — tap "Start speaking" to ask questions hands-free; the AI reply is automatically read aloud so the whole interaction is voice-driven
- **Suggested questions** — auto-generated from care task keywords (medications, diet, wound care, follow-up appointments)
- **Task confirmation** — caregivers mark tasks as done / in-progress / blocked
- **Unresolved question tracking** — questions the AI can't answer confidently are flagged for clinical follow-up

### Care Overview

- Full task checklist with timestamps and responsible parties
- Progress event log
- Complete audit trail of approvals

### UI Highlights

- **Enterprise dark health-tech design** — premium CSS design system
- **AI backend badge** — live topbar pill showing `GPT-4o · TUBS`, `Gemini · flash`, `Groq · llama-3.3-70b`, etc.
- **Top progress bar** — 2px gradient bar animated during every API call
- **Notification centre** — real-time alerts for state changes
- **Keyboard shortcuts** — `Ctrl+K` to focus chat, number keys for tab switching
- **Case context bar** — patient name, avatar, workflow pipeline always visible
- **PWA ready** — installable as a web app (manifest + favicon included)
- **Bilingual** — English / German UI switch

---

## AI Backends

Backends are tried in this priority order. Set the first key that applies and the rest are ignored.

### 1. TU Braunschweig KI-Toolbox — GPT-4o (recommended for TUBS students)

Free GPT-4o access for TU Braunschweig students via the university AI portal.

```env
TUBS_API_KEY=your-tubs-token
TUBS_MODEL=gpt-4o
```

**Setup:** Log in at [ki-toolbox.tu-braunschweig.de](https://ki-toolbox.tu-braunschweig.de), copy your API token from the portal, and set `TUBS_API_KEY`.

The topbar badge shows **GPT-4o · TUBS** in violet when active.

---

### 2. Gemini — Google AI Studio (1 500 req/day free)

```env
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.0-flash
```

**Setup:** Create a free key at [aistudio.google.com](https://aistudio.google.com). No credit card required.

---

### 3. Groq — Free Cloud Inference

Fast, free inference via Groq Cloud. Good fallback when other keys aren't available.

```env
GROQ_API_KEY=gsk_your-key-here
GROQ_MODEL=llama-3.3-70b-versatile
```

**Setup:** Sign up free at [console.groq.com](https://console.groq.com).

| Model | Notes |
|---|---|
| `llama-3.3-70b-versatile` | Best quality (default) |
| `llama-3.1-8b-instant` | Fastest response time |

---

### 4. OpenRouter — Free Fallback

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct:free
```

---

### 5. Ollama — Local, No API Key (recommended for development)

```env
# No key needed — Ollama runs locally
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.1
ollama serve
```

| Model | Size | Notes |
|---|---|---|
| `llama3.1` | ~5 GB | Best overall quality |
| `qwen2.5:7b` | ~5 GB | Excellent structured JSON output |
| `mistral:7b` | ~4 GB | Fast, reliable |
| `phi3.5:mini` | ~2 GB | Smallest, good for low-RAM machines |

---

### 6. Anthropic Claude — Cloud

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Claude is the only backend that supports the full tool-calling agent loop for post-care chat. All other backends use a single-turn direct path that is faster and equally accurate for this use case.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (SPA)                     │
│  app.js · consultation.js · enhancements.js         │
│  styles.css · index.html (PWA)                      │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP JSON
┌──────────────────────▼──────────────────────────────┐
│               FastAPI + Uvicorn                     │
│  api.py — REST endpoints (/api/*)                   │
│  main.py — app factory, CORS, security headers      │
└────┬─────────────────┬───────────────┬──────────────┘
     │                 │               │
┌────▼────┐    ┌───────▼──────┐  ┌────▼────────┐
│ Storage │    │  AI Layer    │  │  PDF / TXT  │
│ JSON on │    │ client.py    │  │ pdf_extract │
│  disk   │    │ agent.py     │  │ transcript_ │
│(no DB)  │    │ summary.py   │  │ import.py   │
└─────────┘    │ prompts.py   │  └─────────────┘
               └──────┬───────┘
        ┌─────────────┼──────────────┐
  ┌─────▼───┐  ┌──────▼──────┐  ┌───▼──────┐
  │  TUBS   │  │   Gemini    │  │  Groq /  │
  │ GPT-4o  │  │  (Google)   │  │  Ollama  │
  └─────────┘  └─────────────┘  └──────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| JSON files per case, no database | Zero infrastructure to run — works out of the box |
| Clinician approval gate | AI drafts are never shown directly to patients |
| Source-linked answers | Every chat response cites the specific passage it came from |
| Unresolved question tracking | Honest about what the AI doesn't know |
| Multi-backend AI chain | TUBS → Gemini → Groq → OpenRouter → Ollama → Claude; no vendor lock-in |
| Direct single-turn path for non-Claude | Removes tool-calling confusion on models that don't support it; faster responses |
| Browser Web Speech API for voice | No API key, no WebSocket server — works in any HTTPS context |
| Auto-speak AI replies after voice input | Fully hands-free loop: speak → AI answers → AI speaks back |
| Input revision guard | If documents change after approval, a fresh draft is required |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI (free cloud)** | GPT-4o via TUBS, Gemini (Google), Groq, OpenRouter |
| **AI (local)** | Ollama — llama3.1, qwen2.5, mistral, phi3.5 |
| **AI (cloud)** | Anthropic Claude API |
| **PDF parsing** | pypdf (text extraction + passage indexing) |
| **HTTP client** | httpx |
| **Config** | pydantic-settings (.env loading) |
| **Storage** | JSON files on disk (no database) |
| **Frontend** | Vanilla JS (ES2022), no framework |
| **CSS** | Custom design system (dark health-tech) |
| **Voice (consultation)** | Browser Web Speech API — continuous capture with speaker toggle |
| **Voice (chat)** | Browser Web Speech API (input) + SpeechSynthesis (output) |
| **Container** | Docker multi-stage build |
| **Package manager** | uv |

---

## Project Structure

```
PlainSpeak/
├── src/plainspeak/
│   ├── main.py              # App factory, CORS, security headers, server entry
│   ├── api.py               # All REST endpoints including /demo/seed and /info
│   ├── config.py            # Settings loaded from .env
│   ├── contracts.py         # Pydantic data models (Case, CareTask, Message…)
│   ├── storage.py           # JSON case store + file management
│   ├── pdf_extract.py       # PDF text extraction + patient name detection
│   ├── transcript_import.py # Transcript PDF parsing + speaker auto-detection
│   ├── ai/
│   │   ├── client.py        # TUBSClient, GeminiClient, GroqClient, OllamaClient, ClaudeClient
│   │   ├── agent.py         # Post-care chat agent (tool loop for Claude; direct path for others)
│   │   ├── summary.py       # AI draft generation
│   │   ├── prompts.py       # System prompts + JSON output schemas
│   │   └── tools.py         # Agent tools: get_case_context, record_progress_update
│   └── static/
│       ├── index.html       # Single-page app shell
│       ├── styles.css       # Full design system (dark health-tech)
│       ├── app.js           # Core app logic, case management, rendering, voice input/output
│       ├── consultation.js  # Live consultation capture (Web Speech API + speaker toggle)
│       ├── enhancements.js  # PDF export, TTS (SpeechSynthesis), animations
│       ├── favicon.svg      # SVG chat-bubble favicon
│       └── manifest.json    # PWA manifest
├── Dockerfile               # Multi-stage production build (non-root, slim)
├── docker-compose.yml       # Container orchestration with data volume
├── pyproject.toml           # Python dependencies + build config (uv)
├── .env.example             # Configuration reference (copy to .env)
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — fast Python package manager

### 1. Clone & install

```bash
git clone https://github.com/ayush009/PlainSpeak.git
cd PlainSpeak
uv sync
```

### 2. Configure

```bash
cp .env.example .env
# Set at least one AI key (TUBS_API_KEY, GEMINI_API_KEY, GROQ_API_KEY…)
# Or install Ollama locally and leave all cloud keys empty
```

### 3. Run

```bash
python -m plainspeak.main
# or
uv run plainspeak
```

Open [http://localhost:3001](http://localhost:3001) and click **"Load Demo Patient"** to see a fully populated example immediately.

---

## Docker Deployment

```bash
# Build and start
docker compose up

# With a free Groq key
GROQ_API_KEY=gsk_... docker compose up
```

App is available at [http://localhost:8080](http://localhost:8080)

**What the Docker image does:**
- Multi-stage build (builder → slim runtime) — minimal image size
- Runs as non-root user (`plainspeak` UID 1001)
- Persists case data in `/data` volume across restarts
- Built-in healthcheck on `/api/health`
- Exposes port 8080

---

## API Reference

Full interactive docs at [http://localhost:3001/api/docs](http://localhost:3001/api/docs) (dev mode)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/info` | Active AI backend + model name |
| `GET` | `/api/cases` | List all cases |
| `POST` | `/api/cases` | Create / reset a case |
| `GET` | `/api/cases/{id}` | Get full case + checklist |
| `POST` | `/api/cases/{id}/document` | Upload discharge PDF |
| `POST` | `/api/cases/{id}/transcript` | Save transcript segments |
| `POST` | `/api/cases/{id}/transcript/document` | Import transcript PDF |
| `POST` | `/api/cases/{id}/transcript/clear` | Clear transcript |
| `POST` | `/api/cases/{id}/summary` | Generate AI draft |
| `POST` | `/api/cases/{id}/approve` | Clinician approval (immutable) |
| `POST` | `/api/cases/{id}/chat` | Post-care caregiver Q&A |
| `POST` | `/api/cases/{id}/updates/{uid}/confirm` | Confirm progress update |
| `POST` | `/api/cases/{id}/updates/{uid}/reject` | Reject progress update |
| `POST` | `/api/demo/seed` | Load built-in demo patient (no AI needed) |

---

## Workflow States

```
awaiting_review  →  approved  →  post_care_active
```

| State | Meaning |
|---|---|
| `awaiting_review` | Inputs captured; awaiting clinician approval |
| `approved` | Clinician signed off; caregiver view unlocked |
| `post_care_active` | First caregiver question asked; active session |

---

## Safety & Trust Design

- **Clinician approval gate** — no care instructions reach caregivers without a named clinician signing off
- **Source citations** — every AI answer references the exact passage it is based on
- **Immutable audit trail** — approved versions are never overwritten; all versions preserved
- **Unresolved question tracking** — AI flags questions it can't answer confidently for clinical follow-up
- **Input revision guard** — if documents change after approval, re-generation is required before re-approval
- **AI is honest** — the system never fabricates; uncertainty is made explicit in the response

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TUBS_API_KEY` | *(empty)* | TU Braunschweig KI-Toolbox token (GPT-4o, free for TUBS students) |
| `TUBS_MODEL` | `gpt-4o` | Model served by TUBS portal |
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio key (Gemini, 1 500 req/day free) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model ID |
| `GROQ_API_KEY` | *(empty)* | Groq Cloud key (free tier) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model ID |
| `OPENROUTER_API_KEY` | *(empty)* | OpenRouter key (free models available) |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.1-70b-instruct:free` | OpenRouter model ID |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Local Ollama model |
| `ANTHROPIC_API_KEY` | *(empty)* | Claude API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Claude model ID |
| `PORT` | `3001` | HTTP server port |
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for Docker/cloud) |
| `APP_ENV` | `development` | `development` or `production` |
| `CORS_ORIGINS` | `http://localhost:3001` | Comma-separated allowed origins |
| `PLAINSPEAK_DATA_DIR` | `data` | Directory for cases and uploads |

---

## Development

```bash
# Install with dev tools (pytest, ruff)
uv sync --group dev

# Run tests
uv run pytest

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

---

## About

Built as a demonstration of how AI can be safely deployed in healthcare — not to replace clinicians, but to extend the care they provide beyond the appointment.

**Stack:** Python · FastAPI · GPT-4o / Gemini / Groq / Ollama · Anthropic Claude · Vanilla JS · Docker

**Author:** Ayush Juyal — M.Sc. Data Science | ML & NLP | [github.com/ayush009](https://github.com/ayush009)

---

*"Understanding care shouldn't end when the appointment does." — The PlainSpeak Principle*
