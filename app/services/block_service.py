from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.block import ProjectBlock
from app.models.project_element import ElementType, ProjectElement
from app.models.team import TeamRole
from app.models.user import User
from app.schemas.block import BlockCreate, BlockUpdate
from app.services.access_service import get_accessible_project


def list_blocks(db: Session, user: User, project_id: UUID) -> list[ProjectBlock]:
    get_accessible_project(db, user, project_id)
    return list(db.scalars(select(ProjectBlock).where(ProjectBlock.project_id == project_id).order_by(ProjectBlock.name)).all())


def get_block(db: Session, user: User, project_id: UUID, block_id: UUID, minimum: TeamRole = TeamRole.VIEWER) -> ProjectBlock:
    get_accessible_project(db, user, project_id, minimum)
    block = db.scalar(select(ProjectBlock).where(ProjectBlock.id == block_id, ProjectBlock.project_id == project_id))
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Block not found')
    return block


def create_block(db: Session, user: User, project_id: UUID, payload: BlockCreate) -> ProjectBlock:
    get_accessible_project(db, user, project_id, TeamRole.EDITOR)
    block = ProjectBlock(project_id=project_id, **payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def update_block(db: Session, user: User, project_id: UUID, block_id: UUID, payload: BlockUpdate) -> ProjectBlock:
    block = get_block(db, user, project_id, block_id, TeamRole.EDITOR)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(block, key, value)
    db.commit()
    db.refresh(block)
    return block


def delete_block(db: Session, user: User, project_id: UUID, block_id: UUID) -> None:
    block = get_block(db, user, project_id, block_id, TeamRole.EDITOR)
    refs = db.scalar(
        select(ProjectElement.id).where(
            ProjectElement.project_id == project_id,
            ProjectElement.element_type == ElementType.BLOCK_REF,
            ProjectElement.properties['block_id'].astext == str(block_id),
        ).limit(1)
    )
    if refs:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Block is in use by block_ref elements')
    db.delete(block)
    db.commit()
