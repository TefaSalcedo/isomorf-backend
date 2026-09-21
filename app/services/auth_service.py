from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_value, verify_password
from app.models.device_session import DeviceSession
from app.models.user import User
from app.schemas.auth import DeviceRegistration, RegisterRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def register_user(db: Session, payload: RegisterRequest) -> User:
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email is already registered')
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), first_name=payload.first_name.strip(), last_name=payload.last_name.strip())
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    return user


def create_device_session(db: Session, user: User, device: DeviceRegistration) -> DeviceSession:
    existing = db.scalar(select(DeviceSession).where(DeviceSession.key_id == device.key_id))
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Device key is already registered')
        existing.is_active = True
        existing.revoked_at = None
        existing.revocation_reason = None
        existing.last_seen_at = datetime.now(timezone.utc)
        existing.fingerprint_hash = hash_value(device.fingerprint)
        existing.public_key = device.public_key
        db.commit()
        db.refresh(existing)
        return existing
    session = DeviceSession(user_id=user.id, key_id=device.key_id, public_key=device.public_key, fingerprint_hash=hash_value(device.fingerprint), device_name=device.device_name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
