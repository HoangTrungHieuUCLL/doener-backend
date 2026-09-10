"""seed exercises

Data migration seeding the fixed catalog of 22 exercises. The exercises
table is read-only via the API after this runs.

Revision ID: 0002_seed_exercises
Revises: 0001_initial
Create Date: 2026-09-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_seed_exercises"
down_revision: Union[str, None] = "0001_initial"
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


def _row(
    key,
    name,
    category,
    type_,
    sets,
    reps=None,
    duration_sec=None,
    tempo=None,
    rest_sec=0,
    per_side=False,
    equipment=None,
):
    return {
        "key": key,
        "name": name,
        "category": category,
        "type": type_,
        "sets": sets,
        "reps": reps,
        "duration_sec": duration_sec,
        "tempo": tempo,
        "rest_sec": rest_sec,
        "per_side": per_side,
        "equipment": equipment,
    }


SEED_ROWS = [
    # --- warmup: 1 set each, rest_sec=0, no tempo, before every workout ---
    _row("warmup_bar_hang", "Bar Hang", "warmup", "time", 1, duration_sec=30, rest_sec=0),
    _row(
        "warmup_deep_squat_hold",
        "Deep Squat Hold",
        "warmup",
        "time",
        1,
        duration_sec=60,
        rest_sec=0,
    ),
    _row(
        "warmup_horizontal_arm_swings",
        "Horizontal Arm Swings",
        "warmup",
        "reps",
        1,
        reps=10,
        rest_sec=0,
    ),
    _row(
        "warmup_torso_rotation_swings",
        "Torso Rotation Swings",
        "warmup",
        "reps",
        1,
        reps=10,
        rest_sec=0,
    ),
    _row("warmup_swimmers", "Swimmers", "warmup", "reps", 1, reps=10, rest_sec=0),
    _row("warmup_hip_raises", "Hip Raises", "warmup", "reps", 1, reps=10, rest_sec=0),
    _row("warmup_jumping_jacks", "Jumping Jacks", "warmup", "reps", 1, reps=50, rest_sec=0),
    # --- workout A: tempo 3/1, rest 90s, 4x8 unless noted ---
    _row(
        "a_lying_leg_curl",
        "Lying Leg Curl",
        "A",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "a_goblet_squat",
        "Goblet Squat",
        "A",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="free_weight",
    ),
    _row(
        "a_machine_row",
        "Machine Row",
        "A",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="cable",
    ),
    _row(
        "a_push_up",
        "Push-Up",
        "A",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="bodyweight",
    ),
    _row(
        "a_forearm_plank",
        "Forearm Plank",
        "A",
        "time",
        3,
        duration_sec=30,
        tempo=None,
        rest_sec=90,
        equipment="bodyweight",
    ),
    # --- workout B: tempo 3/1 default (2/1 where noted), rest 90s, 4x8 unless noted ---
    _row(
        "b_back_extension",
        "Back Extension",
        "B",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "b_reverse_lunge",
        "Reverse Lunge",
        "B",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        per_side=True,
        equipment="bodyweight",
    ),
    _row(
        "b_reverse_fly",
        "Reverse Fly",
        "B",
        "reps",
        4,
        reps=8,
        tempo="2/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "b_chest_press",
        "Chest Press (Parallel Grip)",
        "B",
        "reps",
        4,
        reps=8,
        tempo="2/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "b_side_plank",
        "Side Plank",
        "B",
        "time",
        3,
        duration_sec=30,
        tempo=None,
        rest_sec=90,
        per_side=True,
        equipment="bodyweight",
    ),
    # --- workout C: tempo 3/1, rest 90s, 4x8 unless noted ---
    _row(
        "c_hip_thrust",
        "Hip Thrust (Dumbbell)",
        "C",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="free_weight",
    ),
    _row(
        "c_leg_press",
        "Leg Press",
        "C",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "c_lat_pulldown",
        "Lat Pulldown",
        "C",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="cable",
    ),
    _row(
        "c_machine_fly",
        "Machine Fly",
        "C",
        "reps",
        4,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        equipment="machine",
    ),
    _row(
        "c_cable_lateral_raise",
        "Cable Lateral Raise",
        "C",
        "reps",
        3,
        reps=8,
        tempo="3/1",
        rest_sec=90,
        per_side=True,
        equipment="cable",
    ),
]


def upgrade() -> None:
    op.bulk_insert(exercises_table, SEED_ROWS)


def downgrade() -> None:
    keys = [row["key"] for row in SEED_ROWS]
    conn = op.get_bind()
    conn.execute(
        exercises_table.delete().where(exercises_table.c.key.in_(keys))
    )
