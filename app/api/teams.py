from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.device import require_device_proof
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.team import (
    InviteAccept,
    InviteCreate,
    InvitePreview,
    MemberRoleUpdate,
    ProjectShareCreate,
    ProjectSharePublic,
    TeamCreate,
    TeamDetail,
    TeamInviteCreated,
    TeamMemberPublic,
    TeamPublic,
    TeamUpdate,
)
from app.services import team_service

router = APIRouter(prefix='/api/teams', tags=['teams'])


@router.post('', response_model=TeamPublic, status_code=status.HTTP_201_CREATED)
def create(payload: TeamCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.create_team(db, user, payload)


@router.get('', response_model=list[TeamPublic])
def list_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return team_service.list_teams(db, user)


@router.get('/invites/{token}', response_model=InvitePreview)
def preview_invite(token: str, db: Session = Depends(get_db)):
    return team_service.preview_invite(db, token)


@router.post('/invites/accept', response_model=TeamPublic)
def accept_invite(payload: InviteAccept, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.accept_invite(db, user, payload.token)


@router.get('/{team_id}', response_model=TeamDetail)
def detail(team_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return team_service.team_detail(db, user, team_id)


@router.put('/{team_id}', response_model=TeamPublic)
def update(team_id: UUID, payload: TeamUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.update_team(db, user, team_id, payload)


@router.delete('/{team_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete(team_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    team_service.delete_team(db, user, team_id)


@router.post('/{team_id}/invites', response_model=TeamInviteCreated, status_code=status.HTTP_201_CREATED)
def create_invite(team_id: UUID, payload: InviteCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.create_invite(db, user, team_id, payload)


@router.delete('/{team_id}/invites/{invite_id}', status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(team_id: UUID, invite_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    team_service.revoke_invite(db, user, team_id, invite_id)


@router.patch('/{team_id}/members/{member_id}/role', response_model=TeamMemberPublic)
def update_member_role(team_id: UUID, member_id: UUID, payload: MemberRoleUpdate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.update_member_role(db, user, team_id, member_id, payload.role)


@router.delete('/{team_id}/members/{member_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_member(team_id: UUID, member_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    team_service.remove_member(db, user, team_id, member_id)


@router.post('/{team_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
def leave(team_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    team_service.leave_team(db, user, team_id)


@router.post('/{team_id}/projects', response_model=ProjectSharePublic, status_code=status.HTTP_201_CREATED)
def share_project(team_id: UUID, payload: ProjectShareCreate, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    return team_service.share_project(db, user, team_id, payload)


@router.delete('/{team_id}/projects/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
def unshare_project(team_id: UUID, project_id: UUID, user: User = Depends(get_current_user), _: DeviceSession = Depends(require_device_proof), db: Session = Depends(get_db)):
    team_service.unshare_project(db, user, team_id, project_id)
