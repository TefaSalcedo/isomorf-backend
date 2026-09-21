"""Pytest fixtures for the ISOMORF API test suite.

Tests run against a dedicated PostgreSQL database. The URL is taken from
TEST_DATABASE_URL, or derived from DATABASE_URL by swapping the database name
for ``isomorf_test``. The database is created if missing and migrated with
Alembic once per session; every test runs inside a transaction that is rolled
back afterwards.
"""

import base64
import json
import os
import time
import uuid
from collections.abc import Generator
from pathlib import Path

# Environment must be configured before importing any app module: the engine
# and settings are created at import time.
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key')
os.environ.setdefault('FRONTEND_URL', 'http://localhost:3000')

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL')
if not TEST_DATABASE_URL:
    base_url = os.environ.get('DATABASE_URL', 'postgresql+psycopg://isomorf:isomorf@localhost:5432/isomorf')
    TEST_DATABASE_URL = base_url.rsplit('/', 1)[0] + '/isomorf_test'
os.environ['DATABASE_URL'] = TEST_DATABASE_URL

import psycopg  # noqa: E402
import pytest  # noqa: E402
from cryptography.hazmat.primitives import hashes  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _ensure_database(url: str) -> None:
    parsed = make_url(url)
    conninfo = (
        f"host={parsed.host} port={parsed.port or 5432} dbname=postgres "
        f"user={parsed.username} password={parsed.password}"
    )
    with psycopg.connect(conninfo, autocommit=True) as connection:
        exists = connection.execute('SELECT 1 FROM pg_database WHERE datname = %s', (parsed.database,)).fetchone()
        if not exists:
            connection.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(parsed.database)))


@pytest.fixture(scope='session', autouse=True)
def _migrated_database() -> Generator[None]:
    _ensure_database(TEST_DATABASE_URL)
    from alembic import command
    from alembic.config import Config

    alembic_config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    command.upgrade(alembic_config, 'head')
    yield


@pytest.fixture()
def db_session(_migrated_database: None) -> Generator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode='create_savepoint')
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def make_client(db_session: Session) -> Generator:
    """Factory of TestClients that share the rolled-back session but keep
    independent cookie jars, so tests can act as different users."""
    clients: list[TestClient] = []

    def _override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    def _make() -> TestClient:
        test_client = TestClient(app)
        clients.append(test_client)
        return test_client

    yield _make

    for test_client in clients:
        test_client.close()
    app.dependency_overrides.clear()


@pytest.fixture()
def client(make_client) -> TestClient:
    return make_client()


class DeviceIdentity:
    """ECDSA P-256 device identity that mirrors lib/device/identity.ts."""

    def __init__(self) -> None:
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        numbers = self.private_key.public_key().public_numbers()
        self.key_id = str(uuid.uuid4())
        self.public_key_jwk = json.dumps(
            {
                'kty': 'EC',
                'crv': 'P-256',
                'x': _b64url(numbers.x.to_bytes(32, 'big')),
                'y': _b64url(numbers.y.to_bytes(32, 'big')),
            }
        )
        self.fingerprint = uuid.uuid4().hex + uuid.uuid4().hex

    @property
    def registration(self) -> dict[str, str]:
        return {
            'key_id': self.key_id,
            'public_key': self.public_key_jwk,
            'fingerprint': self.fingerprint,
            'device_name': 'pytest-device',
        }

    def proof_headers(self, method: str, path: str, *, timestamp: int | None = None, nonce: str | None = None, signature: str | None = None) -> dict[str, str]:
        timestamp_value = str(timestamp if timestamp is not None else int(time.time()))
        nonce_value = nonce or uuid.uuid4().hex
        if signature is None:
            canonical = f'{method}:{path}:{timestamp_value}:{nonce_value}'.encode()
            der_signature = self.private_key.sign(canonical, ec.ECDSA(hashes.SHA256()))
            r, s = decode_dss_signature(der_signature)
            signature = _b64url(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))
        return {
            'X-Device-Key-Id': self.key_id,
            'X-Device-Timestamp': timestamp_value,
            'X-Device-Nonce': nonce_value,
            'X-Device-Signature': signature,
        }


class RegisteredClient:
    """TestClient wrapper for a registered user, with signed request helpers."""

    def __init__(self, client: TestClient, device: DeviceIdentity, email: str, password: str, data: dict) -> None:
        self.client = client
        self.device = device
        self.email = email
        self.password = password
        self.data = data

    @property
    def user(self) -> dict:
        return self.data['user']

    @property
    def session_id(self) -> str:
        return self.data['session_id']

    def signed(self, method: str, path: str, **kwargs):
        headers = {**self.device.proof_headers(method, path), **kwargs.pop('headers', {})}
        return self.client.request(method, path, headers=headers, **kwargs)

    def signed_post(self, path: str, **kwargs):
        return self.signed('POST', path, **kwargs)

    def signed_put(self, path: str, **kwargs):
        return self.signed('PUT', path, **kwargs)

    def signed_delete(self, path: str, **kwargs):
        return self.signed('DELETE', path, **kwargs)


def _register(client: TestClient) -> RegisteredClient:
    device = DeviceIdentity()
    email = f'user-{uuid.uuid4().hex[:8]}@example.com'
    password = 'test-password-123'
    response = client.post(
        '/api/auth/register',
        json={
            'email': email,
            'password': password,
            'first_name': 'Test',
            'last_name': 'User',
            'device': device.registration,
        },
    )
    assert response.status_code == 201, response.text
    return RegisteredClient(client, device, email, password, response.json())


@pytest.fixture()
def registered(client: TestClient) -> RegisteredClient:
    return _register(client)
