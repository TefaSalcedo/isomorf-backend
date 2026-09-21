from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectDocument(Base):
    """Full snapshot of a project's document at a given revision.

    The snapshot JSONB payload has the shape::

        {
            "elements": [...],          # serialized project_elements rows
            "design_settings": {...},   # projects.design_settings at that revision
            "load_links": {"<element_id>": ["<load_id>", ...]},
        }

    ``load_links`` lets ``apply_snapshot`` re-link ``element_loads`` rows whose
    ``element_id`` was nulled by a later delete.
    """

    __tablename__ = 'project_documents'
    __table_args__ = (UniqueConstraint('project_id', 'revision', name='uq_project_documents_project_revision'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship('Project')
    element_revisions = relationship('ElementRevision', back_populates='document', cascade='all, delete-orphan')


class ElementRevision(Base):
    """Per-element diff attached to a document revision.

    ``operation`` is one of ``baseline``, ``create``, ``update``, ``delete``.
    ``before``/``after`` hold the full serialized element (``after`` is NULL on
    delete, ``before`` is NULL on create/baseline).
    """

    __tablename__ = 'element_revisions'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('project_documents.id', ondelete='CASCADE'), index=True, nullable=False)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    element_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSONB)
    after: Mapped[dict | None] = mapped_column(JSONB)

    document = relationship('ProjectDocument', back_populates='element_revisions')
