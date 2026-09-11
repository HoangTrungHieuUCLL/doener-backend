from datetime import date as date_

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models import Exercise, PersonalRecord, PlannedDay, SessionSet, User, WorkoutSession
from app.schemas import (
    ConsistencyDay,
    ExerciseProgressPoint,
    LastSetPublic,
    PersonalRecordPublic,
    VolumePoint,
)

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
        VolumePoint(
            session_id=s.id,
            date=s.date,
            total_volume_kg=s.total_volume_kg,
            workout_key=s.workout_key,
        )
        for s in rows
    ]


@router.get("/last-sets", response_model=list[LastSetPublic])
def get_last_sets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # One row per exercise: the most recently logged set for that exercise,
    # across all of the user's sessions (any session, not just the latest).
    rows = session.exec(
        select(SessionSet, WorkoutSession)
        .join(WorkoutSession, SessionSet.session_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == current_user.id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc(), SessionSet.id.desc())
    ).all()
    latest: dict[int, SessionSet] = {}
    for set_row, _ in rows:
        latest.setdefault(set_row.exercise_id, set_row)
    return [
        LastSetPublic(
            exercise_id=exercise_id,
            weight_kg=s.weight_kg,
            reps=s.reps,
            duration_sec=s.duration_sec,
        )
        for exercise_id, s in latest.items()
    ]


@router.get("/exercise/{exercise_id}/progress", response_model=list[ExerciseProgressPoint])
def get_exercise_progress(
    exercise_id: int,
    limit: int = Query(default=30, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    rows = session.exec(
        select(SessionSet, WorkoutSession)
        .join(WorkoutSession, SessionSet.session_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == current_user.id)
        .where(SessionSet.exercise_id == exercise_id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc())
        .limit(limit)
    ).all()
    rows.reverse()
    return [
        ExerciseProgressPoint(
            session_id=ws.id, date=ws.date, weight_kg=s.weight_kg, reps=s.reps
        )
        for s, ws in rows
    ]


@router.get("/consistency", response_model=list[ConsistencyDay])
def get_consistency(
    from_: date_ = Query(alias="from"),
    to: date_ = Query(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    planned = session.exec(
        select(PlannedDay)
        .where(PlannedDay.user_id == current_user.id)
        .where(PlannedDay.date >= from_)
        .where(PlannedDay.date <= to)
    ).all()
    done = session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
        .where(WorkoutSession.finished_at.is_not(None))
        .where(WorkoutSession.date >= from_)
        .where(WorkoutSession.date <= to)
    ).all()
    planned_by_date = {p.date: p.workout_key for p in planned}
    done_by_date = {d.date: d.workout_key for d in done}
    all_dates = sorted(set(planned_by_date) | set(done_by_date))
    return [
        ConsistencyDay(
            date=d, planned_key=planned_by_date.get(d), done_key=done_by_date.get(d)
        )
        for d in all_dates
    ]
