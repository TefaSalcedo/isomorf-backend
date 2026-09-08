from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserPublic


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class DeviceRegistration(BaseModel):
    key_id: str = Field(min_length=8, max_length=128)
    public_key: str = Field(min_length=20, max_length=4096)
    fingerprint: str = Field(min_length=16, max_length=512)
    device_name: str | None = Field(default=None, max_length=120)


class RegisterWithDevice(RegisterRequest):
    device: DeviceRegistration


class LoginWithDevice(LoginRequest):
    device: DeviceRegistration


class SessionPublic(BaseModel):
    id: str
    key_id: str
    device_name: str | None
    created_at: str
    last_seen_at: str
    is_current: bool


class AuthResponse(BaseModel):
    user: UserPublic
    session_id: str
