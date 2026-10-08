from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MaterialCategory(StrEnum):
    CONCRETE = 'concrete'
    STEEL = 'steel'
    MASONRY = 'masonry'
    TIMBER = 'timber'
    ALUMINUM = 'aluminum'
    GENERIC = 'generic'


class MaterialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: MaterialCategory = MaterialCategory.GENERIC
    properties: dict = Field(default_factory=dict)


class MaterialUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: MaterialCategory | None = None
    properties: dict | None = None


class MaterialPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    category: MaterialCategory
    properties: dict
    created_at: datetime
    updated_at: datetime


class SectionShape(StrEnum):
    RECTANGULAR = 'rectangular'
    CIRCULAR = 'circular'
    I_SHAPE = 'i_shape'
    T_SHAPE = 't_shape'
    L_SHAPE = 'l_shape'
    BOX = 'box'
    PIPE = 'pipe'
    CUSTOM = 'custom'


class SectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    shape: SectionShape = SectionShape.RECTANGULAR
    material_id: UUID | None = None
    dimensions: dict = Field(default_factory=dict)
    properties: dict = Field(default_factory=dict)


class SectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    shape: SectionShape | None = None
    material_id: UUID | None = None
    dimensions: dict | None = None
    properties: dict | None = None


class SectionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    shape: SectionShape
    material_id: UUID | None
    dimensions: dict
    properties: dict
    created_at: datetime
    updated_at: datetime


class CatalogPreset(BaseModel):
    """A read-only catalog entry an element can reference as ``preset:<key>``
    or copy into the project as a regular material/section."""
    key: str
    name: str
    category: str | None = None
    shape: str | None = None
    properties: dict = {}
    dimensions: dict = {}


class CatalogPresets(BaseModel):
    materials: list[CatalogPreset]
    sections: list[CatalogPreset]
