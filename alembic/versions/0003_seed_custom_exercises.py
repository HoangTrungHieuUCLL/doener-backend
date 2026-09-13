"""seed custom (choose-your-own) exercises

Data migration adding standalone single exercises for the "Choose my own
exercises" plan option -- a mix of time-based cardio and reps-based
bodyweight moves so the record UI (time vs kg+reps) varies per exercise,
same mechanism as the existing catalog.

Revision ID: 0003_seed_custom_exercises
Revises: 0002_seed_exercises
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_seed_custom_exercises"
down_revision: Union[str, None] = "0002_seed_exercises"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


exercises_table = sa.table(
    "exercises",
    sa.column("key", sa.String),
    sa.column("name", sa.String),
    sa.column("category", sa.String),
    sa.column("type", sa.String),
    sa.column("sets", sa.Integer),
    sa.column("reps", sa.Integer),
    sa.column("duration_sec", sa.Integer),
    sa.column("tempo", sa.String),
    sa.column("rest_sec", sa.Integer),
    sa.column("per_side", sa.Boolean),
    sa.column("equipment", sa.String),
)


def _row(key, name, type_, sets, reps=None, duration_sec=None, rest_sec=0, equipment=None):
    return {
        "key": key,
        "name": name,
        "category": "custom",
        "type": type_,
        "sets": sets,
        "reps": reps,
        "duration_sec": duration_sec,
        "tempo": None,
        "rest_sec": rest_sec,
        "per_side": False,
        "equipment": equipment,
    }


SEED_ROWS = [
    _row("custom_running", "Running", "time", 1, duration_sec=1200, rest_sec=0),
    _row("custom_walking", "Walking", "time", 1, duration_sec=1800, rest_sec=0),
    _row("custom_cycling", "Cycling", "time", 1, duration_sec=1800, rest_sec=0),
    _row("custom_jump_rope", "Jump Rope", "time", 3, duration_sec=60, rest_sec=30),
    _row(
        "custom_rowing_machine",
        "Rowing Machine",
        "time",
        1,
        duration_sec=900,
        rest_sec=0,
        equipment="machine",
    ),
    _row(
        "custom_sit_up", "Sit-Up", "reps", 3, reps=15, rest_sec=45, equipment="bodyweight"
    ),
    _row(
        "custom_burpee", "Burpee", "reps", 3, reps=12, rest_sec=45, equipment="bodyweight"
    ),
    _row(
        "custom_pull_up", "Pull-Up", "reps", 3, reps=6, rest_sec=90, equipment="bodyweight"
    ),
]


def upgrade() -> None:
    op.bulk_insert(exercises_table, SEED_ROWS)


def downgrade() -> None:
    keys = [row["key"] for row in SEED_ROWS]
    conn = op.get_bind()
    conn.execute(exercises_table.delete().where(exercises_table.c.key.in_(keys)))
