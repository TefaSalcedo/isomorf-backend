"""Device proof verification: signature, freshness and nonce replay rules."""

import base64
import time
import uuid

from conftest import DeviceIdentity, _register

PATH = '/api/folders'
PAYLOAD = {'name': 'Proof folder'}


class TestDeviceProof:
    def test_valid_proof_is_accepted(self, registered):
        response = registered.signed_post(PATH, json=PAYLOAD)
        assert response.status_code == 201

    def test_missing_headers_returns_401(self, registered):
        response = registered.client.post(PATH, json=PAYLOAD)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Device proof required'

    def test_key_id_mismatch_returns_401(self, registered):
        other_device = DeviceIdentity()
        response = registered.client.post(PATH, json=PAYLOAD, headers=other_device.proof_headers('POST', PATH))
        assert response.status_code == 401

    def test_invalid_signature_returns_401(self, registered):
        fake_signature = base64.urlsafe_b64encode(b'\x00' * 64).rstrip(b'=').decode()
        headers = registered.device.proof_headers('POST', PATH, signature=fake_signature)
        response = registered.client.post(PATH, json=PAYLOAD, headers=headers)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Invalid device proof'

    def test_expired_timestamp_returns_401(self, registered):
        headers = registered.device.proof_headers('POST', PATH, timestamp=int(time.time()) - 120)
        response = registered.client.post(PATH, json=PAYLOAD, headers=headers)
        assert response.status_code == 401

    def test_nonce_reuse_returns_401(self, registered):
        nonce = uuid.uuid4().hex
        first = registered.client.post(PATH, json=PAYLOAD, headers=registered.device.proof_headers('POST', PATH, nonce=nonce))
        assert first.status_code == 201

        second = registered.client.post(PATH, json=PAYLOAD, headers=registered.device.proof_headers('POST', PATH, nonce=nonce))
        assert second.status_code == 401

    def test_nonce_is_globally_unique(self, make_client):
        user_a = _register(make_client())
        user_b = _register(make_client())
        nonce = uuid.uuid4().hex

        first = user_a.client.post(PATH, json=PAYLOAD, headers=user_a.device.proof_headers('POST', PATH, nonce=nonce))
        second = user_b.client.post(PATH, json=PAYLOAD, headers=user_b.device.proof_headers('POST', PATH, nonce=nonce))
        assert first.status_code == 201
        assert second.status_code == 401


class TestRevokedSession:
    def test_revoked_session_rejects_requests(self, registered):
        session_token = registered.client.cookies.get('isomorf_session')
        second_device = DeviceIdentity()
        login = registered.client.post(
            '/api/auth/login',
            json={'email': registered.email, 'password': registered.password, 'device': second_device.registration},
        )
        assert login.status_code == 200

        registered.client.delete(f'/api/auth/sessions/{registered.session_id}')
        registered.client.cookies.set('isomorf_session', session_token)
        response = registered.client.post(PATH, json=PAYLOAD, headers=registered.device.proof_headers('POST', PATH))
        assert response.status_code == 401
        assert response.json()['detail'] == 'Session is no longer active'
