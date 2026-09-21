from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LoadType(StrEnum):
    DEAD = 'dead'
    LIVE = 'live'
    POINT = 'point'
    DISTRIBUTED = 'distributed'
    SURFACE = 'surface'
    WIND = 'wind'
    SNOW = 'snow'
    SEISMIC = 'seismic'
    SELF_WEIGHT = 'self_weight'


class LoadCase(Base):
    __tablename__ = 'load_cases'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default='service', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship('Project')
    loads = relationship('ElementLoad', back_populates='load_case', cascade='all, delete-orphan')


class ElementLoad(Base):
    __tablename__ = 'element_loads'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    load_case_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('load_cases.id', ondelete='CASCADE'), index=True, nullable=False)
    element_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey('project_elements.id', ondelete='SET NULL'), index=True)
    load_type: Mapped[LoadType] = mapped_column(String(30), nullable=False)
    magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default='kN/m', nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default='-Y', nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    load_case = relationship('LoadCase', back_populates='loads')
