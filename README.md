# TaskForge

Async image-processing platform with priority queues, retry handling, dead-letter recovery,
and idempotent task execution — built on FastAPI, Celery, Redis, and PostgreSQL.

## Why this exists

A generic task-queue tutorial doesn't force real engineering decisions. TaskForge processes
actual uploaded images end-to-end, which means priority lanes, retries, and dead-letter handling
all have a genuine reason to exist instead of being bolted-on demo features.

## Architecture

Client → Nginx → FastAPI → Redis (broker) → Celery Workers → PostgreSQL (job records) + Storage

↑

high_priority queue → worker_high (dedicated)

low_priority queue  → worker_low  (shared with high_priority)

The two-worker-pool split is the core design decision in this project: `worker_high` listens
**only** to `high_priority`, so a high-priority job can never get stuck behind a backlog of
low-priority work, regardless of how deep that backlog gets. `worker_low` listens to both queues,
so idle capacity still gets used — but it always prefers high-priority work when both are waiting.

## Tech stack

| Layer | Choice |
|---|---|
| API Framework | FastAPI |
| Task Queue | Celery |
| Broker | Redis |
| Result store | PostgreSQL (survives restarts — not Redis-only) |
| Image processing | Pillow |
| Monitoring | Flower |
| Frontend | React (Vite) |
| Reverse proxy | Nginx |
| Containerization | Docker / Docker Compose |

## Core design decisions

- **Priority lanes are real Celery queues, not a decorative field.** `priority` on a job
  routes it to `app.tasks.process_image_high` or `app.tasks.process_image_low`, each bound to a
  separate queue, consumed by separate worker pools.
- **Retries distinguish transient vs. permanent failures.** Transient errors (e.g. a flaky
  storage write) retry with exponential backoff (1s → 2s → 4s) up to a per-job `max_retries`.
  Permanent errors (e.g. a corrupted image Pillow can't open) skip retries entirely and go
  straight to dead-letter — retrying an unprocessable file three times wastes time without
  ever succeeding.
- **Dead-letter jobs are never silently dropped.** Both exhausted-retry and permanent failures
  land in `DEAD_LETTER` status, visible via `GET /admin/dead-letter`, with a manual requeue
  endpoint for cases where the underlying issue gets fixed after the fact.
- **Idempotency guards against Celery's at-least-once delivery.** Before processing, a job is
  atomically claimed via `UPDATE ... WHERE status = 'queued'` — only one delivery of a message
  can ever win that update, closing the race condition a simple read-then-write check would miss.
  A duplicate delivery for an already-completed job is detected and skipped entirely.

## API endpoints

POST   /jobs                          — upload a file, returns job_id + status=queued

GET    /jobs/{id}                     — current status, retry_count, error message

GET    /jobs/{id}/result              — download the processed file (only if completed)

GET    /jobs?status=queued            — list jobs, optionally filtered by status

GET    /admin/dead-letter             — list permanently failed jobs

POST   /admin/dead-letter/{id}/retry  — manually requeue a dead-lettered job

## Running locally

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| API (via Nginx) | http://localhost |
| API (direct, for debugging) | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |
| React dashboard | http://localhost:5173 (run `npm run dev` inside `frontend/`) |
| Flower (queue/worker monitoring) | http://localhost:5555 |

## Screenshots

**Flower — two distinct worker pools, two distinct queues:**
*(insert `flower-dashboard.png` here)*

**Dashboard — jobs split into priority lanes:**
*(insert `dashboard-lanes.png` here)*

**Dead-letter admin view with manual retry:**
*(insert `dead-letter-admin.png` here)*

## License

MIT