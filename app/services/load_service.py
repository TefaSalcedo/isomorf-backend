from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_element import ProjectElement
from app.models.structural_load import ElementLoad, LoadCase
from app.models.user import User
from app.schemas.structural_load import ElementLoadCreate, ElementLoadUpdate, LoadCaseCreate


def get_project(db: Session, user: User, project_id: UUID) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


def get_case(db: Session, user: User, project_id: UUID, case_id: UUID) -> LoadCase:
    get_project(db, user, project_id)
    load_case = db.scalar(select(LoadCase).where(LoadCase.id == case_id, LoadCase.project_id == project_id))
    if not load_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Load case not found')
    return load_case


def list_cases(db: Session, user: User, project_id: UUID) -> list[LoadCase]:
    get_project(db, user, project_id)
    return list(db.scalars(select(LoadCase).where(LoadCase.project_id == project_id).order_by(LoadCase.created_at)).all())


def create_case(db: Session, user: User, project_id: UUID, payload: LoadCaseCreate) -> LoadCase:
    get_project(db, user, project_id)
    load_case = LoadCase(project_id=project_id, name=payload.name.strip(), category=payload.category)
    db.add(load_case)
    db.commit()
    db.refresh(load_case)
    return load_case


def list_loads(db: Session, user: User, project_id: UUID) -> list[ElementLoad]:
    get_project(db, user, project_id)
    return list(db.scalars(select(ElementLoad).join(LoadCase).where(LoadCase.project_id == project_id).order_by(ElementLoad.created_at)).all())


def validate_element(db: Session, project_id: UUID, element_id: UUID | None) -> None:
    if element_id is not None and not db.scalar(select(ProjectElement).where(ProjectElement.id == element_id, ProjectElement.project_id == project_id)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Element does not belong to project')


def create_load(db: Session, user: User, project_id: UUID, payload: ElementLoadCreate) -> ElementLoad:
    load_case = get_case(db, user, project_id, payload.load_case_id)
    validate_element(db, load_case.project_id, payload.element_id)
    load = ElementLoad(**payload.model_dump())
    db.add(load)
    db.commit()
    db.refresh(load)
    return load


def update_load(db: Session, user: User, project_id: UUID, load_id: UUID, payload: ElementLoadUpdate) -> ElementLoad:
    load = db.scalar(select(ElementLoad).join(LoadCase).where(ElementLoad.id == load_id, LoadCase.project_id == project_id))
    if not load:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Load not found')
    get_project(db, user, project_id)
    values = payload.model_dump(exclude_unset=True)
    validate_element(db, project_id, values.get('element_id', load.element_id))
    for key, value in values.items():
        setattr(load, key, value)
    db.commit()
    db.refresh(load)
    return load


def delete_load(db: Session, user: User, project_id: UUID, load_id: UUID) -> None:
    load = db.scalar(select(ElementLoad).join(LoadCase).where(ElementLoad.id == load_id, LoadCase.project_id == project_id))
    if not load:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Load not found')
    get_project(db, user, project_id)
    db.delete(load)
    db.commit()
