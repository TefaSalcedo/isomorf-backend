from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.element import ElementPayload, ElementUpdate, ProjectElementPublic
from app.services.element_service import create_element, delete_element, list_elements, update_element

router = APIRouter(prefix='/api/projects/{project_id}/elements', tags=['elements'])


@router.get('', response_model=list[ProjectElementPublic])
def list_all(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_elements(db, user, project_id)


@router.post('', response_model=ProjectElementPublic, status_code=status.HTTP_201_CREATED)
def create(project_id: UUID, payload: ElementPayload, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_element(db, user, project_id, payload)


@router.put('/{element_id}', response_model=ProjectElementPublic)
def update(project_id: UUID, element_id: UUID, payload: ElementUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_element(db, user, project_id, element_id, payload)


@router.delete('/{element_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(project_id: UUID, element_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_element(db, user, project_id, element_id)
