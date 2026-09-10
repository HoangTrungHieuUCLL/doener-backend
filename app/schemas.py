"""Pydantic v2 request/response schemas (kept separate from the SQLModel
table models in app.models)."""
from datetime import date as date_, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

WorkoutKey = Literal["A", "B", "C", "cardio", "rest", "custom"]
SessionWorkoutKey = Literal["A", "B", "C", "cardio"]


# ---------- auth ----------


class SignupRequest(BaseModel):
    username: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------- exercises ----------


class ExercisePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    category: str
    type: str
    sets: int
    reps: Optional[int] = None
    duration_sec: Optional[int] = None
    tempo: Optional[str] = None
    rest_sec: int
    per_side: bool
    equipment: Optional[str] = None


# ---------- plan ----------


class PlanUpsertRequest(BaseModel):
    date: date_
    workout_key: WorkoutKey


class PlannedDayPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_
    workout_key: str


# ---------- sessions ----------


class SessionCreateRequest(BaseModel):
    workout_key: SessionWorkoutKey


class SessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_
    workout_key: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    total_volume_kg: Optional[float] = None


class SessionSetCreateRequest(BaseModel):
    exercise_id: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    duration_sec: Optional[int] = None


class SessionSetPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    exercise_id: int
    set_number: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    duration_sec: Optional[int] = None
    is_new_pr: bool


class CardioLogCreateRequest(BaseModel):
    duration_sec: int
    distance_km: float


class CardioLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    duration_sec: int
    distance_km: float


class SessionSetDetail(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    set_number: int
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    duration_sec: Optional[int] = None


class CardioDetail(BaseModel):
    duration_sec: int
    distance_km: float


class SessionDetail(BaseModel):
    id: int
    date: date_
    workout_key: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    total_volume_kg: Optional[float] = None
    sets: list[SessionSetDetail] = Field(default_factory=list)
    cardio: Optional[CardioDetail] = None


class SessionListResponse(BaseModel):
    items: list[SessionPublic]
    total: int


# ---------- stats ----------


class PersonalRecordPublic(BaseModel):
    exercise_id: int
    exercise_name: str
    best_weight_kg: float
    achieved_at: datetime


class VolumePoint(BaseModel):
    session_id: int
    date: date_
    total_volume_kg: float


# ---------- together ----------


class TodayPlan(BaseModel):
    workout_key: str


class LastSessionSummary(BaseModel):
    id: int
    date: date_
    workout_key: str
    total_volume_kg: Optional[float] = None


class TogetherEntry(BaseModel):
    user_id: int
    username: str
    display_name: str
    today_plan: Optional[TodayPlan] = None
    today_status: Literal["done", "not_done"]
    last_session: Optional[LastSessionSummary] = None
    session_count: int
