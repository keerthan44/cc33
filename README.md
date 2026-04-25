# Voice Note Taker

AI-powered voice note-taking and task management. Speak naturally — Whisper transcribes it, GPT extracts your intent, and the app creates tasks, updates statuses, or queries your list automatically.

> **Looking for architecture, LLM strategy, and trade-offs?** → [DESIGN.md](DESIGN.md)

---

## Quick start — ~5 minutes

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1 — Clone

```bash
git clone https://github.com/keerthan44/cc33.git
cd cc33
```

### 2 — Add your API key

`backend/.env.prod` only needs one change. Get this from .env.prod.example:

```bash
OPENAI_API_KEY=sk-...          # ← only thing you need to set
OPENAI_MODEL=gpt-5.4
WHISPER_MODEL_SIZE=tiny.en
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
CORS_ORIGINS=["http://localhost:3000"]
```

`frontend/.env.prod` is already configured and needs no changes. Get this from the .env.prod.example:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3 — Start

```bash
docker compose up --build
```

First build takes 3–5 minutes (Python deps, npm packages). Subsequent starts are fast.

| | URL |
|---|---|
| App | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

> **First STT call is slow** — faster-whisper downloads the Whisper model (~75 MB for `tiny.en`) on first use. All subsequent calls are fast.

### 4 — Use it

1. Open http://localhost:3000
2. Click the mic, allow microphone access
3. Speak a task, question, or note — partial transcript appears live
4. Click stop — intent detected, tasks created or shown

**Example phrases:**
- *"Add a dentist appointment for next Tuesday"*
- *"Mark the doctor thing as done"*
- *"What tasks do I have pending this week?"*
- *"Schedule a gym session tomorrow and show me what's due this week"*

---

## Test without a mic

```bash
# Health check
curl http://localhost:8000/api/health

# Create a task via text
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"raw_transcript": "remind me to call the dentist tomorrow", "source": "text"}'

# List tasks
curl http://localhost:8000/api/tasks

# Upload a wav file
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "file=@samples/sample.wav"
```

---

## Hot reload

Source is bind-mounted into both containers — backend Python and frontend TypeScript changes reload automatically with no rebuild.

---

## Stop / reset

```bash
docker compose down          # stop, keep DB data
docker compose down -v       # stop and wipe database
```

---

## Switching models

| Setting | Key in `backend/.env.prod` | Default |
|---|---|---|
| LLM | `OPENAI_MODEL` | `gpt-5.4` |
| Embeddings | `EMBEDDING_MODEL` | `text-embedding-3-small` |
| Whisper | `WHISPER_MODEL_SIZE` | `tiny.en` — use `base` or `small` for better accuracy |
