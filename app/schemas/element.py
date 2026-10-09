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
    SLAB = 'slab'
    FOOTING = 'footing'
    STAIR = 'stair'
    RAMP = 'ramp'
    OPENING = 'opening'
    JOIST = 'joist'
    GRADE_BEAM = 'grade_beam'
    BRACE = 'brace'
    PILE = 'pile'
    LINE = 'line'
    POLYLINE = 'polyline'
    ARC = 'arc'
    CIRCLE = 'circle'
    ELLIPSE = 'ellipse'
    RECTANGLE = 'rectangle'
    HATCH = 'hatch'


class ElementPayload(BaseModel):
    id: UUID | None = None
    element_type: ElementType
    x1: float
    y1: float
    x2: float
    y2: float
    length: float = Field(gt=0)
    rotation: float = 0
    material_id: UUID | None = None
    section_id: UUID | None = None
    properties: dict = {}

    @model_validator(mode='after')
    def validate_coordinates(self):
        # Closed polylines legitimately share their first and last vertex.
        if self.element_type == ElementType.POLYLINE:
            return self
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
    material_id: UUID | None = None
    section_id: UUID | None = None
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
    material_id: UUID | None
    section_id: UUID | None
    properties: dict
    created_at: datetime
    updated_at: datetime
