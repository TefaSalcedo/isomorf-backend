from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.dependencies.auth import get_current_session, get_current_user
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginWithDevice, RegisterWithDevice, SessionPublic
from app.schemas.user import UserPublic
from app.services.auth_service import authenticate_user, create_device_session, register_user

router = APIRouter(prefix='/api/auth', tags=['auth'])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(settings.cookie_name, token, httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite, max_age=settings.access_token_expire_minutes * 60, path='/')


def issue_session(response: Response, session: DeviceSession) -> AuthResponse:
    token, _ = create_access_token(session.user_id, session.id)
    set_session_cookie(response, token)
    return AuthResponse(user=UserPublic.model_validate(session.user), session_id=str(session.id))


@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterWithDevice, response: Response, db: Session = Depends(get_db)):
    user = register_user(db, payload)
    session = create_device_session(db, user, payload.device)
    return issue_session(response, session)


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginWithDevice, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    session = create_device_session(db, user, payload.device)
    return issue_session(response, session)


@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, session: DeviceSession = Depends(get_current_session), db: Session = Depends(get_db)):
    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    session.revocation_reason = 'logout'
    db.commit()
    response.delete_cookie(settings.cookie_name, path='/')


@router.get('/me', response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return user


@router.get('/sessions', response_model=list[SessionPublic])
def sessions(current: DeviceSession = Depends(get_current_session), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.scalars(select(DeviceSession).where(DeviceSession.user_id == user.id, DeviceSession.is_active.is_(True)).order_by(DeviceSession.last_seen_at.desc())).all()
    return [SessionPublic(id=str(item.id), key_id=item.key_id, device_name=item.device_name, created_at=item.created_at.isoformat(), last_seen_at=item.last_seen_at.isoformat(), is_current=item.id == current.id) for item in records]


@router.delete('/sessions/{session_id}', status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.scalar(select(DeviceSession).where(DeviceSession.id == session_id, DeviceSession.user_id == user.id, DeviceSession.is_active.is_(True)))
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    session.revocation_reason = 'revoked_by_user'
    db.commit()
