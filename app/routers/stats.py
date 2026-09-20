from datetime import date as date_

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlmodel import Session, func, select

from app.database import get_session
from app.deps import get_current_user
from app.models import Exercise, PersonalRecord, PlannedDay, SessionSet, User, WorkoutSession
from app.schemas import (
    ConsistencyDay,
    ExerciseProgressPoint,
    ExerciseTrendPoint,
    LastSetEntry,
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


# How many past sessions the per-exercise sparkline covers.
TREND_LIMIT = 8

# Newest-session-first ordering, with the session id as a final tiebreaker so
# sessions started within the same clock tick still order deterministically.
_SESSION_RECENCY = (
    WorkoutSession.date.desc(),
    WorkoutSession.started_at.desc(),
    WorkoutSession.id.desc(),
)


@router.get("/last-sets", response_model=list[LastSetPublic])
def get_last_sets(
    exclude_session_id: int | None = Query(
        default=None,
        description=(
            "Session to leave out -- pass the in-progress session so 'last time' "
            "always means a previous session rather than the sets just logged."
        ),
    ),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """One recap per exercise: every set from the last session it appeared in,
    plus a short trend of top efforts for the sessions before that."""
    # Rank each set within its exercise by session recency, so rn == 1 is the
    # final set of the most recent session that exercise was logged in. The
    # ranking runs in the database, so nothing unbounded is pulled into memory.
    ranked = (
        select(
            SessionSet.exercise_id.label("exercise_id"),
            SessionSet.weight_kg.label("weight_kg"),
            SessionSet.reps.label("reps"),
            SessionSet.duration_sec.label("duration_sec"),
            WorkoutSession.id.label("session_id"),
            WorkoutSession.date.label("date"),
            func.row_number()
            .over(
                partition_by=SessionSet.exercise_id,
                order_by=(*_SESSION_RECENCY, SessionSet.set_number.desc(), SessionSet.id.desc()),
            )
            .label("rn"),
        )
        .join(WorkoutSession, SessionSet.session_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == current_user.id)
    )
    if exclude_session_id is not None:
        ranked = ranked.where(WorkoutSession.id != exclude_session_id)
    ranked_sq = ranked.subquery()

    latest = session.exec(
        select(
            ranked_sq.c.exercise_id,
            ranked_sq.c.weight_kg,
            ranked_sq.c.reps,
            ranked_sq.c.duration_sec,
            ranked_sq.c.session_id,
            ranked_sq.c.date,
        ).where(ranked_sq.c.rn == 1)
    ).all()
    if not latest:
        return []

    # All sets of each winning (exercise, session) pair. An OR of equality
    # pairs rather than a row-value IN, which not every backend supports.
    pair_filter = or_(
        *[
            and_(SessionSet.exercise_id == row.exercise_id, SessionSet.session_id == row.session_id)
            for row in latest
        ]
    )
    set_rows = session.exec(
        select(SessionSet).where(pair_filter).order_by(SessionSet.set_number, SessionSet.id)
    ).all()
    sets_by_exercise: dict[int, list[LastSetEntry]] = {}
    for s in set_rows:
        sets_by_exercise.setdefault(s.exercise_id, []).append(
            LastSetEntry(
                set_number=s.set_number,
                weight_kg=s.weight_kg,
                reps=s.reps,
                duration_sec=s.duration_sec,
            )
        )

    # Top effort per (exercise, session), capped at TREND_LIMIT sessions per
    # exercise so the payload stays flat no matter how long the user's history.
    grouped = (
        select(
            SessionSet.exercise_id.label("exercise_id"),
            WorkoutSession.id.label("session_id"),
            WorkoutSession.date.label("date"),
            WorkoutSession.started_at.label("started_at"),
            func.max(SessionSet.weight_kg).label("top_weight_kg"),
            func.max(SessionSet.reps).label("top_reps"),
            func.max(SessionSet.duration_sec).label("top_duration_sec"),
        )
        .join(WorkoutSession, SessionSet.session_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == current_user.id)
    )
    if exclude_session_id is not None:
        grouped = grouped.where(WorkoutSession.id != exclude_session_id)
    grouped_sq = grouped.group_by(
        SessionSet.exercise_id, WorkoutSession.id, WorkoutSession.date, WorkoutSession.started_at
    ).subquery()

    trend_ranked = select(
        grouped_sq.c.exercise_id,
        grouped_sq.c.session_id,
        grouped_sq.c.date,
        grouped_sq.c.top_weight_kg,
        grouped_sq.c.top_reps,
        grouped_sq.c.top_duration_sec,
        func.row_number()
        .over(
            partition_by=grouped_sq.c.exercise_id,
            order_by=(
                grouped_sq.c.date.desc(),
                grouped_sq.c.started_at.desc(),
                grouped_sq.c.session_id.desc(),
            ),
        ).label("rn"),
    ).subquery()

    trend_rows = session.exec(
        select(
            trend_ranked.c.exercise_id,
            trend_ranked.c.session_id,
            trend_ranked.c.date,
            trend_ranked.c.top_weight_kg,
            trend_ranked.c.top_reps,
            trend_ranked.c.top_duration_sec,
        ).where(trend_ranked.c.rn <= TREND_LIMIT)
    ).all()

    trend_by_exercise: dict[int, list[ExerciseTrendPoint]] = {}
    for row in trend_rows:
        trend_by_exercise.setdefault(row.exercise_id, []).append(
            ExerciseTrendPoint(
                session_id=row.session_id,
                date=row.date,
                top_weight_kg=row.top_weight_kg,
                top_reps=row.top_reps,
                top_duration_sec=row.top_duration_sec,
            )
        )
    # Rows arrive newest-first; the sparkline reads left-to-right in time.
    for points in trend_by_exercise.values():
        points.reverse()

    return [
        LastSetPublic(
            exercise_id=row.exercise_id,
            weight_kg=row.weight_kg,
            reps=row.reps,
            duration_sec=row.duration_sec,
            session_id=row.session_id,
            date=row.date,
            sets=sets_by_exercise.get(row.exercise_id, []),
            trend=trend_by_exercise.get(row.exercise_id, []),
        )
        for row in latest
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
