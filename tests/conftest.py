"""Pytest fixtures. Tests run against a fresh SQLite in-memory DB per test,
with the DB session dependency overridden — no Postgres needed."""
import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models import Exercise

# Seed rows mirroring alembic/versions/0002_seed_exercises.py (kept small
# here; only the fields the tests exercise matter).
_SEED_EXERCISES = [
    dict(
        key="a_goblet_squat",
        name="Goblet Squat",
        category="A",
        type="reps",
        sets=4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        per_side=False,
        equipment="free_weight",
    ),
    dict(
        key="a_forearm_plank",
        name="Forearm Plank",
        category="A",
        type="time",
        sets=3,
        duration_sec=30,
        rest_sec=90,
        per_side=False,
        equipment="bodyweight",
    ),
    dict(
        key="warmup_bar_hang",
        name="Bar Hang",
        category="warmup",
        type="time",
        sets=1,
        duration_sec=30,
        rest_sec=0,
        per_side=False,
        equipment=None,
    ),
]


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for row in _SEED_EXERCISES:
            session.add(Exercise(**row))
        session.commit()
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    def _make(username="alice", password="hunter2", display_name="Alice"):
        resp = client.post(
            "/auth/signup",
            json={"username": username, "password": password, "display_name": display_name},
        )
        assert resp.status_code == 201, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make
