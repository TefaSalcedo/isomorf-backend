from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_element import ProjectElement
from app.models.user import User
from app.schemas.element import ElementPayload, ElementUpdate


def get_owned_project(db: Session, user: User, project_id: UUID) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


def list_elements(db: Session, user: User, project_id: UUID) -> list[ProjectElement]:
    get_owned_project(db, user, project_id)
    return list(db.scalars(select(ProjectElement).where(ProjectElement.project_id == project_id).order_by(ProjectElement.created_at)).all())


def get_element(db: Session, user: User, project_id: UUID, element_id: UUID) -> ProjectElement:
    get_owned_project(db, user, project_id)
    element = db.scalar(select(ProjectElement).where(ProjectElement.id == element_id, ProjectElement.project_id == project_id))
    if not element:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Element not found')
    return element


def create_element(db: Session, user: User, project_id: UUID, payload: ElementPayload) -> ProjectElement:
    get_owned_project(db, user, project_id)
    data = payload.model_dump(exclude={'id'})
    data['id'] = payload.id if payload.id is not None else uuid4()
    element = ProjectElement(project_id=project_id, **data)
    db.add(element)
    db.commit()
    db.refresh(element)
    return element


def update_element(db: Session, user: User, project_id: UUID, element_id: UUID, payload: ElementUpdate) -> ProjectElement:
    element = get_element(db, user, project_id, element_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(element, key, value)
    db.commit()
    db.refresh(element)
    return element


def delete_element(db: Session, user: User, project_id: UUID, element_id: UUID) -> None:
    element = get_element(db, user, project_id, element_id)
    db.delete(element)
    db.commit()
