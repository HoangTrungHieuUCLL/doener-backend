# Doener Backend

FastAPI backend for Doener, a workout-tracking app (auth, workout plans, logged sessions, personal records, and stats).

This repository is standalone: it does not reference or share code with any frontend repo, and it is deployed independently.

## Tech stack

- Python 3.12, FastAPI
- SQLAlchemy 2.0 + SQLModel for models, Pydantic v2 for request/response schemas
- Alembic for migrations
- PostgreSQL in production; SQLite for the test suite
- JWT auth (access token only, no refresh token), passwords hashed with bcrypt via passlib

## Local development (docker compose)

1. Copy the example env file and adjust as needed:

   ```bash
   cp .env.example .env
   ```

2. Build and start the backend + a local Postgres instance:

   ```bash
   docker compose up --build
   ```

   The API is then available at `http://localhost:8000`. Migrations (including seeding the 22-exercise catalog) run automatically on container startup via `entrypoint.sh` (`alembic upgrade head && uvicorn ...`).

3. Interactive API docs: `http://localhost:8000/docs`.

## Running without Docker

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg://doener:doener@localhost:5432/doener"  # or a sqlite:/// URL for quick local hacking
export JWT_SECRET_KEY="some-local-secret"

alembic upgrade head   # creates tables + seeds the 22 exercises
uvicorn app.main:app --reload
```

## Running tests

The test suite runs entirely against an in-memory SQLite database (the DB session dependency is overridden in `tests/conftest.py`), so no Postgres instance or Docker is required:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Covers: signup/login flow, JWT rejection of missing/invalid tokens, `total_volume_kg` computation on session finish, personal-record upsert behavior (`is_new_pr` true on a new max, false otherwise), and the per-exercise recap served by `/stats/last-sets` (full set list, `exclude_session_id` filtering, trend ordering and cap, per-user isolation).

## Environment variables

| Variable             | Required | Default            | Notes                                                              |
| --------------------- | -------- | ------------------- | -------------------------------------------------------------------- |
| `DATABASE_URL`        | yes      | —                    | e.g. `postgresql+psycopg://user:pass@host:5432/dbname`               |
| `JWT_SECRET_KEY`      | yes (prod) | insecure dev fallback (logs a warning) | Secret used to sign JWTs                                              |
| `JWT_ALGORITHM`       | no       | `HS256`              |                                                                        |
| `JWT_EXPIRE_MINUTES`  | no       | `20160` (14 days)    | No refresh token, so the access token itself is long-lived            |
| `CORS_ORIGINS`        | no       | empty (no origins allowed) | Comma-separated list of allowed origins                        |
| `PORT`                | no       | `8000`               | The app binds `0.0.0.0:$PORT` (Railway convention)                    |

## Deployment

This service is deployed standalone on Railway with a Postgres add-on, wired purely through the `DATABASE_URL` and `CORS_ORIGINS` environment variables — there are no hardcoded URLs anywhere in the code. On deploy, the container's `CMD` runs `alembic upgrade head` before starting `uvicorn`, so migrations (schema + exercise seed data) apply automatically on every release.

## API

See the running service's `/docs` (Swagger UI) or `/redoc` for the full interactive API reference. Endpoints: `/auth/signup`, `/auth/login`, `/auth/me`, `/exercises`, `/plan`, `/sessions` (+ `/sessions/{id}/sets`, `/sessions/{id}/cardio`, `/sessions/{id}/finish`, `/sessions/{id}`), `/stats/prs`, `/stats/volume`, `/stats/last-sets`, `/stats/exercise/{id}/progress`, `/stats/consistency`, `/together`.
