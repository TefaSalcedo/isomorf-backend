from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TeamRole(StrEnum):
    OWNER = 'owner'
    EDITOR = 'editor'
    VIEWER = 'viewer'


ROLE_RANK = {TeamRole.VIEWER: 1, TeamRole.EDITOR: 2, TeamRole.OWNER: 3}


class Team(Base):
    __tablename__ = 'teams'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    members = relationship('TeamMember', back_populates='team', cascade='all, delete-orphan')
    invites = relationship('TeamInvite', back_populates='team', cascade='all, delete-orphan')
    shares = relationship('ProjectShare', back_populates='team', cascade='all, delete-orphan')


class TeamMember(Base):
    __tablename__ = 'team_members'
    __table_args__ = (UniqueConstraint('team_id', 'user_id', name='uq_team_members_team_user'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    role: Mapped[TeamRole] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team = relationship('Team', back_populates='members')
    user = relationship('User')


class TeamInvite(Base):
    __tablename__ = 'team_invites'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), index=True, nullable=False)
    invited_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    role: Mapped[TeamRole] = mapped_column(String(10), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team = relationship('Team', back_populates='invites')


class ProjectShare(Base):
    __tablename__ = 'project_shares'
    __table_args__ = (UniqueConstraint('project_id', 'team_id', name='uq_project_shares_project_team'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    team_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), index=True, nullable=False)
    shared_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team = relationship('Team', back_populates='shares')
    project = relationship('Project')
