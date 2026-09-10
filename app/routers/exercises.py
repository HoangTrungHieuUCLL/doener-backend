from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models import Exercise, User
from app.schemas import ExercisePublic

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExercisePublic])
def list_exercises(
    session: Session = Depends(get_session),
    _current_user: User = Depends(get_current_user),
):
    exercises = session.exec(select(Exercise).order_by(Exercise.id)).all()
    return exercises
