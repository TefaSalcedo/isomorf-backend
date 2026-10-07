"""Extend element types and add material/section catalog.

Revision ID: 0007_element_catalog
Revises: 0006_teams_and_shares

Adds the structural element types needed for a complete parametric model
(slabs, footings, stairs, ramps, openings, joists, grade beams, braces, piles),
creates the ``materials`` and ``sections`` catalog tables, and lets elements
reference them through ``material_id``/``section_id``.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0007_element_catalog'
down_revision: Union[str, Sequence[str], None] = '0006_teams_and_shares'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ELEMENT_TYPES = ('slab', 'footing', 'stair', 'ramp', 'opening', 'joist', 'grade_beam', 'brace', 'pile')


def upgrade() -> None:
    for value in NEW_ELEMENT_TYPES:
        op.execute(f"ALTER TYPE element_type ADD VALUE IF NOT EXISTS '{value}'")

    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.Enum('concrete', 'steel', 'masonry', 'timber', 'aluminum', 'generic', name='material_category'), nullable=False, server_default='generic'),
        sa.Column('properties', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('shape', sa.Enum('rectangular', 'circular', 'i_shape', 't_shape', 'l_shape', 'box', 'pipe', 'custom', name='section_shape'), nullable=False, server_default='rectangular'),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='SET NULL'), nullable=True),
        sa.Column('dimensions', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('properties', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column('project_elements', sa.Column('material_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='SET NULL'), nullable=True))
    op.add_column('project_elements', sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_project_elements_material_id', 'project_elements', ['material_id'])
    op.create_index('ix_project_elements_section_id', 'project_elements', ['section_id'])


def downgrade() -> None:
    op.drop_column('project_elements', 'section_id')
    op.drop_column('project_elements', 'material_id')
    op.drop_table('sections')
    op.drop_table('materials')
    op.execute('DROP TYPE IF EXISTS section_shape')
    op.execute('DROP TYPE IF EXISTS material_category')
    # PostgreSQL does not support removing enum values; recreate the type if a
    # real rollback is needed.
