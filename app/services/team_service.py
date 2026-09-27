"""Teams, memberships, invitations and project shares.

Team owners administer members, invites and shares; editors and viewers only
read team data. A project can only be shared with a team by the project owner.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.team import ProjectShare, Team, TeamInvite, TeamMember, TeamRole
from app.models.user import User
from app.schemas.team import InviteCreate, ProjectShareCreate, TeamCreate, TeamUpdate
from app.services.access_service import get_accessible_project


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _membership(db: Session, team_id: UUID, user_id: UUID) -> TeamMember | None:
    return db.scalar(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id))


def get_team(db: Session, user: User, team_id: UUID, minimum: TeamRole = TeamRole.VIEWER) -> tuple[Team, TeamMember]:
    team = db.get(Team, team_id)
    membership = _membership(db, team_id, user.id) if team else None
    if team is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Team not found')
    if minimum == TeamRole.OWNER and membership.role != TeamRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only team owners can do this')
    return team, membership


def _member_count(db: Session, team_id: UUID) -> int:
    return db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)) or 0


def _project_count(db: Session, team_id: UUID) -> int:
    return db.scalar(select(func.count()).select_from(ProjectShare).where(ProjectShare.team_id == team_id)) or 0


def _team_summary(db: Session, team: Team, membership: TeamMember) -> dict:
    return {
        'id': team.id,
        'name': team.name,
        'owner_id': team.owner_id,
        'my_role': TeamRole(membership.role),
        'member_count': _member_count(db, team.id),
        'project_count': _project_count(db, team.id),
        'created_at': team.created_at,
        'updated_at': team.updated_at,
    }


def _member_public(member: TeamMember) -> dict:
    return {
        'id': member.id,
        'user_id': member.user_id,
        'email': member.user.email,
        'first_name': member.user.first_name,
        'last_name': member.user.last_name,
        'role': TeamRole(member.role),
        'created_at': member.created_at,
    }


def list_teams(db: Session, user: User) -> list[dict]:
    rows = db.execute(
        select(Team, TeamMember).join(TeamMember, TeamMember.team_id == Team.id).where(TeamMember.user_id == user.id).order_by(Team.created_at)
    ).all()
    return [_team_summary(db, team, membership) for team, membership in rows]


def create_team(db: Session, user: User, payload: TeamCreate) -> dict:
    team = Team(name=payload.name.strip(), owner_id=user.id)
    db.add(team)
    db.flush()
    membership = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.OWNER)
    db.add(membership)
    db.commit()
    db.refresh(team)
    db.refresh(membership)
    return _team_summary(db, team, membership)


def team_detail(db: Session, user: User, team_id: UUID) -> dict:
    team, membership = get_team(db, user, team_id)
    members = db.scalars(select(TeamMember).where(TeamMember.team_id == team.id).order_by(TeamMember.created_at)).all()
    projects = db.scalars(
        select(Project).join(ProjectShare, ProjectShare.project_id == Project.id).where(ProjectShare.team_id == team.id).order_by(Project.updated_at.desc())
    ).all()
    for project in projects:
        project.access_role = TeamRole.OWNER if project.user_id == user.id else TeamRole(membership.role)
    invites: list[TeamInvite] = []
    if membership.role == TeamRole.OWNER:
        invites = list(
            db.scalars(
                select(TeamInvite)
                .where(TeamInvite.team_id == team.id, TeamInvite.accepted_at.is_(None), TeamInvite.expires_at > func.now())
                .order_by(TeamInvite.created_at.desc())
            ).all()
        )
    return {
        **_team_summary(db, team, membership),
        'members': [_member_public(member) for member in members],
        'projects': projects,
        'invites': invites,
    }


def update_team(db: Session, user: User, team_id: UUID, payload: TeamUpdate) -> dict:
    team, membership = get_team(db, user, team_id, TeamRole.OWNER)
    team.name = payload.name.strip()
    db.commit()
    db.refresh(team)
    return _team_summary(db, team, membership)


def delete_team(db: Session, user: User, team_id: UUID) -> None:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    db.delete(team)
    db.commit()


def create_invite(db: Session, user: User, team_id: UUID, payload: InviteCreate) -> dict:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    if payload.role == TeamRole.OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Ownership cannot be granted through an invite')
    token = secrets.token_urlsafe(32)
    invite = TeamInvite(
        team_id=team.id,
        invited_by=user.id,
        email=payload.email.lower() if payload.email else None,
        role=payload.role,
        token_hash=_hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(days=payload.expires_in_days),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {
        'id': invite.id,
        'team_id': invite.team_id,
        'email': invite.email,
        'role': TeamRole(invite.role),
        'expires_at': invite.expires_at,
        'accepted_at': invite.accepted_at,
        'created_at': invite.created_at,
        'token': token,
        'accept_url': f'{settings.frontend_url.rstrip("/")}/invites/{token}',
    }


def revoke_invite(db: Session, user: User, team_id: UUID, invite_id: UUID) -> None:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    invite = db.scalar(select(TeamInvite).where(TeamInvite.id == invite_id, TeamInvite.team_id == team.id))
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invite not found')
    db.delete(invite)
    db.commit()


def _valid_invite(db: Session, token: str) -> TeamInvite:
    invite = db.scalar(select(TeamInvite).where(TeamInvite.token_hash == _hash_token(token)))
    if not invite or invite.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invite not found')
    if invite.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail='Invite has expired')
    return invite


def preview_invite(db: Session, token: str) -> dict:
    invite = _valid_invite(db, token)
    inviter = db.get(User, invite.invited_by)
    return {
        'team_id': invite.team_id,
        'team_name': invite.team.name,
        'role': TeamRole(invite.role),
        'email': invite.email,
        'expires_at': invite.expires_at,
        'invited_by': f'{inviter.first_name} {inviter.last_name}'.strip() if inviter else '',
    }


def accept_invite(db: Session, user: User, token: str) -> dict:
    invite = _valid_invite(db, token)
    if invite.email and invite.email != user.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='This invite was issued to a different email')
    membership = _membership(db, invite.team_id, user.id)
    if membership is None:
        membership = TeamMember(team_id=invite.team_id, user_id=user.id, role=invite.role)
        db.add(membership)
    invite.accepted_at = datetime.now(UTC)
    invite.accepted_by = user.id
    db.commit()
    db.refresh(membership)
    return _team_summary(db, invite.team, membership)


def update_member_role(db: Session, user: User, team_id: UUID, member_id: UUID, role: TeamRole) -> dict:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    member = db.scalar(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')
    if member.user_id == team.owner_id and role != TeamRole.OWNER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The team creator must remain an owner')
    member.role = role
    db.commit()
    db.refresh(member)
    return _member_public(member)


def remove_member(db: Session, user: User, team_id: UUID, member_id: UUID) -> None:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    member = db.scalar(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')
    if member.user_id == team.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The team creator cannot be removed')
    db.delete(member)
    db.commit()


def leave_team(db: Session, user: User, team_id: UUID) -> None:
    team, membership = get_team(db, user, team_id)
    if membership.user_id == team.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='The team creator cannot leave; delete the team instead')
    db.delete(membership)
    db.commit()


def share_project(db: Session, user: User, team_id: UUID, payload: ProjectShareCreate) -> ProjectShare:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    project = get_accessible_project(db, user, payload.project_id, TeamRole.OWNER)
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only the project owner can share it')
    existing = db.scalar(select(ProjectShare).where(ProjectShare.project_id == project.id, ProjectShare.team_id == team.id))
    if existing:
        return existing
    share = ProjectShare(project_id=project.id, team_id=team.id, shared_by=user.id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def unshare_project(db: Session, user: User, team_id: UUID, project_id: UUID) -> None:
    team, _ = get_team(db, user, team_id, TeamRole.OWNER)
    share = db.scalar(select(ProjectShare).where(ProjectShare.project_id == project_id, ProjectShare.team_id == team.id))
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Share not found')
    db.delete(share)
    db.commit()
