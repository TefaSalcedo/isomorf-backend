from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.models.project import Project
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderUpdate


def get_folder(db: Session, user: User, folder_id: UUID) -> Folder:
    folder = db.scalar(select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id))
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Folder not found')
    return folder


def list_folders(db: Session, user: User) -> list[Folder]:
    return list(db.scalars(select(Folder).where(Folder.user_id == user.id).order_by(Folder.name)).all())


def create_folder(db: Session, user: User, payload: FolderCreate) -> Folder:
    folder = Folder(user_id=user.id, name=payload.name.strip())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def update_folder(db: Session, user: User, folder_id: UUID, payload: FolderUpdate) -> Folder:
    folder = get_folder(db, user, folder_id)
    folder.name = payload.name.strip()
    db.commit()
    db.refresh(folder)
    return folder


def delete_folder(db: Session, user: User, folder_id: UUID) -> None:
    folder = get_folder(db, user, folder_id)
    db.query(Project).filter(Project.folder_id == folder.id).update({Project.folder_id: None})
    db.delete(folder)
    db.commit()
