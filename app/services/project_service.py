from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.folder import Folder
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.document_service import _head_revision, ensure_baseline


def list_projects(db: Session, user: User) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc())).all())


def get_project(db: Session, user: User, project_id: str | UUID) -> Project:
    identifier = str(project_id)
    project = db.scalar(select(Project).options(selectinload(Project.elements)).where(Project.public_id == identifier, Project.user_id == user.id))
    if not project:
        try:
            internal_id = UUID(identifier)
        except ValueError:
            internal_id = None
        if internal_id:
            project = db.scalar(select(Project).options(selectinload(Project.elements)).where(Project.id == internal_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
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
    project = get_project(db, user, project_id)
    values = payload.model_dump(exclude_unset=True)
    if 'folder_id' in values:
        validate_folder(db, user, values['folder_id'])
    for key, value in values.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, user: User, project_id: UUID) -> None:
    project = get_project(db, user, project_id)
    db.delete(project)
    db.commit()
