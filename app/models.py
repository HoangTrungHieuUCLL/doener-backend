"""SQLModel table models. Kept deliberately portable (no Postgres-only
column types) so the exact same schema works against SQLite in tests."""
from datetime import date as date_, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False, index=True)
    password_hash: str
    display_name: str
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, nullable=False, index=True)
    name: str
    category: str  # "warmup" | "A" | "B" | "C"
    type: str  # "reps" | "time"
    sets: int
    reps: Optional[int] = None
    duration_sec: Optional[int] = None
    tempo: Optional[str] = None
    rest_sec: int
    per_side: bool = False
    equipment: Optional[str] = None  # "machine" | "free_weight" | "bodyweight" | "cable" | null


class PlannedDay(SQLModel, table=True):
    __tablename__ = "planned_days"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_planned_days_user_date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    date: date_ = Field(nullable=False, index=True)
    workout_key: str  # "A" | "B" | "C" | "cardio" | "rest" | "custom"


class WorkoutSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    date: date_ = Field(nullable=False, index=True)
    workout_key: str  # "A" | "B" | "C" | "cardio"
    started_at: datetime = Field(default_factory=utcnow, nullable=False)
    finished_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    total_volume_kg: Optional[float] = None


class SessionSet(SQLModel, table=True):
    __tablename__ = "session_sets"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", nullable=False, index=True)
    exercise_id: int = Field(foreign_key="exercises.id", nullable=False, index=True)
    set_number: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    duration_sec: Optional[int] = None


class CardioLog(SQLModel, table=True):
    __tablename__ = "cardio_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", nullable=False, index=True)
    duration_sec: int
    distance_km: float


class PersonalRecord(SQLModel, table=True):
    __tablename__ = "personal_records"
    __table_args__ = (
        UniqueConstraint("user_id", "exercise_id", name="uq_personal_records_user_exercise"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    exercise_id: int = Field(foreign_key="exercises.id", nullable=False, index=True)
    best_weight_kg: float
    achieved_at: datetime = Field(default_factory=utcnow, nullable=False)
