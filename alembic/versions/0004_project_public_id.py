"""Add stable public project identifiers.

Revision ID: 0004_project_public_id
Revises: 0003_workspace_folders_loads
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = '0004_project_public_id'
down_revision: Union[str, Sequence[str], None] = '0003_workspace_folders_loads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('public_id', sa.String(length=12), nullable=True))
    op.execute("UPDATE projects SET public_id = substr(md5(id::text), 1, 12) WHERE public_id IS NULL")
    op.alter_column('projects', 'public_id', nullable=False)
    op.create_index('ix_projects_public_id', 'projects', ['public_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_projects_public_id', table_name='projects')
    op.drop_column('projects', 'public_id')
