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

**At creation time:** The task's `title + description` is embedded with `text-embedding-3-small` and stored as a `vector(1536)` column in PostgreSQL via pgvector. This runs as a background `asyncio.Task` with its own DB session so it doesn't block the request.

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

**Known risk:** semantic search can match the wrong task when titles are similar and no date disambiguator is provided. The mitigation is limiting results to top-3 and requiring a reasonably specific identifier. A user saying "the thing" will get whichever task is semantically closest — this is an acceptable limitation for a personal tool.

---

## Partial transcript streaming

WebM audio is streamed as binary chunks over a WebSocket. Chunk 0 contains the EBML container header, so `b"".join(chunks)` is always valid WebM regardless of how many chunks have arrived. This means the accumulated audio can be transcribed at any point during recording.

On each new chunk, if no partial transcription is already running, one is fired in the background:

```python
task = asyncio.create_task(send_partial(b"".join(chunks)))
_background_tasks.add(task)           # prevent GC
task.add_done_callback(_background_tasks.discard)
```

The `_background_tasks` set is the key detail — Python's garbage collector can collect unreferenced `asyncio.Task` objects mid-execution. Storing a reference prevents silent task cancellation.

Partial transcription uses `vad_filter=True` (voice activity detection) to skip silence, reducing the noise of empty partial results during pauses.

---

## Why these tools

### faster-whisper over the OpenAI transcription API

Local inference means no per-request transcription cost and no network round-trip for audio. `faster-whisper` is ~4× faster than the original Whisper implementation at equal accuracy. `tiny.en` is the default — fast enough for real-time partials on CPU. `base` or `small` give meaningfully better accuracy for accents or technical vocabulary.

Trade-off: cold start on the first request (model load), and accuracy is lower than Whisper `large` or the hosted API.

### pgvector over a dedicated vector database

Semantic search lives in the same Postgres instance as the relational data — no external service to run, no sync to maintain, no separate connection pool. For a personal task manager this is the right call. The HNSW index (`vector_cosine_ops`) makes search fast enough at any realistic task count.

Trade-off: dedicated vector databases (Pinecone, Weaviate) offer higher throughput at scale, filtered vector search, and metadata indexing. None of that matters here.

### LangChain's `with_structured_output` over raw OpenAI SDK

The raw SDK requires manually writing the JSON schema for `response_format` or `tools`. LangChain derives it automatically from the Pydantic model, which means the schema and the Python types are always in sync. Changing a field in `IntentAction` updates both the validation and the LLM constraint automatically.

Trade-off: LangChain adds a dependency and occasionally changes its API. The abstraction is worth it for the structured output guarantee.

### WebSockets over polling or SSE

The client needs to send binary audio and receive multiple ordered events (partial, final, intent, tasks, done) over the same connection. SSE is unidirectional; polling adds latency and complexity. WebSockets are the right primitive.

Trade-off: WebSockets are stateful and harder to scale horizontally behind a load balancer (requires sticky sessions or shared state). For a single-instance personal tool this is irrelevant.

### asyncio background tasks for embeddings

Embedding computation happens after the task is created and the response is returned to the user. It runs as a fire-and-forget `asyncio.Task` with its own DB session. This keeps the request latency low — the user doesn't wait for the embedding API call.

Trade-off: if the server restarts before the background task completes, the embedding is lost. The ILIKE fallback in semantic search means the task is still findable; it just won't match natural-language queries until the embedding is backfilled on the next update.

---

## What would change at scale

| Concern | Current approach | At scale |
|---|---|---|
| Embedding backfill | Fire-and-forget asyncio task | Persistent job queue (Celery, ARQ) |
| WebSocket scaling | Single uvicorn process | Sticky sessions or Redis pub/sub |
| Vector search | Exact scan + HNSW | Dedicated vector DB with filtered search |
| STT | Local Whisper | Hosted API or GPU inference server |
| Multi-tenancy | None | Per-user task isolation, auth layer |
