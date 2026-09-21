from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.element import ElementPayload, ProjectElementPublic
from app.schemas.project import DesignSettings


class DocumentPayload(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    design_settings: DesignSettings | None = None
    elements: list[ElementPayload] = Field(default_factory=list)


class DocumentState(BaseModel):
    revision: int
    head_revision: int
    can_undo: bool
    can_redo: bool
    elements: list[ProjectElementPublic]
    design_settings: dict


class RevisionChange(BaseModel):
    element_id: UUID
    operation: str
    before: dict | None = None
    after: dict | None = None


class RevisionEntry(BaseModel):
    revision: int
    created_at: datetime
    changes: list[RevisionChange] = []


class HistoryResponse(BaseModel):
    current_revision: int
    head_revision: int
    revisions: list[RevisionEntry]
