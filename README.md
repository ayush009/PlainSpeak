# PlainSpeak — AI-Powered Care Intelligence

> **Bridging clinical expertise and everyday understanding — from the consultation room all the way home.**

PlainSpeak is a full-stack clinical AI platform that transforms discharge instructions into grounded, voice-accessible care guidance. It captures the consultation, combines it with the discharge document, and generates a clinician-approved care plan that patients and caregivers can ask questions about at home — in plain language, 24/7.

**Runs entirely with a free local AI (Ollama) — no API key required.**

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

The app ships with a built-in demo patient — **no Ollama or Claude required** to see it working:

1. Start the server: `python -m plainspeak.main`
2. Open [http://localhost:3001](http://localhost:3001)
3. Click **"Load Demo Patient"** in the sidebar

This loads **Emily Carter** — a post-cholecystectomy patient — with 14 consultation transcript segments and a fully approved 8-task care plan signed by Dr. Sarah Chen. You can immediately explore the Care @ Home chat, task tracking, and the full UI without any AI backend.

---

## Features

### Care @ Clinic — Doctor's Workspace

Three-step clinician workflow:

**Step 1 — Capture the Consultation**
- Live voice transcription via Reson8 WebSocket API with real-time waveform visualisation
- Upload a written transcript PDF — auto-parsed and split into speaker turns
- Manual line-by-line entry for offline environments
- Paste a full conversation and auto-detect speakers (Clinician / Patient)

**Step 2 — Add the Discharge Document**
- Upload a PDF discharge summary (max 10 MB)
- Automatic text extraction with passage-level indexing
- Patient name auto-detected from the document

**Step 3 — AI-Assisted Review & Approval**
- One-click draft generation (works with Claude or local Ollama)
- AI produces a plain-language summary + source-linked care checklist
- Clinician edits the draft: modify tasks, adjust timing, add/remove steps
- Clinician approval signs the version with their name — stored immutably
- Export approved plan as PDF, copy to clipboard, or read aloud (TTS)

### Care @ Home — Caregiver Experience

Unlocks only after a clinician approves the care plan:

- **Contextual Q&A chat** — answers grounded strictly in the approved plan with source citations
- **Suggested questions** — auto-generated from care task keywords (medications, diet, wound care, follow-up appointments)
- **Task confirmation** — caregivers mark tasks as done / in-progress / blocked
- **Unresolved question tracking** — questions the AI can't answer confidently are flagged for clinical follow-up

### Care Overview

- Full task checklist with timestamps and responsible parties
- Progress event log
- Complete audit trail of approvals

### UI Highlights

- **Enterprise dark health-tech design** — premium CSS design system
- **AI backend badge** — live topbar pill showing `Ollama · llama3.1` (amber) or `Claude · model` (green)
- **Top progress bar** — 2px gradient bar animated during every API call
- **Notification centre** — real-time alerts for state changes
- **Keyboard shortcuts** — `Ctrl+K` to focus chat, number keys for tab switching
- **Case context bar** — patient name, avatar, workflow pipeline always visible
- **PWA ready** — installable as a web app (manifest + favicon included)
- **Bilingual** — English / German UI switch

---

## AI Backends

### Ollama — Local, Free, No API Key (recommended for development)

```env
USE_OLLAMA=true
OLLAMA_MODEL=llama3.1
```

Runs entirely on your machine. No data leaves. Uses Ollama's OpenAI-compatible `/v1/chat/completions` endpoint.

**Setup:**
```bash
# 1. Install Ollama: https://ollama.ai
# 2. Pull a model
ollama pull llama3.1

# 3. Start Ollama (keep running in background)
ollama serve
```

**Recommended models:**

| Model | Size | Notes |
|---|---|---|
| `llama3.1` | ~5 GB | Best overall quality |
| `qwen2.5:7b` | ~5 GB | Excellent structured JSON output |
| `mistral:7b` | ~4 GB | Fast, reliable |
| `phi3.5:mini` | ~2 GB | Smallest, good for low-RAM machines |

### Anthropic Claude — Cloud (optional, for production)

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-opus-4-5
```

Get a key at [console.anthropic.com](https://console.anthropic.com). Leave blank to auto-use Ollama.

**Auto-selection:** if `ANTHROPIC_API_KEY` is empty, Ollama is used automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser (SPA)                     │
│  app.js · consultation.js · enhancements.js         │
│  styles.css (6500+ lines) · index.html (PWA)        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP JSON / WebSocket
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
                ┌─────┴──────┐
         ┌──────▼───┐  ┌─────▼──────┐
         │  Claude  │  │   Ollama   │
         │  (cloud) │  │  (local)   │
         └──────────┘  └────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| JSON files per case, no database | Zero infrastructure to run — works out of the box |
| Clinician approval gate | AI drafts are never shown directly to patients |
| Source-linked answers | Every chat response cites the specific passage it came from |
| Unresolved question tracking | Honest about what the AI doesn't know |
| Dual AI backend (Claude + Ollama) | No vendor lock-in; runs free locally |
| Tool-calling agent loop | Post-care Q&A uses up to 6 LLM turns with context + progress tools |
| Input revision guard | If documents change after approval, a fresh draft is required |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI (local)** | Ollama — llama3.1, qwen2.5, mistral, phi3.5 |
| **AI (cloud)** | Anthropic Claude API |
| **PDF parsing** | pypdf (text extraction + passage indexing) |
| **HTTP client** | httpx |
| **Config** | pydantic-settings (.env loading) |
| **Storage** | JSON files on disk (no database) |
| **Frontend** | Vanilla JS (ES2022), no framework |
| **CSS** | Custom design system (dark health-tech, 6500+ lines) |
| **Voice** | Reson8 WebSocket API + Web Audio API |
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
│   ├── voice.py             # Reson8 voice token relay
│   ├── ai/
│   │   ├── client.py        # ClaudeClient + OllamaClient (shared LLM Protocol)
│   │   ├── agent.py         # Post-care chat agent (tool-calling loop, max 6 turns)
│   │   ├── summary.py       # AI draft generation
│   │   ├── prompts.py       # System prompts + JSON output schemas
│   │   └── tools.py         # Agent tools: get_case_context, record_progress_update
│   └── static/
│       ├── index.html       # Single-page app shell (~1700 lines)
│       ├── styles.css       # Full design system (6500+ lines)
│       ├── app.js           # Core app logic, case management, rendering
│       ├── consultation.js  # Real-time consultation capture module
│       ├── enhancements.js  # PDF export, TTS, neural background, animations
│       ├── favicon.svg      # SVG chat-bubble favicon
│       └── manifest.json    # PWA manifest
├── Dockerfile               # Multi-stage production build (non-root, ~slim)
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
- [Ollama](https://ollama.ai) running locally (free, no API key)

### 1. Clone & install

```bash
git clone https://github.com/ayush009/PlainSpeak.git
cd PlainSpeak
uv sync
```

### 2. Start Ollama

```bash
ollama pull llama3.1
ollama serve
```

### 3. Configure

```bash
cp .env.example .env
# The defaults use Ollama — no edits needed to get started
```

### 4. Run

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

# With Claude API key
ANTHROPIC_API_KEY=sk-ant-... docker compose up
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
| `ANTHROPIC_API_KEY` | *(empty)* | Claude API key — leave blank to use Ollama |
| `ANTHROPIC_MODEL` | `claude-opus-4-5` | Claude model ID |
| `ANTHROPIC_EFFORT` | `medium` | Reasoning effort: `low` / `medium` / `high` / `max` |
| `USE_OLLAMA` | `true` | Force Ollama backend |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Local model to use |
| `RESON8_API_KEY` | *(empty)* | Voice transcription key (optional) |
| `PORT` | `3001` | HTTP server port |
| `HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for Docker/cloud) |
| `APP_ENV` | `development` | `development` or `production` |
| `CORS_ORIGINS` | `http://localhost:3001` | Comma-separated allowed origins |
| `PLAINSPEAK_DATA_DIR` | `data` | Directory for cases and uploads |

---

## Development

```bash
# Install with dev tools (pytest, ruff, fpdf2)
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

**Stack:** Python · FastAPI · Ollama · Anthropic Claude · Vanilla JS · Docker

**Author:** Ayush Juyal — M.Sc. Data Science | ML & NLP | [github.com/ayush009](https://github.com/ayush009)

---

*"Understanding care shouldn't end when the appointment does." — The PlainSpeak Principle*
