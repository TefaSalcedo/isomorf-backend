from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.element import ElementType


class BlockItem(BaseModel):
    """One element inside a block definition, stored in world plan
    coordinates (centimeters). ``base_x``/``base_y`` on the definition
    marks the insertion anchor the client subtracts when instantiating."""

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


class BlockCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=5000)
    base_x: float = 0
    base_y: float = 0
    items: list[BlockItem] = Field(min_length=1, max_length=500)


class BlockUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    base_x: float | None = None
    base_y: float | None = None
    items: list[BlockItem] | None = Field(default=None, min_length=1, max_length=500)


class BlockPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str
    base_x: float
    base_y: float
    items: list[BlockItem]
    created_at: datetime
    updated_at: datetime
