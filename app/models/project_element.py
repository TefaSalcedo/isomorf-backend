from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ElementType(StrEnum):
    WALL = 'wall'
    DOOR = 'door'
    WINDOW = 'window'
    COLUMN = 'column'
    BEAM = 'beam'


class ProjectElement(Base):
    __tablename__ = 'project_elements'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    element_type: Mapped[ElementType] = mapped_column(Enum(ElementType, name='element_type', values_callable=lambda enum: [x.value for x in enum]), nullable=False)
    x1: Mapped[float] = mapped_column(Float, nullable=False)
    y1: Mapped[float] = mapped_column(Float, nullable=False)
    x2: Mapped[float] = mapped_column(Float, nullable=False)
    y2: Mapped[float] = mapped_column(Float, nullable=False)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    rotation: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship('Project', back_populates='elements')
