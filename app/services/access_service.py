"""Project access resolution.

A user reaches a project either as its owner or through a team the project is
shared with; the effective role is the highest one granted. Unknown or
inaccessible projects answer 404 so their existence is never revealed, while
an insufficient role answers 403.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.project import Project
from app.models.team import ROLE_RANK, ProjectShare, TeamMember, TeamRole
from app.models.user import User


def resolve_project_role(db: Session, user: User, project: Project) -> TeamRole | None:
    if project.user_id == user.id:
        return TeamRole.OWNER
    roles = db.scalars(
        select(TeamMember.role)
        .join(ProjectShare, ProjectShare.team_id == TeamMember.team_id)
        .where(ProjectShare.project_id == project.id, TeamMember.user_id == user.id)
    ).all()
    if not roles:
        return None
    return max((TeamRole(role) for role in roles), key=lambda role: ROLE_RANK[role])


def has_role(role: TeamRole | None, minimum: TeamRole) -> bool:
    return role is not None and ROLE_RANK[role] >= ROLE_RANK[minimum]


def _project_query(project_id: str | UUID) -> Select[tuple[Project]]:
    identifier = str(project_id)
    try:
        internal_id: UUID | None = UUID(identifier)
    except ValueError:
        internal_id = None
    if internal_id is not None:
        return select(Project).where((Project.id == internal_id) | (Project.public_id == identifier))
    return select(Project).where(Project.public_id == identifier)


def get_accessible_project(db: Session, user: User, project_id: str | UUID, minimum: TeamRole = TeamRole.VIEWER, *, lock: bool = False) -> Project:
    query = _project_query(project_id)
    if lock:
        query = query.with_for_update()
    project = db.scalar(query)
    role = resolve_project_role(db, user, project) if project else None
    if project is None or role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if not has_role(role, minimum):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Requires {minimum.value} access to this project')
    project.access_role = role
    return project
