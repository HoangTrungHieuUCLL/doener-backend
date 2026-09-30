"""Allow more than one planned workout per day

Revision ID: 0004_multiple_plans_per_day
Revises: 0003_seed_custom_exercises
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004_multiple_plans_per_day"
down_revision: Union[str, None] = "0003_seed_custom_exercises"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch mode so SQLite (which cannot drop a constraint in place) rebuilds the table.
    with op.batch_alter_table("planned_days") as batch_op:
        batch_op.drop_constraint("uq_planned_days_user_date", type_="unique")


def downgrade() -> None:
    # Fails if a day already holds several workouts; remove the extras first.
    with op.batch_alter_table("planned_days") as batch_op:
        batch_op.create_unique_constraint("uq_planned_days_user_date", ["user_id", "date"])
