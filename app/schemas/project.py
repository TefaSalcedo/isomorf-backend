from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    linetype: str | None = Field(default=None, max_length=20)
    lineweight: float | None = Field(default=None, ge=0.05, le=2.0)


class DimStyle(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    text_height: float = Field(gt=0, le=50)
    arrow: Literal['arrow', 'tick', 'dot']
    arrow_size: float = Field(gt=0, le=50)
    ext_offset: float = Field(ge=0, le=50)
    ext_extend: float = Field(ge=0, le=50)
    decimals: int = Field(ge=0, le=6)
    unit: Literal['m', 'cm', 'mm']
    angle_decimals: int = Field(ge=0, le=4)


class DesignSettings(BaseModel):
    unit: str | None = Field(default=None, max_length=10)
    seismic_zone: str | None = Field(default=None, max_length=100)
    hail_zone: str | None = Field(default=None, max_length=100)
    wind_zone: str | None = Field(default=None, max_length=100)
    building_code: str | None = Field(default=None, max_length=200)
    material: MaterialConstants | None = Field(default_factory=MaterialConstants)
    layers: list[PlanLayer] | None = Field(default=None, max_length=50)
    annotation_scale: float | None = Field(default=None, gt=0, le=10000)
    dim_styles: list[DimStyle] | None = Field(default=None, max_length=30)
    active_dim_style_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode='after')
    def validate_dim_styles(self):
        if self.dim_styles is None:
            return self

        style_ids = [style.id for style in self.dim_styles]
        if len(style_ids) != len(set(style_ids)):
            raise ValueError('DIM style IDs must be unique')
        if self.active_dim_style_id is not None and self.active_dim_style_id not in style_ids:
            raise ValueError('Active DIM style ID must exist in DIM styles')
        return self


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
    access_role: str = 'owner'


class ProjectDetail(ProjectPublic):
    elements: list[ProjectElementPublic] = []
    current_revision: int = 0
    head_revision: int = 0
