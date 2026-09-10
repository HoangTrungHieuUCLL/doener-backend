from datetime import date as date_

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.database import get_session
from app.deps import get_current_user
from app.models import PlannedDay, User, WorkoutSession
from app.schemas import LastSessionSummary, TodayPlan, TogetherEntry

router = APIRouter(tags=["together"])


@router.get("/together", response_model=list[TogetherEntry])
def get_together(
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
):
    today = date_.today()
    users = session.exec(select(User).order_by(User.id)).all()

    entries: list[TogetherEntry] = []
    for user in users:
        today_plan_row = session.exec(
            select(PlannedDay)
            .where(PlannedDay.user_id == user.id)
            .where(PlannedDay.date == today)
        ).first()
        today_plan = TodayPlan(workout_key=today_plan_row.workout_key) if today_plan_row else None

        finished_today = session.exec(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .where(WorkoutSession.date == today)
            .where(WorkoutSession.finished_at.is_not(None))
        ).first()
        today_status = "done" if finished_today is not None else "not_done"

        last_session_row = session.exec(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
            .order_by(WorkoutSession.date.desc(), WorkoutSession.started_at.desc())
        ).first()
        last_session = (
            LastSessionSummary(
                id=last_session_row.id,
                date=last_session_row.date,
                workout_key=last_session_row.workout_key,
                total_volume_kg=last_session_row.total_volume_kg,
            )
            if last_session_row is not None
            else None
        )

        session_count = session.exec(
            select(func.count())
            .select_from(WorkoutSession)
            .where(WorkoutSession.user_id == user.id)
        ).one()

        entries.append(
            TogetherEntry(
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                today_plan=today_plan,
                today_status=today_status,
                last_session=last_session,
                session_count=session_count,
            )
        )

    return entries
