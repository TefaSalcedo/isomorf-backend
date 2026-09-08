"""Add structural element types and project design settings.

Revision ID: 0002_editor_structural_support
Revises: 0001_initial_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_editor_structural_support'
down_revision: Union[str, Sequence[str], None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE element_type ADD VALUE 'column'")
    op.execute("ALTER TYPE element_type ADD VALUE 'beam'")
    op.add_column(
        'projects',
        sa.Column(
            'design_settings',
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('projects', 'design_settings')
    # PostgreSQL does not support removing enum values directly.
    # Recreate the type with only the original values if needed in a real rollback.
    pass
