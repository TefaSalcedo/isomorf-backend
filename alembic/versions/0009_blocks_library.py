"""Add block_ref element type and the project block library.

Revision ID: 0009_blocks_library
Revises: 0008_cad_primitives

Roadmap week 10: reusable blocks/symbols. ``block_ref`` marks an element
that points at a row in ``project_blocks`` (a named group of items stored
in block-local coordinates, inserted at the element's own geometry).
Layer linetype/lineweight live inside ``design_settings`` JSONB, so they
need no DDL here.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0009_blocks_library'
down_revision: Union[str, Sequence[str], None] = '0008_cad_primitives'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE element_type ADD VALUE IF NOT EXISTS 'block_ref'")
    op.create_table(
        'project_blocks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('base_x', sa.Float(), nullable=False, server_default='0'),
        sa.Column('base_y', sa.Float(), nullable=False, server_default='0'),
        sa.Column('items', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_project_blocks_project_id', 'project_blocks', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_project_blocks_project_id', table_name='project_blocks')
    op.drop_table('project_blocks')
    # PostgreSQL does not support removing enum values; 'block_ref' stays
    # in the element_type enum after downgrade (same as 0008).
