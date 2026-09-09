from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderPublic, FolderUpdate
from app.services.folder_service import create_folder, delete_folder, list_folders, update_folder

router = APIRouter(prefix='/api/folders', tags=['folders'])


@router.get('', response_model=list[FolderPublic])
def list_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_folders(db, user)


@router.post('', response_model=FolderPublic, status_code=status.HTTP_201_CREATED)
def create(payload: FolderCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_folder(db, user, payload)


@router.put('/{folder_id}', response_model=FolderPublic)
def update(folder_id: UUID, payload: FolderUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_folder(db, user, folder_id, payload)


@router.delete('/{folder_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(folder_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_folder(db, user, folder_id)
