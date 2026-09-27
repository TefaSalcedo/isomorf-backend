from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.team import TeamRole
from app.schemas.project import ProjectPublic

MemberRole = TeamRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class TeamUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class TeamMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    role: TeamRole
    created_at: datetime


class TeamPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    owner_id: UUID
    my_role: TeamRole
    member_count: int
    project_count: int
    created_at: datetime
    updated_at: datetime


class TeamDetail(TeamPublic):
    members: list[TeamMemberPublic]
    projects: list[ProjectPublic]
    invites: list['TeamInvitePublic']


class InviteCreate(BaseModel):
    email: EmailStr | None = None
    role: TeamRole = TeamRole.VIEWER
    expires_in_days: int = Field(default=7, ge=1, le=90)


class TeamInvitePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    email: str | None
    role: TeamRole
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class TeamInviteCreated(TeamInvitePublic):
    token: str
    accept_url: str


class InvitePreview(BaseModel):
    team_id: UUID
    team_name: str
    role: TeamRole
    email: str | None
    expires_at: datetime
    invited_by: str


class InviteAccept(BaseModel):
    token: str = Field(min_length=16, max_length=128)


class MemberRoleUpdate(BaseModel):
    role: TeamRole


class ProjectShareCreate(BaseModel):
    project_id: UUID


class ProjectSharePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    team_id: UUID
    created_at: datetime
