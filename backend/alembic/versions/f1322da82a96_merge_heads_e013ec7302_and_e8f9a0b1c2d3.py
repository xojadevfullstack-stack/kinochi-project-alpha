"""merge heads e013ec7302 and e8f9a0b1c2d3

Revision ID: f1322da82a96
Revises: e013ec7302, e8f9a0b1c2d3
Create Date: 2026-10-27 10:09:20.446672
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = 'f1322da82a96'
down_revision: Union[str, None] = ('e013ec7302', 'e8f9a0b1c2d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
