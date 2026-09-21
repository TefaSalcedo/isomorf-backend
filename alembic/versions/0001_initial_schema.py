"""Create initial ISOMORF schema.

Revision ID: 0001_initial_schema
Revises:
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

element_type = postgresql.ENUM('wall', 'door', 'window', name='element_type')
element_type_column = postgresql.ENUM('wall', 'door', 'window', name='element_type', create_type=False)


def upgrade() -> None:
    element_type.create(op.get_bind(), checkfirst=True)
    op.create_table('users', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('email', sa.String(320), nullable=False), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('first_name', sa.String(100), nullable=False), sa.Column('last_name', sa.String(100), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table('projects', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('name', sa.String(200), nullable=False), sa.Column('description', sa.Text(), nullable=False, server_default=''), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])
    op.create_table('project_elements', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False), sa.Column('element_type', element_type_column, nullable=False), sa.Column('x1', sa.Float(), nullable=False), sa.Column('y1', sa.Float(), nullable=False), sa.Column('x2', sa.Float(), nullable=False), sa.Column('y2', sa.Float(), nullable=False), sa.Column('length', sa.Float(), nullable=False), sa.Column('rotation', sa.Float(), nullable=False, server_default='0'), sa.Column('properties', postgresql.JSONB(), nullable=False, server_default='{}'), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_project_elements_project_id', 'project_elements', ['project_id'])
    op.create_table('device_sessions', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('public_key', sa.Text(), nullable=False), sa.Column('key_id', sa.String(128), nullable=False), sa.Column('fingerprint_hash', sa.String(64), nullable=False), sa.Column('device_name', sa.String(120)), sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()), sa.Column('revoked_at', sa.DateTime(timezone=True)), sa.Column('revocation_reason', sa.String(255)))
    op.create_index('ix_device_sessions_user_id', 'device_sessions', ['user_id'])
    op.create_index('ix_device_sessions_key_id', 'device_sessions', ['key_id'], unique=True)
    op.create_table('device_nonces', sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('device_sessions.id', ondelete='CASCADE'), nullable=False), sa.Column('nonce_hash', sa.String(64), nullable=False), sa.Column('used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_device_nonces_session_id', 'device_nonces', ['session_id'])
    op.create_index('ix_device_nonces_nonce_hash', 'device_nonces', ['nonce_hash'], unique=True)


def downgrade() -> None:
    op.drop_table('device_nonces')
    op.drop_table('device_sessions')
    op.drop_table('project_elements')
    op.drop_table('projects')
    op.drop_table('users')
    element_type.drop(op.get_bind(), checkfirst=True)
