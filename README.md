# Voice Note Taker

AI-powered voice note-taking and task management. Speak a task, Whisper transcribes it, an OpenAI model extracts your intent via LangChain, and the system creates tasks automatically.

## Prerequisites

- Python 3.11+
- Node.js 20+
- ffmpeg (`brew install ffmpeg` / `apt install ffmpeg`)
- An OpenAI API key

## Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

> First request is slow — faster-whisper downloads the model (~150 MB for `base`) on first call.

## Frontend setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Generate a test audio file

```bash
python samples/generate_sample.py
```

## Sample curl

```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "file=@samples/sample.wav"
```

## Architecture

```
Backend layers:
  Controller (thin HTTP)
      ↓
  Service (business logic)
      ↓
  Repository (DB queries)
      ↓
  Model (SQLAlchemy ORM)

Frontend layers:
  Page
    ↓
  Components
    ↓
  Hooks
    ↓
  Services
    ↓
  lib (types + HTTP)
```

## Known limitations

- **First STT call is slow** — model loads on first call; subsequent calls are fast.
- **WebSocket streaming requires a local run** — hosted/serverless deployments should use `POST /api/voice/transcribe` instead.
- **SQLite only** — swap `DATABASE_URL` to a PostgreSQL async DSN for production.
- **LangChain provider swap** — to change from OpenAI to Anthropic, replace `ChatOpenAI` with `ChatAnthropic` in `backend/app/services/intent_service.py` and update the API key in `.env`.
