from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.block import BlockCreate, BlockPublic, BlockUpdate
from app.services.block_service import create_block, delete_block, get_block, list_blocks, update_block

router = APIRouter(prefix='/api/projects/{project_id}/blocks', tags=['blocks'])


@router.get('', response_model=list[BlockPublic])
def list_project_blocks(project_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_blocks(db, user, project_id)


@router.post('', response_model=BlockPublic, status_code=status.HTTP_201_CREATED)
def create_project_block(project_id: UUID, payload: BlockCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return create_block(db, user, project_id, payload)


@router.get('/{block_id}', response_model=BlockPublic)
def get_project_block(project_id: UUID, block_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_block(db, user, project_id, block_id)


@router.put('/{block_id}', response_model=BlockPublic)
def update_project_block(project_id: UUID, block_id: UUID, payload: BlockUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return update_block(db, user, project_id, block_id, payload)


@router.delete('/{block_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_project_block(project_id: UUID, block_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    delete_block(db, user, project_id, block_id)
