from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def hash_value(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def create_access_token(user_id: UUID, session_id: UUID) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        'sub': str(user_id),
        'sid': str(session_id),
        'iat': now,
        'exp': expires_at,
        'iss': 'isomorf-api',
        'aud': 'isomorf-web',
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm), expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer='isomorf-api',
        audience='isomorf-web',
    )
    return payload


def get_token_subject(token: str) -> tuple[UUID, UUID]:
    try:
        payload = decode_access_token(token)
        return UUID(payload['sub']), UUID(payload['sid'])
    except (JWTError, KeyError, ValueError) as error:
        raise ValueError('Invalid authentication token') from error
