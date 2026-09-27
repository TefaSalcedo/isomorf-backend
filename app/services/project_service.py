from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.models.project import Project
from app.models.team import ProjectShare, TeamMember, TeamRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.access_service import get_accessible_project, resolve_project_role
from app.services.document_service import _head_revision, ensure_baseline


def list_projects(db: Session, user: User) -> list[Project]:
    shared_ids = (
        select(ProjectShare.project_id)
        .join(TeamMember, TeamMember.team_id == ProjectShare.team_id)
        .where(TeamMember.user_id == user.id)
    )
    projects = list(
        db.scalars(
            select(Project)
            .where((Project.user_id == user.id) | Project.id.in_(shared_ids))
            .order_by(Project.updated_at.desc())
        ).all()
    )
    for project in projects:
        project.access_role = resolve_project_role(db, user, project) or TeamRole.VIEWER
    return projects


def get_project(db: Session, user: User, project_id: str | UUID, minimum: TeamRole = TeamRole.VIEWER) -> Project:
    project = get_accessible_project(db, user, project_id, minimum)
    project.head_revision = _head_revision(db, project.id)
    return project


def validate_folder(db: Session, user: User, folder_id: UUID | None) -> None:
    if folder_id is not None and not db.scalar(select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Folder does not belong to user')


def create_project(db: Session, user: User, payload: ProjectCreate) -> Project:
    validate_folder(db, user, payload.folder_id)
    project = Project(user_id=user.id, folder_id=payload.folder_id, name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    ensure_baseline(db, project)
    db.commit()
    return project


def update_project(db: Session, user: User, project_id: UUID, payload: ProjectUpdate) -> Project:
    values = payload.model_dump(exclude_unset=True)
    minimum = TeamRole.OWNER if 'folder_id' in values else TeamRole.EDITOR
    project = get_project(db, user, project_id, minimum)
    if 'folder_id' in values:
        validate_folder(db, user, values['folder_id'])
    for key, value in values.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, user: User, project_id: UUID) -> None:
    project = get_project(db, user, project_id, TeamRole.OWNER)
    db.delete(project)
    db.commit()
