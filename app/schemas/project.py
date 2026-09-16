from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.element import ProjectElementPublic


class ProjectCreate(BaseModel):
    name: str = Field(default='Sin nombre', min_length=1, max_length=200)
    description: str = Field(default='', max_length=5000)
    folder_id: UUID | None = None


class MaterialConstants(BaseModel):
    compressive_strength: float | None = Field(default=None, ge=0)
    density: float | None = Field(default=None, ge=0)
    elastic_modulus: float | None = Field(default=None, ge=0)


class PlanLayer(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    color: str = Field(pattern=r'^#[0-9a-fA-F]{6}$')
    visible: bool = True
    locked: bool = False


class DesignSettings(BaseModel):
    unit: str | None = Field(default=None, max_length=10)
    seismic_zone: str | None = Field(default=None, max_length=100)
    hail_zone: str | None = Field(default=None, max_length=100)
    wind_zone: str | None = Field(default=None, max_length=100)
    building_code: str | None = Field(default=None, max_length=200)
    material: MaterialConstants | None = Field(default_factory=MaterialConstants)
    layers: list[PlanLayer] | None = Field(default=None, max_length=50)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    folder_id: UUID | None = None
    design_settings: DesignSettings | None = None


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    public_id: str
    folder_id: UUID | None
    name: str
    description: str
    design_settings: dict
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectPublic):
    elements: list[ProjectElementPublic] = []
