# Graph Report - doener-backend  (2026-09-11)

## Corpus Check
- Corpus is ~4,555 words - fits in a single context window. You may not need a graph.

## Summary
- 195 nodes · 427 edges · 15 communities (8 shown, 2 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.94)
- Token cost: 73,545 input · 0 output

## Community Hubs (Navigation)
- Docs & Deployment
- Config & Database Setup
- Auth & Access Control
- Session & Workout Schemas
- Migrations & Plan Router
- Workout Sessions & Models
- Session Tests
- Stats Router
- Seed Exercises Migration
- Container Entrypoint

## God Nodes (most connected - your core abstractions)
1. `Doener Backend (FastAPI service)` - 30 edges
2. `User` - 26 edges
3. `get_current_user()` - 12 edges
4. `Exercise` - 11 edges
5. `get_session_detail()` - 11 edges
6. `get_session()` - 10 edges
7. `WorkoutSession` - 10 edges
8. `add_set()` - 10 edges
9. `signup()` - 9 edges
10. `login()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `python-dotenv==1.0.1` --conceptually_related_to--> `Doener Backend (FastAPI service)`  [INFERRED]
  requirements.txt → README.md
- `python-jose[cryptography]==3.3.0` --shares_data_with--> `JWT auth, access-token-only (no refresh token) — long-lived access token trade-off`  [INFERRED]
  requirements.txt → README.md
- `engine_fixture()` --uses--> `Exercise`  [INFERRED]
  tests/conftest.py → app/models.py
- `fastapi==0.115.0` --shares_data_with--> `FastAPI`  [INFERRED]
  requirements.txt → README.md
- `sqlalchemy==2.0.35` --shares_data_with--> `SQLAlchemy 2.0`  [INFERRED]
  requirements.txt → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **FastAPI backend tech stack (FastAPI, SQLAlchemy, SQLModel, Pydantic v2, Alembic)** — readme_fastapi, readme_sqlalchemy, readme_sqlmodel, readme_pydantic, readme_alembic [EXTRACTED 1.00]
- **Docker Compose local dev stack (postgres + backend + volume)** — docker_compose_postgres_service, docker_compose_backend_service, docker_compose_postgres_data_volume [EXTRACTED 1.00]
- **JWT authentication configuration (secret, algorithm, expiry, signing library)** — readme_jwt_auth, readme_jwt_secret_key_env, readme_jwt_algorithm_env, readme_jwt_expire_minutes_env, requirements_python_jose [INFERRED 0.85]

## Communities (15 total, 2 thin omitted)

### Community 0 - "Docs & Deployment"
Cohesion: 0.05
Nodes (48): docker-compose: backend service (build .), Postgres healthcheck (pg_isready) gates backend startup via depends_on condition, doener_postgres_data volume, docker-compose: postgres service (postgres:16), Alembic (migrations), /auth/signup, /auth/login, /auth/me endpoints, Password hashing: bcrypt via passlib, CORS_ORIGINS env var (+40 more)

### Community 1 - "Config & Database Setup"
Cohesion: 0.10
Nodes (19): get_settings(), Application configuration, read from environment variables., Settings, get_session(), Database engine/session setup. Portable across PostgreSQL (production) and…, FastAPI dependency yielding a DB session. Overridden in tests., health(), get (+11 more)

### Community 2 - "Auth & Access Control"
Cohesion: 0.14
Nodes (23): get_current_user(), Session, Shared FastAPI dependencies: DB session + current-user auth., login(), me(), get, post, Session (+15 more)

### Community 3 - "Session & Workout Schemas"
Cohesion: 0.20
Nodes (21): get_together(), get, Session, CardioDetail, CardioLogCreateRequest, CardioLogPublic, ExercisePublic, LastSessionSummary (+13 more)

### Community 4 - "Migrations & Plan Router"
Cohesion: 0.18
Nodes (14): CardioLog, PersonalRecord, PlannedDay, SQLModel table models. Kept deliberately portable (no Postgres-only column…, utcnow(), get_plan(), get, post (+6 more)

### Community 5 - "Workout Sessions & Models"
Cohesion: 0.38
Nodes (13): SessionSet, User, WorkoutSession, add_cardio(), add_set(), create_session(), finish_session(), _get_owned_session() (+5 more)

### Community 6 - "Session Tests"
Cohesion: 0.31
Nodes (6): _get_exercise_id(), test_add_set_to_finished_session_is_409(), test_finish_session_computes_total_volume_kg(), test_new_max_weight_sets_pr_flag_true(), test_non_max_weight_does_not_flag_pr(), test_set_number_increments_per_exercise()

### Community 7 - "Stats Router"
Cohesion: 0.48
Nodes (6): get_prs(), get_volume(), get, Session, PersonalRecordPublic, VolumePoint

## Knowledge Gaps
- **24 isolated node(s):** `entrypoint.sh script`, `Doener (workout-tracking app)`, `Python 3.12`, `/auth/signup, /auth/login, /auth/me endpoints`, `/exercises endpoint` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 72 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Workout Sessions & Models` to `Config & Database Setup`, `Auth & Access Control`, `Session & Workout Schemas`, `Migrations & Plan Router`, `Stats Router`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `get_current_user()` connect `Auth & Access Control` to `Config & Database Setup`, `Session & Workout Schemas`, `Migrations & Plan Router`, `Workout Sessions & Models`, `Stats Router`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `User` (e.g. with `get_current_user()` and `login()`) actually correct?**
  _`User` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `get_current_user()` (e.g. with `User` and `InvalidTokenError`) actually correct?**
  _`get_current_user()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `entrypoint.sh script`, `Doener (workout-tracking app)`, `Python 3.12` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Docs & Deployment` be split into smaller, more focused modules?**
  _Cohesion score 0.054078014184397165 - nodes in this community are weakly interconnected._
- **Should `Config & Database Setup` be split into smaller, more focused modules?**
  _Cohesion score 0.10052910052910052 - nodes in this community are weakly interconnected._