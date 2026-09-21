import base64
import json
import time
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_value
from app.dependencies.auth import get_current_session
from app.models.device_session import DeviceNonce, DeviceSession


def decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def public_key_from_jwk(value: str):
    data = json.loads(value)
    if data.get('kty') != 'EC' or data.get('crv') != 'P-256':
        raise ValueError('Unsupported public key')
    x = int.from_bytes(decode_base64url(data['x']), 'big')
    y = int.from_bytes(decode_base64url(data['y']), 'big')
    return ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()


def raw_ecdsa_signature_to_der(value: bytes) -> bytes:
    if len(value) != 64:
        raise ValueError('Unsupported signature length')
    r = int.from_bytes(value[:32], 'big')
    s = int.from_bytes(value[32:], 'big')
    return encode_dss_signature(r, s)


def require_device_proof(
    request: Request,
    session: DeviceSession = Depends(get_current_session),
    db: Session = Depends(get_db),
    key_id: str | None = Header(default=None, alias='X-Device-Key-Id'),
    timestamp: str | None = Header(default=None, alias='X-Device-Timestamp'),
    nonce: str | None = Header(default=None, alias='X-Device-Nonce'),
    signature: str | None = Header(default=None, alias='X-Device-Signature'),
) -> DeviceSession:
    if key_id is None or timestamp is None or nonce is None or signature is None or key_id != session.key_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Device proof required')
    try:
        timestamp_value = int(timestamp)
        if abs(int(time.time()) - timestamp_value) > 90:
            raise ValueError('Expired proof')
        canonical = f'{request.method}:{request.url.path}:{timestamp}:{nonce}'.encode()
        public_key = public_key_from_jwk(session.public_key)
        public_key.verify(raw_ecdsa_signature_to_der(decode_base64url(signature)), canonical, ec.ECDSA(hashes.SHA256()))
        nonce_hash = hash_value(nonce)
        if db.scalar(select(DeviceNonce).where(DeviceNonce.nonce_hash == nonce_hash)):
            raise ValueError('Nonce reused')
        db.add(DeviceNonce(session_id=session.id, nonce_hash=nonce_hash))
        session.last_seen_at = datetime.now(timezone.utc)
        db.commit()
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, IntegrityError, Exception) as error:
        db.rollback()
        if isinstance(error, HTTPException):
            raise
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid device proof') from error
    return session
