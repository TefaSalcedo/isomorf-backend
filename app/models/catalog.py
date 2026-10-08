from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaterialCategory(StrEnum):
    CONCRETE = 'concrete'
    STEEL = 'steel'
    MASONRY = 'masonry'
    TIMBER = 'timber'
    ALUMINUM = 'aluminum'
    GENERIC = 'generic'


class Material(Base):
    __tablename__ = 'materials'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[MaterialCategory] = mapped_column(Enum(MaterialCategory, name='material_category', values_callable=lambda enum: [x.value for x in enum]), default=MaterialCategory.GENERIC, nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship('Project')
    sections = relationship('Section', back_populates='material')


class SectionShape(StrEnum):
    RECTANGULAR = 'rectangular'
    CIRCULAR = 'circular'
    I_SHAPE = 'i_shape'
    T_SHAPE = 't_shape'
    L_SHAPE = 'l_shape'
    BOX = 'box'
    PIPE = 'pipe'
    CUSTOM = 'custom'


class Section(Base):
    __tablename__ = 'sections'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    shape: Mapped[SectionShape] = mapped_column(Enum(SectionShape, name='section_shape', values_callable=lambda enum: [x.value for x in enum]), default=SectionShape.RECTANGULAR, nullable=False)
    material_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('materials.id', ondelete='SET NULL'), index=True)
    dimensions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship('Project')
    material = relationship('Material', back_populates='sections')
