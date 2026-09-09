from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class LoadCaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default='service', max_length=50)


class LoadCasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    category: str
    created_at: datetime
    updated_at: datetime


class ElementLoadCreate(BaseModel):
    load_case_id: UUID
    element_id: UUID | None = None
    load_type: LoadType
    magnitude: float
    unit: str = Field(default='kN/m', max_length=30)
    direction: str = Field(default='-Y', max_length=20)
    position: dict = Field(default_factory=dict)


class ElementLoadUpdate(BaseModel):
    element_id: UUID | None = None
    load_type: LoadType | None = None
    magnitude: float | None = None
    unit: str | None = Field(default=None, max_length=30)
    direction: str | None = Field(default=None, max_length=20)
    position: dict | None = None


class ElementLoadPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    load_case_id: UUID
    element_id: UUID | None
    load_type: LoadType
    magnitude: float
    unit: str
    direction: str
    position: dict
    created_at: datetime
