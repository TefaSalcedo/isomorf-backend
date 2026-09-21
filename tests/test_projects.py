"""Project CRUD endpoints, including public_id lookup and ownership rules."""

import uuid

from conftest import _register


def _create_project(registered, **overrides):
    payload = {'name': 'Frame model', 'description': 'Two-storey frame', **overrides}
    return registered.signed_post('/api/projects', json=payload)


class TestCreate:
    def test_creates_project_with_public_id(self, registered):
        response = _create_project(registered)
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['name'] == 'Frame model'
        assert len(data['public_id']) == 12
        assert data['design_settings'] == {}

    def test_requires_authentication(self, client):
        response = client.post('/api/projects', json={'name': 'x'})
        assert response.status_code == 401

    def test_requires_device_proof(self, registered):
        response = registered.client.post('/api/projects', json={'name': 'x'})
        assert response.status_code == 401
        assert response.json()['detail'] == 'Device proof required'

    def test_folder_of_another_user_returns_400(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        folder = owner.signed_post('/api/folders', json={'name': 'Private'})
        assert folder.status_code == 201

        response = _create_project(intruder, folder_id=folder.json()['id'])
        assert response.status_code == 400
        assert response.json()['detail'] == 'Folder does not belong to user'


class TestRead:
    def test_list_returns_only_own_projects(self, make_client):
        user_a = _register(make_client())
        user_b = _register(make_client())
        _create_project(user_a, name='A project')
        _create_project(user_b, name='B project')

        projects = user_a.client.get('/api/projects').json()
        assert [item['name'] for item in projects] == ['A project']

    def test_get_by_public_id(self, registered):
        project = _create_project(registered).json()
        response = registered.client.get(f"/api/projects/{project['public_id']}")
        assert response.status_code == 200
        assert response.json()['id'] == project['id']
        assert response.json()['elements'] == []

    def test_get_by_internal_uuid(self, registered):
        project = _create_project(registered).json()
        response = registered.client.get(f"/api/projects/{project['id']}")
        assert response.status_code == 200
        assert response.json()['public_id'] == project['public_id']

    def test_get_unknown_returns_404(self, registered):
        assert registered.client.get(f'/api/projects/{uuid.uuid4()}').status_code == 404

    def test_get_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        project = _create_project(owner).json()
        assert intruder.client.get(f"/api/projects/{project['public_id']}").status_code == 404


class TestUpdate:
    def test_updates_fields(self, registered):
        project = _create_project(registered).json()
        response = registered.signed_put(
            f"/api/projects/{project['id']}",
            json={'name': 'Renamed', 'description': 'Updated', 'design_settings': {'unit': 'm', 'layers': [{'id': 'l1', 'name': 'Walls', 'color': '#ff0000', 'visible': True, 'locked': False}]}},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['name'] == 'Renamed'
        assert data['design_settings']['layers'][0]['name'] == 'Walls'

    def test_update_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        project = _create_project(owner).json()
        response = intruder.signed_put(f"/api/projects/{project['id']}", json={'name': 'Hijacked'})
        assert response.status_code == 404


class TestDelete:
    def test_deletes_project(self, registered):
        project = _create_project(registered).json()
        assert registered.signed_delete(f"/api/projects/{project['id']}").status_code == 204
        assert registered.client.get(f"/api/projects/{project['id']}").status_code == 404

    def test_delete_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        project = _create_project(owner).json()
        assert intruder.signed_delete(f"/api/projects/{project['id']}").status_code == 404
