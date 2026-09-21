from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.document import DocumentPayload, DocumentState, HistoryResponse
from app.services.document_service import get_history, redo_document, restore_revision, save_document, undo_document

router = APIRouter(prefix='/api/projects/{project_id}', tags=['documents'])


@router.put('/document', response_model=DocumentState)
def save(project_id: UUID, payload: DocumentPayload, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return save_document(db, user, project_id, payload)


@router.get('/history', response_model=HistoryResponse)
def history(project_id: UUID, limit: int = Query(default=100, ge=1, le=500), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_history(db, user, project_id, limit)


@router.post('/history/undo', response_model=DocumentState)
def undo(project_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return undo_document(db, user, project_id)


@router.post('/history/redo', response_model=DocumentState)
def redo(project_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return redo_document(db, user, project_id)


@router.post('/history/{revision}/restore', response_model=DocumentState)
def restore(project_id: UUID, revision: int, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return restore_revision(db, user, project_id, revision)
