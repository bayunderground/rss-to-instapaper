# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

RSS-to-Instapaper: a minimal Flask app that runs on Google App Engine, triggered by a cron job every 30 minutes. It fetches configured RSS feeds and bookmarks new items to Instapaper. Single-user, single-purpose.

## Running Locally

```bash
# Use the existing .venv
source .venv/bin/activate

# Env vars are loaded from .env automatically via python-dotenv
python main.py          # starts Flask on :8080
python test.py          # smoke-tests Instapaper connection
```

The cron endpoint is `GET|POST /tasks/fetch`. The `X-Appengine-Cron: true` header check is skipped locally (only enforced when `GAE_APPLICATION` env var is set, i.e. on App Engine).

## Deploying

```bash
bash depl.sh
```

Loads env vars from `.env`, generates `app.yaml` from `app.template.yaml`, then runs `gcloud app deploy` for both the app and `cron.yaml`. Schedule is every 30 minutes, Europe/Amsterdam timezone.

## Architecture

**Entry points:**
- `main.py` — Flask routes: `GET /` (health check), `GET|POST /tasks/fetch` (cron handler)
- `job.py` — `run_job()` orchestrates the full fetch-and-push cycle

**Data flow:**
1. Cron calls `/tasks/fetch`
2. `run_job()` preloads all `ProcessedItem` rows into an in-memory dict keyed by `item_key`
3. All feeds are fetched first (so a broken feed doesn't interrupt the send loop)
4. For each item not yet processed: INSERT a `ProcessedItem` row with `attempted_at=now, processed_at=NULL`, then call the Instapaper Simple API
5. On success: set `processed_at`. On failure: rollback the `processed_at` mutation so the row stays pending and is retried after 2 hours

**Retry / idempotency:**
- `item_key` is the RSS item's guid, falling back to its link URL; unique constraint in DB prevents duplicates
- `attempted_at` set but `processed_at=NULL` means pending — retried after `STALE_PENDING_RETRY_AFTER_SECONDS` (default 2 h)
- Concurrent insert conflicts (`IntegrityError`) are handled by reloading the existing row and re-applying skip/retry logic
- Instapaper 400 "already saved" is treated as success; 5xx/429 are retried with exponential backoff (up to 4 attempts)
- Network errors from `requests` (`RequestException`) are not caught in `instapaper.py` — they propagate and abort the job; the cron will retry in 30 minutes

**Database:**
- `feeds` — RSS URLs with optional `title` and `regex_filter` (applied to item titles)
- `processed_items` — one row per feed item; `processed_at=NULL` = pending/failed, set = done
- Neon PostgreSQL (eu-central-1); schema reference in `db_schema.sql`
- `db.py` creates the SQLAlchemy engine with `pool_pre_ping=True` (needed because Neon drops idle connections). `session_scope()` in `db.py` is unused — `job.py` uses `SessionLocal()` as a context manager directly.

**Instapaper API:** Simple API (`POST https://www.instapaper.com/api/add`, HTTP Basic Auth) — not the OAuth Full API.

**Configuration** (`config.py`): all values from env vars — `DATABASE_URL`, `INSTAPAPER_USERNAME`, `INSTAPAPER_PASSWORD`; optional tuning vars documented in `config.py`.
