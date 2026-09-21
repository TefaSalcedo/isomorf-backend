"""Add versioned document model: snapshots, per-element diffs and revision pointer.

Revision ID: 0005_versioned_documents
Revises: 0004_project_public_id
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0005_versioned_documents'
down_revision: Union[str, Sequence[str], None] = '0004_project_public_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'project_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'revision', name='uq_project_documents_project_revision'),
    )
    op.create_index('ix_project_documents_project_id', 'project_documents', ['project_id'])

    op.create_table(
        'element_revisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('project_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('element_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation', sa.String(length=10), nullable=False),
        sa.Column('before', postgresql.JSONB(), nullable=True),
        sa.Column('after', postgresql.JSONB(), nullable=True),
    )
    op.create_index('ix_element_revisions_document_id', 'element_revisions', ['document_id'])
    op.create_index('ix_element_revisions_project_id', 'element_revisions', ['project_id'])

    op.add_column('projects', sa.Column('current_revision', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('projects', 'current_revision')
    op.drop_index('ix_element_revisions_project_id', table_name='element_revisions')
    op.drop_index('ix_element_revisions_document_id', table_name='element_revisions')
    op.drop_table('element_revisions')
    op.drop_index('ix_project_documents_project_id', table_name='project_documents')
    op.drop_table('project_documents')
