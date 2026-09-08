from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ElementType(StrEnum):
    WALL = 'wall'
    DOOR = 'door'
    WINDOW = 'window'
    COLUMN = 'column'
    BEAM = 'beam'


class ElementPayload(BaseModel):
    id: UUID | None = None
    element_type: ElementType
    x1: float
    y1: float
    x2: float
    y2: float
    length: float = Field(gt=0)
    rotation: float = 0
    properties: dict = {}

    @model_validator(mode='after')
    def validate_coordinates(self):
        if self.x1 == self.x2 and self.y1 == self.y2:
            raise ValueError('Element endpoints must be different')
        return self


class ElementUpdate(BaseModel):
    element_type: ElementType | None = None
    x1: float | None = None
    y1: float | None = None
    x2: float | None = None
    y2: float | None = None
    length: float | None = Field(default=None, gt=0)
    rotation: float | None = None
    properties: dict | None = None


class ProjectElementPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    element_type: ElementType
    x1: float
    y1: float
    x2: float
    y2: float
    length: float
    rotation: float
    properties: dict
    created_at: datetime
    updated_at: datetime
