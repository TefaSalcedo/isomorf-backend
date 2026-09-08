from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str = Field(alias='DATABASE_URL')
    jwt_secret_key: str = Field(alias='JWT_SECRET_KEY')
    jwt_algorithm: str = Field(default='HS256', alias='JWT_ALGORITHM')
    access_token_expire_minutes: int = Field(default=15, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    refresh_token_expire_days: int = Field(default=30, alias='REFRESH_TOKEN_EXPIRE_DAYS')
    frontend_url: str = Field(default='http://localhost:3000', alias='FRONTEND_URL')
    cookie_secure: bool = Field(default=False, alias='COOKIE_SECURE')
    cookie_samesite: str = Field(default='lax', alias='COOKIE_SAMESITE')
    cookie_name: str = Field(default='isomorf_session', alias='COOKIE_NAME')
    refresh_cookie_name: str = Field(default='isomorf_refresh', alias='REFRESH_COOKIE_NAME')
    device_proof_max_age_seconds: int = Field(default=90, alias='DEVICE_PROOF_MAX_AGE_SECONDS')


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
