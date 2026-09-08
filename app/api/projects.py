from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectPublic, ProjectUpdate
from app.services.project_service import create_project, delete_project, get_project, list_projects, update_project

router = APIRouter(prefix='/api/projects', tags=['projects'])


@router.post('', response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
def create(payload: ProjectCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_project(db, user, payload)


@router.get('', response_model=list[ProjectPublic])
def list_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_projects(db, user)


@router.get('/{project_id}', response_model=ProjectDetail)
def get(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_project(db, user, project_id)


@router.put('/{project_id}', response_model=ProjectPublic)
def update(project_id: UUID, payload: ProjectUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_project(db, user, project_id, payload)


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(project_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_project(db, user, project_id)
