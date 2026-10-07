from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.presets import MATERIAL_PRESETS, SECTION_PRESETS
from app.models.catalog import Material, Section
from app.models.team import TeamRole
from app.models.user import User
from app.schemas.catalog import MaterialCreate, MaterialUpdate, SectionCreate, SectionUpdate
from app.services.access_service import get_accessible_project


def list_materials(db: Session, user: User, project_id: UUID) -> list[Material]:
    get_accessible_project(db, user, project_id)
    return list(db.scalars(select(Material).where(Material.project_id == project_id).order_by(Material.name)).all())


def get_material(db: Session, user: User, project_id: UUID, material_id: UUID, minimum: TeamRole = TeamRole.VIEWER) -> Material:
    get_accessible_project(db, user, project_id, minimum)
    material = db.scalar(select(Material).where(Material.id == material_id, Material.project_id == project_id))
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Material not found')
    return material


def create_material(db: Session, user: User, project_id: UUID, payload: MaterialCreate) -> Material:
    get_accessible_project(db, user, project_id, TeamRole.EDITOR)
    material = Material(project_id=project_id, **payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def update_material(db: Session, user: User, project_id: UUID, material_id: UUID, payload: MaterialUpdate) -> Material:
    material = get_material(db, user, project_id, material_id, TeamRole.EDITOR)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(material, key, value)
    db.commit()
    db.refresh(material)
    return material


def delete_material(db: Session, user: User, project_id: UUID, material_id: UUID) -> None:
    material = get_material(db, user, project_id, material_id, TeamRole.EDITOR)
    db.delete(material)
    db.commit()


def list_sections(db: Session, user: User, project_id: UUID) -> list[Section]:
    get_accessible_project(db, user, project_id)
    return list(db.scalars(select(Section).where(Section.project_id == project_id).order_by(Section.name)).all())


def get_section(db: Session, user: User, project_id: UUID, section_id: UUID, minimum: TeamRole = TeamRole.VIEWER) -> Section:
    get_accessible_project(db, user, project_id, minimum)
    section = db.scalar(select(Section).where(Section.id == section_id, Section.project_id == project_id))
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Section not found')
    return section


def validate_material(db: Session, project_id: UUID, material_id: UUID | None) -> None:
    if material_id is not None and not db.scalar(select(Material).where(Material.id == material_id, Material.project_id == project_id)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Material does not belong to project')


def create_section(db: Session, user: User, project_id: UUID, payload: SectionCreate) -> Section:
    get_accessible_project(db, user, project_id, TeamRole.EDITOR)
    validate_material(db, project_id, payload.material_id)
    section = Section(project_id=project_id, **payload.model_dump())
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def update_section(db: Session, user: User, project_id: UUID, section_id: UUID, payload: SectionUpdate) -> Section:
    section = get_section(db, user, project_id, section_id, TeamRole.EDITOR)
    values = payload.model_dump(exclude_unset=True)
    validate_material(db, project_id, values.get('material_id', section.material_id))
    for key, value in values.items():
        setattr(section, key, value)
    db.commit()
    db.refresh(section)
    return section


def delete_section(db: Session, user: User, project_id: UUID, section_id: UUID) -> None:
    section = get_section(db, user, project_id, section_id, TeamRole.EDITOR)
    db.delete(section)
    db.commit()


def list_presets() -> dict:
    return {'materials': MATERIAL_PRESETS, 'sections': SECTION_PRESETS}
