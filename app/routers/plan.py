from datetime import date as date_

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models import PlannedDay, User
from app.schemas import PlannedDayPublic, PlanUpsertRequest

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("", response_model=list[PlannedDayPublic])
def get_plan(
    from_: date_ = Query(alias="from"),
    to: date_ = Query(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(PlannedDay)
        .where(PlannedDay.user_id == current_user.id)
        .where(PlannedDay.date >= from_)
        .where(PlannedDay.date <= to)
        .order_by(PlannedDay.date)
    )
    return session.exec(statement).all()


@router.post("", response_model=PlannedDayPublic)
def upsert_plan(
    payload: PlanUpsertRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = session.exec(
        select(PlannedDay)
        .where(PlannedDay.user_id == current_user.id)
        .where(PlannedDay.date == payload.date)
    ).first()

    if existing is not None:
        existing.workout_key = payload.workout_key
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    planned_day = PlannedDay(
        user_id=current_user.id, date=payload.date, workout_key=payload.workout_key
    )
    session.add(planned_day)
    session.commit()
    session.refresh(planned_day)
    return planned_day
