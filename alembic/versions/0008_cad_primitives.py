"""Add CAD drawing primitive element types.

Revision ID: 0008_cad_primitives
Revises: 0007_element_catalog

Adds the annotation primitives from roadmap week 8 (line, polyline, arc,
circle, ellipse, rectangle, hatch) to the ``element_type`` enum so drawing
entities can be persisted alongside structural elements.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0008_cad_primitives'
down_revision: Union[str, Sequence[str], None] = '0007_element_catalog'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ELEMENT_TYPES = ('line', 'polyline', 'arc', 'circle', 'ellipse', 'rectangle', 'hatch')


def upgrade() -> None:
    for value in NEW_ELEMENT_TYPES:
        op.execute(f"ALTER TYPE element_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; recreate the type if a
    # real rollback is needed.
    pass
