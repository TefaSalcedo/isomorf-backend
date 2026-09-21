"""Folder CRUD endpoints and ownership rules."""

import uuid

from conftest import _register


class TestCreate:
    def test_creates_folder(self, registered):
        response = registered.signed_post('/api/folders', json={'name': 'Structural models'})
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['name'] == 'Structural models'
        assert data['project_count'] == 0

    def test_requires_device_proof(self, registered):
        assert registered.client.post('/api/folders', json={'name': 'x'}).status_code == 401

    def test_requires_authentication(self, client):
        assert client.post('/api/folders', json={'name': 'x'}).status_code == 401


class TestList:
    def test_lists_only_own_folders(self, make_client):
        user_a = _register(make_client())
        user_b = _register(make_client())
        user_a.signed_post('/api/folders', json={'name': 'A folder'})
        user_b.signed_post('/api/folders', json={'name': 'B folder'})

        folders = user_a.client.get('/api/folders').json()
        assert [item['name'] for item in folders] == ['A folder']


class TestUpdate:
    def test_renames_folder(self, registered):
        folder = registered.signed_post('/api/folders', json={'name': 'Old'}).json()
        response = registered.signed_put(f"/api/folders/{folder['id']}", json={'name': 'New'})
        assert response.status_code == 200
        assert response.json()['name'] == 'New'

    def test_update_other_users_folder_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        folder = owner.signed_post('/api/folders', json={'name': 'Private'}).json()
        assert intruder.signed_put(f"/api/folders/{folder['id']}", json={'name': 'Hijacked'}).status_code == 404

    def test_update_unknown_returns_404(self, registered):
        assert registered.signed_put(f'/api/folders/{uuid.uuid4()}', json={'name': 'x'}).status_code == 404


class TestDelete:
    def test_deletes_folder(self, registered):
        folder = registered.signed_post('/api/folders', json={'name': 'Temp'}).json()
        assert registered.signed_delete(f"/api/folders/{folder['id']}").status_code == 204
        assert registered.client.get('/api/folders').json() == []

    def test_delete_detaches_projects(self, registered):
        folder = registered.signed_post('/api/folders', json={'name': 'Temp'}).json()
        project = registered.signed_post('/api/projects', json={'name': 'P', 'folder_id': folder['id']}).json()
        assert project['folder_id'] == folder['id']

        registered.signed_delete(f"/api/folders/{folder['id']}")
        refreshed = registered.client.get(f"/api/projects/{project['id']}").json()
        assert refreshed['folder_id'] is None

    def test_delete_other_users_folder_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        folder = owner.signed_post('/api/folders', json={'name': 'Private'}).json()
        assert intruder.signed_delete(f"/api/folders/{folder['id']}").status_code == 404
