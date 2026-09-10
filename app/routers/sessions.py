from datetime import date as date_
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.database import get_session
from app.deps import get_current_user
from app.models import CardioLog, Exercise, PersonalRecord, SessionSet, User, WorkoutSession
from app.schemas import (
    CardioDetail,
    CardioLogCreateRequest,
    CardioLogPublic,
    SessionCreateRequest,
    SessionDetail,
    SessionListResponse,
    SessionPublic,
    SessionSetCreateRequest,
    SessionSetDetail,
    SessionSetPublic,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_owned_session(session_id: int, session: Session, current_user: User) -> WorkoutSession:
    workout_session = session.get(WorkoutSession, session_id)
    if workout_session is None or workout_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return workout_session


@router.post("", response_model=SessionPublic, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workout_session = WorkoutSession(
        user_id=current_user.id,
        date=date_.today(),
        workout_key=payload.workout_key,
        started_at=datetime.now(timezone.utc),
    )
    session.add(workout_session)
    session.commit()
    session.refresh(workout_session)
    return workout_session


@router.post(
    "/{session_id}/sets", response_model=SessionSetPublic, status_code=status.HTTP_201_CREATED
)
def add_set(
    session_id: int,
    payload: SessionSetCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workout_session = _get_owned_session(session_id, session, current_user)
    if workout_session.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Session is already finished"
        )

    exercise = session.get(Exercise, payload.exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    existing_count = session.exec(
        select(func.count())
        .select_from(SessionSet)
        .where(SessionSet.session_id == session_id)
        .where(SessionSet.exercise_id == payload.exercise_id)
    ).one()
    set_number = existing_count + 1

    session_set = SessionSet(
        session_id=session_id,
        exercise_id=payload.exercise_id,
        set_number=set_number,
        weight_kg=payload.weight_kg,
        reps=payload.reps,
        duration_sec=payload.duration_sec,
    )
    session.add(session_set)

    is_new_pr = False
    if payload.weight_kg is not None:
        pr = session.exec(
            select(PersonalRecord)
            .where(PersonalRecord.user_id == current_user.id)
            .where(PersonalRecord.exercise_id == payload.exercise_id)
        ).first()
        if pr is None:
            pr = PersonalRecord(
                user_id=current_user.id,
                exercise_id=payload.exercise_id,
                best_weight_kg=payload.weight_kg,
                achieved_at=datetime.now(timezone.utc),
            )
            session.add(pr)
            is_new_pr = True
        elif payload.weight_kg > pr.best_weight_kg:
            pr.best_weight_kg = payload.weight_kg
            pr.achieved_at = datetime.now(timezone.utc)
            session.add(pr)
            is_new_pr = True

    session.commit()
    session.refresh(session_set)

    return SessionSetPublic(
        id=session_set.id,
        session_id=session_set.session_id,
        exercise_id=session_set.exercise_id,
        set_number=session_set.set_number,
        weight_kg=session_set.weight_kg,
        reps=session_set.reps,
        duration_sec=session_set.duration_sec,
        is_new_pr=is_new_pr,
    )


@router.post(
    "/{session_id}/cardio", response_model=CardioLogPublic, status_code=status.HTTP_201_CREATED
)
def add_cardio(
    session_id: int,
    payload: CardioLogCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workout_session = _get_owned_session(session_id, session, current_user)
    if workout_session.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Session is already finished"
        )

    cardio_log = CardioLog(
        session_id=session_id,
        duration_sec=payload.duration_sec,
        distance_km=payload.distance_km,
    )
    session.add(cardio_log)
    session.commit()
    session.refresh(cardio_log)
    return cardio_log


@router.post("/{session_id}/finish", response_model=SessionPublic)
def finish_session(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workout_session = _get_owned_session(session_id, session, current_user)
    if workout_session.finished_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Session is already finished"
        )

    finished_at = datetime.now(timezone.utc)
    started_at = workout_session.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    duration_sec = int((finished_at - started_at).total_seconds())

    sets = session.exec(
        select(SessionSet).where(SessionSet.session_id == session_id)
    ).all()
    total_volume_kg = sum(
        (s.weight_kg * s.reps) for s in sets if s.weight_kg is not None and s.reps is not None
    )

    workout_session.finished_at = finished_at
    workout_session.duration_sec = duration_sec
    workout_session.total_volume_kg = float(total_volume_kg)

    session.add(workout_session)
    session.commit()
    session.refresh(workout_session)
    return workout_session


@router.get("", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    base_query = select(WorkoutSession).where(WorkoutSession.user_id == current_user.id)

    total = session.exec(
        select(func.count())
        .select_from(WorkoutSession)
        .where(WorkoutSession.user_id == current_user.id)
    ).one()

    items = session.exec(
        base_query.order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return SessionListResponse(items=items, total=total)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session_detail(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    workout_session = _get_owned_session(session_id, session, current_user)

    rows = session.exec(
        select(SessionSet, Exercise)
        .join(Exercise, SessionSet.exercise_id == Exercise.id)
        .where(SessionSet.session_id == session_id)
        .order_by(SessionSet.id)
    ).all()
    sets = [
        SessionSetDetail(
            id=session_set.id,
            exercise_id=session_set.exercise_id,
            exercise_name=exercise.name,
            set_number=session_set.set_number,
            weight_kg=session_set.weight_kg,
            reps=session_set.reps,
            duration_sec=session_set.duration_sec,
        )
        for session_set, exercise in rows
    ]

    cardio_log = session.exec(
        select(CardioLog).where(CardioLog.session_id == session_id)
    ).first()
    cardio = (
        CardioDetail(duration_sec=cardio_log.duration_sec, distance_km=cardio_log.distance_km)
        if cardio_log is not None
        else None
    )

    return SessionDetail(
        id=workout_session.id,
        date=workout_session.date,
        workout_key=workout_session.workout_key,
        started_at=workout_session.started_at,
        finished_at=workout_session.finished_at,
        duration_sec=workout_session.duration_sec,
        total_volume_kg=workout_session.total_volume_kg,
        sets=sets,
        cardio=cardio,
    )
