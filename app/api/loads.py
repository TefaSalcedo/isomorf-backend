from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.structural_load import ElementLoadCreate, ElementLoadPublic, ElementLoadUpdate, LoadCaseCreate, LoadCasePublic
from app.services.load_service import create_case, create_load, delete_load, list_cases, list_loads, update_load

router = APIRouter(prefix='/api/projects/{project_id}', tags=['loads'])


@router.get('/load-cases', response_model=list[LoadCasePublic])
def get_cases(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_cases(db, user, project_id)


@router.post('/load-cases', response_model=LoadCasePublic, status_code=status.HTTP_201_CREATED)
def add_case(project_id: UUID, payload: LoadCaseCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_case(db, user, project_id, payload)


@router.get('/loads', response_model=list[ElementLoadPublic])
def get_loads(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_loads(db, user, project_id)


@router.post('/loads', response_model=ElementLoadPublic, status_code=status.HTTP_201_CREATED)
def add_load(project_id: UUID, payload: ElementLoadCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_load(db, user, project_id, payload)


@router.put('/loads/{load_id}', response_model=ElementLoadPublic)
def update(project_id: UUID, load_id: UUID, payload: ElementLoadUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_load(db, user, project_id, load_id, payload)


@router.delete('/loads/{load_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(project_id: UUID, load_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_load(db, user, project_id, load_id)
