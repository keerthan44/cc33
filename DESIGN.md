# Design Note

Architecture decisions, LLM strategy, failure handling, and trade-offs.

---

## What the system does

The user speaks. Whisper transcribes it locally. A GPT model classifies the transcript into one or more structured intents — create tasks, update a task, query tasks, or general note. The result is persisted and streamed back to the browser in real time.

The interesting problems are:
1. Getting reliable structured output from an LLM
2. Matching vague natural-language identifiers ("the doctor thing") to the right task
3. Streaming partial transcripts while recording is still in progress

---

## LLM strategy

### Structured output, not free text

Intent extraction uses LangChain's `with_structured_output` bound to a Pydantic schema:

```python
self._chain = prompt | llm.with_structured_output(ExtractedIntent)
```

This maps the Pydantic model to an OpenAI function-calling schema. The key detail is `ConfigDict(extra="forbid")` on every nested model — this produces `additionalProperties: false` in the JSON schema, which activates OpenAI's strict mode and guarantees the model cannot return fields outside the schema. Without it, the model can hallucinate extra keys that Pydantic would silently ignore.

```python
class ExtractedIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")   # → additionalProperties: false
    actions: list[IntentAction]                 # always a list, never a single value
```

The output is **always validated by Pydantic** before it reaches business logic. There is no string parsing, no JSON.loads, no regex.

### Multi-intent in one pass

The schema uses `actions: list[IntentAction]` rather than a single intent field. This means one LLM call handles *"schedule a dentist appointment and show me what's pending"* — returning a `CREATE_TASK` and a `QUERY_TASKS` action in the same response, processed independently.

### The system prompt

The prompt has four jobs:
1. Resolve relative dates to `YYYY-MM-DD` ("three years from now" → absolute date)
2. Classify each distinct intent into its own `IntentAction`
3. For `UPDATE_TASK_STATUS`: distinguish the disambiguator date (which task) from the new due date (what to change it to)
4. Extract task arrays — never merge two tasks into one

The prompt explicitly tells the model: *"If the task might not exist yet, still use UPDATE_TASK_STATUS — the backend will create it."* This keeps the LLM's job simple (classify intent, extract fields) and moves the upsert decision into the service layer where it belongs.

### Failure handling

Every intent extraction runs with up to 3 retries:

```python
for attempt in range(max_retries + 1):
    try:
        return await asyncio.to_thread(self._invoke, transcript)
    except Exception as exc:
        logger.error("attempt %d/%d failed: %s", ...)

return ExtractedIntent(actions=[IntentAction(intent=IntentType.GENERAL_NOTE)])
```

On total failure, the system falls back to `GENERAL_NOTE`. The transcript is **always saved** as a note, even if intent extraction fails completely. The user's speech is never lost.

---

## Semantic search for task matching

When a user says *"mark the doctor thing as done"*, the system needs to find the task titled *"Dentist appointment"*.

**At creation time:** The task's `title + description` is embedded with `text-embedding-3-small` and stored as a `vector(1536)` column in PostgreSQL via pgvector. The embedding is computed inline before the `INSERT`, so the task is always fully searchable by the time the response is returned.

**At update time:** The natural-language identifier ("the doctor thing") is embedded and compared via cosine distance:

```sql
SELECT * FROM tasks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> $1
LIMIT 3
```

If the user also supplies a disambiguating date ("the dentist appointment from last Tuesday"), results are filtered to that exact `due_date` to avoid wrong-task matches.

**Fallback chain:**
1. Semantic search (cosine similarity)
2. ILIKE title search (for tasks with no embedding yet — fresh DB or embedding failed)
3. Upsert — create the task if nothing matches

The upsert is important: *"postpone my gym session to next month"* should work even if the gym session task doesn't exist yet.

**Known risk:** semantic search can match the wrong task when titles are similar and no date disambiguator is provided. The mitigation is limiting results to top-3 and requiring a reasonably specific identifier. A user saying "the thing" will get whichever task is semantically closest. This can be improved by using different embedding models or fine tuning one. 

---

## Partial transcript streaming

### Why `b"".join(chunks)` is always valid WebM

The browser's `MediaRecorder` produces WebM. The first chunk it emits contains the **EBML header** — container metadata (codec, sample rate, channel layout). Every subsequent chunk is a raw audio cluster that cannot be decoded without the header. Because the header is always chunk 0 and chunks are accumulated in order, `b"".join(chunks)` is always a complete, decodable WebM file regardless of how many chunks have arrived. This is what makes mid-recording transcription possible.

### Partial transcription flow

On each new binary chunk the server appends it to the accumulator. If Whisper is idle it fires immediately; if Whisper is busy it sets a `pending` flag instead of dropping the chunk:

```python
chunks.append(chunk)
if not is_transcribing[0]:
    is_transcribing[0] = True
    asyncio.create_task(send_partial(b"".join(chunks)))
elif is_transcribing[0]:
    pending[0] = True   # new audio arrived; re-run when current call finishes
```

When Whisper finishes it checks `pending` and immediately re-runs against the latest accumulated snapshot:

```python
finally:
    is_transcribing[0] = False
    if pending[0] and not stop_received:
        pending[0] = False
        is_transcribing[0] = True
        asyncio.create_task(send_partial(b"".join(chunks)))
```

This is better than a pure skip (which freezes the partial transcript until the next chunk arrives 2 s later) and better than a full queue (which would process stale intermediate snapshots). At most one re-run is ever pending — and it always uses the freshest audio. `vad_filter=True` tells Whisper to skip silence so pauses don't produce empty partial results.

### Final transcription — same WebSocket, no second API call

When the user clicks stop, the client sends `{"type": "stop"}` as a text message over the same connection. The server handles it in the same receive loop:

```
binary chunk 0 (EBML header) ──► chunks=[c0]; Whisper(c0)        → partial
binary chunk 1               ──► chunks=[c0,c1]; Whisper(c0+c1)  → partial
binary chunk 2               ──► chunks=[c0,c1,c2]; (busy, skip)
{"type":"stop"}              ──► Whisper(c0+c1+c2, vad_filter=False) → final
                                 → GPT intent extraction
                                 → DB write
                                 ← {"type":"final"}, {"type":"actions"}, {"type":"done"}
                                 [break — WebSocket closes]
```

`vad_filter=False` on the final pass captures every word rather than trimming silence. After the `done` message is sent the loop breaks and the WebSocket closes naturally — there is no follow-up HTTP call. The `POST /api/voice/transcribe` REST endpoint is a completely separate path for uploading pre-recorded audio files.

---

## Known limitations

### LLM sometimes classifies UPDATE as CREATE because it cannot see the database

**The bug:** The LLM decides intent purely from the transcript — it has no visibility into what tasks actually exist. If the user says *"finish the report"* and a task called *"Write Q2 report"* exists, the LLM may classify this as `CREATE_TASK` (creating a duplicate) rather than `UPDATE_TASK_STATUS` (marking the existing one done). There is no signal in the transcript alone that tells the model whether a matching task is already there.

**Why the current design has this problem:** Intent classification and database lookup are two separate steps. The LLM runs first and commits to an intent; the semantic search only runs afterward if the intent is already `UPDATE_TASK_STATUS`. If the LLM guessed wrong, the search never happens.

**Ideal fix — tool calling with a score-gated confirmation loop:**

Give the LLM a `search_tasks` tool it can call before committing to an intent:

```python
tools = [
    {
        "name": "search_tasks",
        "description": "Search existing tasks by natural language query. "
                       "Call this before deciding UPDATE vs CREATE.",
        "parameters": {
            "query": {"type": "string", "description": "Natural language description of the task"}
        }
    }
]
```

The agent flow becomes:

```
User transcript
      │
      ▼
LLM thinks about intent
      │
      ├─ suspects UPDATE ──► calls search_tasks("finish the report")
      │                             │
      │                       DB returns top match +
      │                       cosine similarity score
      │                             │
      │                    score ≥ 0.85? ──► YES ──► UPDATE existing task
      │                             │
      │                            NO ──► CREATE new task
      │
      └─ clearly CREATE (no existing task implied) ──► CREATE directly
```

The similarity threshold (e.g. 0.85) is the key gate. A high score means the semantic match is confident enough to treat the utterance as an update; a low score means the user is describing something new. The threshold can be tuned on real utterances — lower catches more updates but risks false matches; higher is conservative but misses ambiguous references.

This turns intent extraction from a single-shot classification into a two-turn agentic loop: the LLM reasons, queries, then decides — with the database as a grounding source rather than pure language inference.