"""Project element CRUD endpoints, ownership rules and payload validation."""

import uuid

import pytest
from conftest import _register

WALL = {'element_type': 'wall', 'x1': 0, 'y1': 0, 'x2': 400, 'y2': 0, 'length': 400, 'rotation': 0, 'properties': {}}


@pytest.fixture()
def project(registered):
    response = registered.signed_post('/api/projects', json={'name': 'With elements'})
    assert response.status_code == 201, response.text
    return response.json()


class TestCreate:
    def test_creates_element(self, registered, project):
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json=WALL)
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['element_type'] == 'wall'
        assert data['project_id'] == project['id']
        assert data['length'] == 400

    def test_accepts_client_provided_id(self, registered, project):
        element_id = str(uuid.uuid4())
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json={**WALL, 'id': element_id})
        assert response.status_code == 201
        assert response.json()['id'] == element_id

    def test_rejects_degenerate_geometry(self, registered, project):
        response = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={**WALL, 'x2': 0, 'y2': 0},
        )
        assert response.status_code == 422

    def test_requires_device_proof(self, registered, project):
        response = registered.client.post(f"/api/projects/{project['id']}/elements", json=WALL)
        assert response.status_code == 401

    def test_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        owner_project = owner.signed_post('/api/projects', json={'name': 'P'}).json()
        response = intruder.signed_post(f"/api/projects/{owner_project['id']}/elements", json=WALL)
        assert response.status_code == 404


class TestCadPrimitives:
    """Roadmap week 8: annotation primitives persist alongside structural types."""

    @pytest.mark.parametrize('element_type', ['line', 'arc', 'circle', 'ellipse', 'rectangle', 'hatch'])
    def test_creates_primitive(self, registered, project, element_type):
        payload = {
            'element_type': element_type,
            'x1': 0,
            'y1': 0,
            'x2': 200,
            'y2': 150,
            'length': 250,
            'rotation': 0,
            'properties': {},
        }
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json=payload)
        assert response.status_code == 201, response.text
        assert response.json()['element_type'] == element_type

    def test_creates_polyline_with_vertices(self, registered, project):
        payload = {
            'element_type': 'polyline',
            'x1': 0,
            'y1': 0,
            'x2': 600,
            'y2': 400,
            'length': 2000,
            'rotation': 0,
            'properties': {'points': [{'x': 0, 'y': 0}, {'x': 600, 'y': 0}, {'x': 600, 'y': 400}, {'x': 0, 'y': 400}]},
        }
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json=payload)
        assert response.status_code == 201, response.text
        assert response.json()['properties']['points'][2] == {'x': 600, 'y': 400}

    def test_closed_polyline_allows_equal_endpoints(self, registered, project):
        payload = {
            'element_type': 'polyline',
            'x1': 0,
            'y1': 0,
            'x2': 0,
            'y2': 0,
            'length': 2000,
            'rotation': 0,
            'properties': {'closed': True, 'points': [{'x': 0, 'y': 0}, {'x': 600, 'y': 0}, {'x': 600, 'y': 400}, {'x': 0, 'y': 400}]},
        }
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json=payload)
        assert response.status_code == 201, response.text

    def test_line_still_rejects_degenerate_geometry(self, registered, project):
        response = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={'element_type': 'line', 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0, 'length': 1, 'rotation': 0, 'properties': {}},
        )
        assert response.status_code == 422

    def test_primitives_roundtrip_through_document(self, registered, project):
        element = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={'element_type': 'circle', 'x1': 100, 'y1': 100, 'x2': 150, 'y2': 100, 'length': 314.16, 'rotation': 0, 'properties': {'radius': 50}},
        ).json()
        response = registered.signed_put(
            f"/api/projects/{project['id']}/document",
            json={'elements': [element]},
        )
        assert response.status_code == 200, response.text
        saved = [el for el in response.json()['elements'] if el['id'] == element['id']]
        assert saved and saved[0]['element_type'] == 'circle'
        assert saved[0]['properties']['radius'] == 50


class TestList:
    def test_lists_elements(self, registered, project):
        registered.signed_post(f"/api/projects/{project['id']}/elements", json=WALL)
        registered.signed_post(f"/api/projects/{project['id']}/elements", json={**WALL, 'element_type': 'column', 'x2': 0, 'y2': 300, 'length': 300})

        response = registered.client.get(f"/api/projects/{project['id']}/elements")
        assert response.status_code == 200
        types = [item['element_type'] for item in response.json()]
        assert types == ['wall', 'column']

    def test_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        owner_project = owner.signed_post('/api/projects', json={'name': 'P'}).json()
        assert intruder.client.get(f"/api/projects/{owner_project['id']}/elements").status_code == 404


class TestUpdate:
    def test_updates_element(self, registered, project):
        element = registered.signed_post(f"/api/projects/{project['id']}/elements", json=WALL).json()
        response = registered.signed_put(
            f"/api/projects/{project['id']}/elements/{element['id']}",
            json={'properties': {'layer_id': 'l1'}, 'rotation': 15},
        )
        assert response.status_code == 200
        assert response.json()['properties'] == {'layer_id': 'l1'}
        assert response.json()['rotation'] == 15

    def test_unknown_element_returns_404(self, registered, project):
        response = registered.signed_put(f"/api/projects/{project['id']}/elements/{uuid.uuid4()}", json={'rotation': 1})
        assert response.status_code == 404


class TestDelete:
    def test_deletes_element(self, registered, project):
        element = registered.signed_post(f"/api/projects/{project['id']}/elements", json=WALL).json()
        assert registered.signed_delete(f"/api/projects/{project['id']}/elements/{element['id']}").status_code == 204
        assert registered.client.get(f"/api/projects/{project['id']}/elements").json() == []

    def test_unknown_element_returns_404(self, registered, project):
        assert registered.signed_delete(f"/api/projects/{project['id']}/elements/{uuid.uuid4()}").status_code == 404
