from datetime import datetime, timezone
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.device_session import DeviceSession
from app.models.user import User


def get_current_session(request: Request, db: Session = Depends(get_db), token: str | None = Cookie(default=None, alias='isomorf_session')) -> DeviceSession:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload['sub'])
        session_id = UUID(payload['sid'])
    except (JWTError, KeyError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication token') from error
    session = db.scalar(select(DeviceSession).where(DeviceSession.id == session_id, DeviceSession.user_id == user_id, DeviceSession.is_active.is_(True)))
    if not session or (session.revoked_at and session.revoked_at <= datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session is no longer active')
    return session


def get_current_user(session: DeviceSession = Depends(get_current_session), db: Session = Depends(get_db)) -> User:
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not active')
    return user
