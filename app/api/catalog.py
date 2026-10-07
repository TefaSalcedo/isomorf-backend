from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.catalog import (
    CatalogPresets,
    MaterialCreate,
    MaterialPublic,
    MaterialUpdate,
    SectionCreate,
    SectionPublic,
    SectionUpdate,
)
from app.services.catalog_service import (
    create_material,
    create_section,
    delete_material,
    delete_section,
    list_materials,
    list_presets,
    list_sections,
    update_material,
    update_section,
)

presets_router = APIRouter(prefix='/api/catalog', tags=['catalog'])
materials_router = APIRouter(prefix='/api/projects/{project_id}/materials', tags=['materials'])
sections_router = APIRouter(prefix='/api/projects/{project_id}/sections', tags=['sections'])


@presets_router.get('/presets', response_model=CatalogPresets)
def get_presets(user: User = Depends(get_current_user)):
    return list_presets()


@materials_router.get('', response_model=list[MaterialPublic])
def list_project_materials(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_materials(db, user, project_id)


@materials_router.post('', response_model=MaterialPublic, status_code=status.HTTP_201_CREATED)
def create_project_material(project_id: UUID, payload: MaterialCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_material(db, user, project_id, payload)


@materials_router.put('/{material_id}', response_model=MaterialPublic)
def update_project_material(project_id: UUID, material_id: UUID, payload: MaterialUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_material(db, user, project_id, material_id, payload)


@materials_router.delete('/{material_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_project_material(project_id: UUID, material_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_material(db, user, project_id, material_id)


@sections_router.get('', response_model=list[SectionPublic])
def list_project_sections(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_sections(db, user, project_id)


@sections_router.post('', response_model=SectionPublic, status_code=status.HTTP_201_CREATED)
def create_project_section(project_id: UUID, payload: SectionCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_section(db, user, project_id, payload)


@sections_router.put('/{section_id}', response_model=SectionPublic)
def update_project_section(project_id: UUID, section_id: UUID, payload: SectionUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_section(db, user, project_id, section_id, payload)


@sections_router.delete('/{section_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_project_section(project_id: UUID, section_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_section(db, user, project_id, section_id)
