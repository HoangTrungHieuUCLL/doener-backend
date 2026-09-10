from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models import Exercise, PersonalRecord, User, WorkoutSession
from app.schemas import PersonalRecordPublic, VolumePoint

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/prs", response_model=list[PersonalRecordPublic])
def get_prs(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    rows = session.exec(
        select(PersonalRecord, Exercise)
        .join(Exercise, PersonalRecord.exercise_id == Exercise.id)
        .where(PersonalRecord.user_id == current_user.id)
        .order_by(Exercise.name)
    ).all()
    return [
        PersonalRecordPublic(
            exercise_id=pr.exercise_id,
            exercise_name=exercise.name,
            best_weight_kg=pr.best_weight_kg,
            achieved_at=pr.achieved_at,
        )
        for pr, exercise in rows
    ]


@router.get("/volume", response_model=list[VolumePoint])
def get_volume(
    limit: int = Query(default=10, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Last N finished sessions, newest first, then reverse to oldest-to-newest.
    rows = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
        .where(WorkoutSession.finished_at.is_not(None))
        .where(WorkoutSession.total_volume_kg.is_not(None))
        .order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc())
        .limit(limit)
    ).all()
    rows.reverse()
    return [
        VolumePoint(session_id=s.id, date=s.date, total_volume_kg=s.total_volume_kg) for s in rows
    ]
