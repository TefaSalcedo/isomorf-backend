"""Auth endpoints: register, login, logout, me, session listing/revocation."""

import uuid

from conftest import DeviceIdentity, _register

SESSION_COOKIE = 'isomorf_session'
HINT_COOKIE = 'isomorf_auth_hint'


def _register_payload(device: DeviceIdentity, email: str = 'alice@example.com') -> dict:
    return {
        'email': email,
        'password': 'super-secret-1',
        'first_name': 'Alice',
        'last_name': 'Engineer',
        'device': device.registration,
    }


class TestRegister:
    def test_creates_user_session_and_cookies(self, client):
        response = client.post('/api/auth/register', json=_register_payload(DeviceIdentity()))
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['user']['email'] == 'alice@example.com'
        assert data['user']['first_name'] == 'Alice'
        assert data['session_id']
        assert client.cookies.get(SESSION_COOKIE)
        assert client.cookies.get(HINT_COOKIE) == '1'

    def test_duplicate_email_returns_409(self, client):
        client.post('/api/auth/register', json=_register_payload(DeviceIdentity()))
        response = client.post('/api/auth/register', json=_register_payload(DeviceIdentity()))
        assert response.status_code == 409
        assert response.json()['detail'] == 'Email is already registered'

    def test_email_is_normalized_to_lowercase(self, client):
        response = client.post('/api/auth/register', json=_register_payload(DeviceIdentity(), email='Alice@Example.COM'))
        assert response.status_code == 201
        assert response.json()['user']['email'] == 'alice@example.com'

    def test_device_key_owned_by_other_user_returns_409(self, client):
        device = DeviceIdentity()
        client.post('/api/auth/register', json=_register_payload(device, 'alice@example.com'))
        response = client.post('/api/auth/register', json=_register_payload(device, 'bob@example.com'))
        assert response.status_code == 409
        assert response.json()['detail'] == 'Device key is already registered'


class TestLogin:
    def test_login_issues_new_session_and_cookies(self, registered):
        response = registered.client.post(
            '/api/auth/login',
            json={'email': registered.email, 'password': registered.password, 'device': DeviceIdentity().registration},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['user']['email'] == registered.email
        assert data['session_id'] != registered.session_id
        assert registered.client.cookies.get(SESSION_COOKIE)
        assert registered.client.cookies.get(HINT_COOKIE) == '1'

    def test_login_with_same_device_reuses_session(self, registered):
        response = registered.client.post(
            '/api/auth/login',
            json={'email': registered.email, 'password': registered.password, 'device': registered.device.registration},
        )
        assert response.status_code == 200
        assert response.json()['session_id'] == registered.session_id

    def test_wrong_password_returns_401(self, registered):
        response = registered.client.post(
            '/api/auth/login',
            json={'email': registered.email, 'password': 'wrong-password', 'device': DeviceIdentity().registration},
        )
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, client):
        response = client.post(
            '/api/auth/login',
            json={'email': 'ghost@example.com', 'password': 'super-secret-1', 'device': DeviceIdentity().registration},
        )
        assert response.status_code == 401


class TestMe:
    def test_returns_current_user(self, registered):
        response = registered.client.get('/api/auth/me')
        assert response.status_code == 200
        assert response.json()['email'] == registered.email

    def test_requires_authentication(self, client):
        assert client.get('/api/auth/me').status_code == 401

    def test_rejects_invalid_token(self, client):
        client.cookies.set(SESSION_COOKIE, 'not-a-jwt')
        assert client.get('/api/auth/me').status_code == 401


class TestLogout:
    def test_revokes_session_and_clears_cookies(self, registered):
        response = registered.client.post('/api/auth/logout')
        assert response.status_code == 204
        set_cookies = response.headers.get_list('set-cookie')
        assert any(header.startswith(f'{SESSION_COOKIE}=') for header in set_cookies)
        assert any(header.startswith(f'{HINT_COOKIE}=') for header in set_cookies)
        assert registered.client.get('/api/auth/me').status_code == 401

    def test_requires_authentication(self, client):
        assert client.post('/api/auth/logout').status_code == 401


class TestSessions:
    def test_lists_active_sessions_flagging_current(self, registered):
        second_device = DeviceIdentity()
        login = registered.client.post(
            '/api/auth/login',
            json={'email': registered.email, 'password': registered.password, 'device': second_device.registration},
        )
        assert login.status_code == 200
        current_id = login.json()['session_id']

        response = registered.client.get('/api/auth/sessions')
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) == 2
        current = [item for item in sessions if item['is_current']]
        assert len(current) == 1
        assert current[0]['id'] == current_id
        assert current[0]['key_id'] == second_device.key_id

    def test_revoke_session(self, registered):
        revoke = registered.client.delete(f'/api/auth/sessions/{registered.session_id}')
        assert revoke.status_code == 204
        assert registered.client.get('/api/auth/me').status_code == 401

    def test_revoke_unknown_session_returns_404(self, registered):
        assert registered.client.delete(f'/api/auth/sessions/{uuid.uuid4()}').status_code == 404

    def test_revoke_other_users_session_returns_404(self, make_client):
        user_a = _register(make_client())
        user_b = _register(make_client())
        response = user_b.client.delete(f'/api/auth/sessions/{user_a.session_id}')
        assert response.status_code == 404
        assert user_a.client.get('/api/auth/me').status_code == 200
