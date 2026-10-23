"""Add Week 11 annotation element types.

Revision ID: 0010_annotations
Revises: 0009_blocks_library
"""

from typing import Sequence, Union

from alembic import op

revision: str = '0010_annotations'
down_revision: Union[str, Sequence[str], None] = '0009_blocks_library'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ELEMENT_TYPES = ('dimension', 'leader', 'text', 'table')


def upgrade() -> None:
    for value in NEW_ELEMENT_TYPES:
        op.execute(f"ALTER TYPE element_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values.
    pass
