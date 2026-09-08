from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeviceSession(Base):
    __tablename__ = 'device_sessions'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship('User', back_populates='device_sessions')
    nonces = relationship('DeviceNonce', back_populates='session', cascade='all, delete-orphan')


class DeviceNonce(Base):
    __tablename__ = 'device_nonces'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('device_sessions.id', ondelete='CASCADE'), index=True, nullable=False)
    nonce_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship('DeviceSession', back_populates='nonces')
