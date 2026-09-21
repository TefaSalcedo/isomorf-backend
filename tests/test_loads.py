"""Load case and element load endpoints."""

import uuid

import pytest
from conftest import _register


@pytest.fixture()
def project(registered):
    response = registered.signed_post('/api/projects', json={'name': 'Loads project'})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def load_case(registered, project):
    response = registered.signed_post(f"/api/projects/{project['id']}/load-cases", json={'name': 'Dead', 'category': 'permanent'})
    assert response.status_code == 201, response.text
    return response.json()


def _load_payload(load_case, **overrides):
    return {'load_case_id': load_case['id'], 'load_type': 'distributed', 'magnitude': 25.5, 'unit': 'kN/m', 'direction': '-Y', 'position': {}, **overrides}


class TestLoadCases:
    def test_create_and_list(self, registered, project):
        created = registered.signed_post(f"/api/projects/{project['id']}/load-cases", json={'name': 'Live'})
        assert created.status_code == 201
        assert created.json()['category'] == 'service'

        response = registered.client.get(f"/api/projects/{project['id']}/load-cases")
        assert response.status_code == 200
        assert [item['name'] for item in response.json()] == ['Live']

    def test_requires_device_proof(self, registered, project):
        assert registered.client.post(f"/api/projects/{project['id']}/load-cases", json={'name': 'x'}).status_code == 401

    def test_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        owner_project = owner.signed_post('/api/projects', json={'name': 'P'}).json()
        response = intruder.signed_post(f"/api/projects/{owner_project['id']}/load-cases", json={'name': 'x'})
        assert response.status_code == 404


class TestLoads:
    def test_create_list_update_delete(self, registered, project, load_case):
        element = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={'element_type': 'beam', 'x1': 0, 'y1': 0, 'x2': 500, 'y2': 0, 'length': 500, 'rotation': 0, 'properties': {}},
        ).json()

        created = registered.signed_post(
            f"/api/projects/{project['id']}/loads",
            json=_load_payload(load_case, element_id=element['id']),
        )
        assert created.status_code == 201, created.text
        load = created.json()
        assert load['element_id'] == element['id']
        assert load['load_type'] == 'distributed'

        loads = registered.client.get(f"/api/projects/{project['id']}/loads").json()
        assert len(loads) == 1

        updated = registered.signed_put(
            f"/api/projects/{project['id']}/loads/{load['id']}",
            json={'magnitude': 30.0},
        )
        assert updated.status_code == 200
        assert updated.json()['magnitude'] == 30.0

        assert registered.signed_delete(f"/api/projects/{project['id']}/loads/{load['id']}").status_code == 204
        assert registered.client.get(f"/api/projects/{project['id']}/loads").json() == []

    def test_load_case_from_other_project_returns_404(self, registered, project):
        other_project = registered.signed_post('/api/projects', json={'name': 'Other'}).json()
        other_case = registered.signed_post(f"/api/projects/{other_project['id']}/load-cases", json={'name': 'Dead'}).json()

        response = registered.signed_post(f"/api/projects/{project['id']}/loads", json=_load_payload(other_case))
        assert response.status_code == 404

    def test_element_from_other_project_returns_400(self, registered, project, load_case):
        other_project = registered.signed_post('/api/projects', json={'name': 'Other'}).json()
        element = registered.signed_post(
            f"/api/projects/{other_project['id']}/elements",
            json={'element_type': 'wall', 'x1': 0, 'y1': 0, 'x2': 100, 'y2': 0, 'length': 100, 'rotation': 0, 'properties': {}},
        ).json()

        response = registered.signed_post(
            f"/api/projects/{project['id']}/loads",
            json=_load_payload(load_case, element_id=element['id']),
        )
        assert response.status_code == 400
        assert response.json()['detail'] == 'Element does not belong to project'

    def test_unknown_load_returns_404(self, registered, project):
        assert registered.signed_put(f"/api/projects/{project['id']}/loads/{uuid.uuid4()}", json={'magnitude': 1}).status_code == 404
        assert registered.signed_delete(f"/api/projects/{project['id']}/loads/{uuid.uuid4()}").status_code == 404
