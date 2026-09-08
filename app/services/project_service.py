from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(db: Session, user: User) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc())).all())


def get_project(db: Session, user: User, project_id: UUID) -> Project:
    project = db.scalar(select(Project).options(selectinload(Project.elements)).where(Project.id == project_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


def create_project(db: Session, user: User, payload: ProjectCreate) -> Project:
    project = Project(user_id=user.id, name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, user: User, project_id: UUID, payload: ProjectUpdate) -> Project:
    project = get_project(db, user, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, user: User, project_id: UUID) -> None:
    project = get_project(db, user, project_id)
    db.delete(project)
    db.commit()
