"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("tempo", sa.String(), nullable=True),
        sa.Column("rest_sec", sa.Integer(), nullable=False),
        sa.Column("per_side", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("equipment", sa.String(), nullable=True),
    )
    op.create_index("ix_exercises_key", "exercises", ["key"], unique=True)

    op.create_table(
        "planned_days",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("workout_key", sa.String(), nullable=False),
        sa.UniqueConstraint("user_id", "date", name="uq_planned_days_user_date"),
    )
    op.create_index("ix_planned_days_user_id", "planned_days", ["user_id"])
    op.create_index("ix_planned_days_date", "planned_days", ["date"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("workout_key", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("total_volume_kg", sa.Float(), nullable=True),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_date", "sessions", ["date"])

    op.create_table(
        "session_sets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id"), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
    )
    op.create_index("ix_session_sets_session_id", "session_sets", ["session_id"])
    op.create_index("ix_session_sets_exercise_id", "session_sets", ["exercise_id"])

    op.create_table(
        "cardio_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
    )
    op.create_index("ix_cardio_logs_session_id", "cardio_logs", ["session_id"])

    op.create_table(
        "personal_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id"), nullable=False),
        sa.Column("best_weight_kg", sa.Float(), nullable=False),
        sa.Column("achieved_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "exercise_id", name="uq_personal_records_user_exercise"),
    )
    op.create_index("ix_personal_records_user_id", "personal_records", ["user_id"])
    op.create_index("ix_personal_records_exercise_id", "personal_records", ["exercise_id"])


def downgrade() -> None:
    op.drop_table("personal_records")
    op.drop_table("cardio_logs")
    op.drop_table("session_sets")
    op.drop_table("sessions")
    op.drop_table("planned_days")
    op.drop_table("exercises")
    op.drop_table("users")
