"""Add workspace folders and structural load inputs.

Revision ID: 0003_workspace_folders_loads
Revises: 0002_editor_structural_support
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003_workspace_folders_loads'
down_revision: Union[str, Sequence[str], None] = '0002_editor_structural_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'folders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_folders_user_id', 'folders', ['user_id'])
    op.add_column('projects', sa.Column('folder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('folders.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_projects_folder_id', 'projects', ['folder_id'])
    op.create_table(
        'load_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='service'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_load_cases_project_id', 'load_cases', ['project_id'])
    op.create_table(
        'element_loads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('load_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('load_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('element_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_elements.id', ondelete='SET NULL'), nullable=True),
        sa.Column('load_type', sa.String(30), nullable=False),
        sa.Column('magnitude', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(30), nullable=False, server_default='kN/m'),
        sa.Column('direction', sa.String(20), nullable=False, server_default='-Y'),
        sa.Column('position', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_element_loads_load_case_id', 'element_loads', ['load_case_id'])
    op.create_index('ix_element_loads_element_id', 'element_loads', ['element_id'])


def downgrade() -> None:
    op.drop_index('ix_element_loads_element_id', table_name='element_loads')
    op.drop_index('ix_element_loads_load_case_id', table_name='element_loads')
    op.drop_table('element_loads')
    op.drop_index('ix_load_cases_project_id', table_name='load_cases')
    op.drop_table('load_cases')
    op.drop_index('ix_projects_folder_id', table_name='projects')
    op.drop_column('projects', 'folder_id')
    op.drop_index('ix_folders_user_id', table_name='folders')
    op.drop_table('folders')
