"""Database engine/session setup.

Portable across PostgreSQL (production) and SQLite (tests): we avoid any
Postgres-only column types in the models so the same schema works on both.
"""
from sqlmodel import Session, create_engine

from app.config import settings


def _make_engine():
    url = settings.DATABASE_URL
    connect_args = {}
    if url.startswith("sqlite"):
        # Needed for SQLite when used with FastAPI's threaded test client.
        connect_args = {"check_same_thread": False}
    return create_engine(url, echo=False, connect_args=connect_args)


engine = _make_engine()


def get_session():
    """FastAPI dependency yielding a DB session. Overridden in tests."""
    with Session(engine) as session:
        yield session
