"""Project block library endpoints and the block_ref element type."""

import pytest
from conftest import _register

BLOCK = {
    'name': 'Title block A1',
    'description': 'Corporate title block',
    'base_x': 0,
    'base_y': 0,
    'items': [
        {'element_type': 'rectangle', 'x1': 0, 'y1': 0, 'x2': 84, 'y2': 59, 'length': 286, 'rotation': 0, 'properties': {}},
        {'element_type': 'line', 'x1': 0, 'y1': 40, 'x2': 84, 'y2': 40, 'length': 84, 'rotation': 0, 'properties': {}},
    ],
}


@pytest.fixture()
def project(registered):
    response = registered.signed_post('/api/projects', json={'name': 'With blocks'})
    assert response.status_code == 201, response.text
    return response.json()


def _block_ref(block_id, x=0, y=0):
    return {
        'element_type': 'block_ref',
        'x1': x, 'y1': y, 'x2': x + 84, 'y2': y + 59,
        'length': 1, 'rotation': 0,
        'properties': {'block_id': block_id},
    }


class TestBlocks:
    def test_crud_block(self, registered, project):
        created = registered.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK)
        assert created.status_code == 201, created.text
        block = created.json()
        assert block['name'] == BLOCK['name']
        assert len(block['items']) == 2

        listed = registered.client.get(f"/api/projects/{project['id']}/blocks")
        assert [b['id'] for b in listed.json()] == [block['id']]

        fetched = registered.client.get(f"/api/projects/{project['id']}/blocks/{block['id']}")
        assert fetched.status_code == 200
        assert fetched.json()['items'][0]['element_type'] == 'rectangle'

        updated = registered.signed_put(
            f"/api/projects/{project['id']}/blocks/{block['id']}",
            json={'name': 'Renamed', 'description': 'v2'},
        )
        assert updated.status_code == 200
        assert updated.json()['name'] == 'Renamed'

        assert registered.signed_delete(f"/api/projects/{project['id']}/blocks/{block['id']}").status_code == 204
        assert registered.client.get(f"/api/projects/{project['id']}/blocks").json() == []

    def test_rejects_empty_items(self, registered, project):
        response = registered.signed_post(
            f"/api/projects/{project['id']}/blocks",
            json={**BLOCK, 'items': []},
        )
        assert response.status_code == 422

    def test_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        owner_project = owner.signed_post('/api/projects', json={'name': 'P'}).json()
        response = intruder.signed_post(f"/api/projects/{owner_project['id']}/blocks", json=BLOCK)
        assert response.status_code == 404


class TestBlockRoles:
    def test_viewer_reads_but_cannot_mutate(self, make_client):
        owner = _register(make_client())
        viewer = _register(make_client())
        team = owner.signed_post('/api/teams', json={'name': 'T'}).json()
        invite = owner.signed_post(f"/api/teams/{team['id']}/invites", json={'role': 'viewer'}).json()
        viewer.signed_post('/api/teams/invites/accept', json={'token': invite['token']})
        project = owner.signed_post('/api/projects', json={'name': 'Shared'}).json()
        owner.signed_post(f"/api/teams/{team['id']}/projects", json={'project_id': project['id']})

        block = owner.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).json()

        assert viewer.client.get(f"/api/projects/{project['id']}/blocks").status_code == 200
        assert viewer.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).status_code == 403
        assert viewer.signed_put(f"/api/projects/{project['id']}/blocks/{block['id']}", json={'name': 'X'}).status_code == 403
        assert viewer.signed_delete(f"/api/projects/{project['id']}/blocks/{block['id']}").status_code == 403


class TestBlockRef:
    def test_block_ref_element_accepted(self, registered, project):
        block = registered.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).json()
        created = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json=_block_ref(block['id']),
        )
        assert created.status_code == 201, created.text
        assert created.json()['element_type'] == 'block_ref'

    def test_block_ref_allows_point_geometry(self, registered, project):
        block = registered.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).json()
        payload = {**_block_ref(block['id']), 'x2': 0, 'y2': 0}
        response = registered.signed_post(f"/api/projects/{project['id']}/elements", json=payload)
        assert response.status_code == 201, response.text

    def test_delete_block_in_use_returns_409(self, registered, project):
        block = registered.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).json()
        registered.signed_post(f"/api/projects/{project['id']}/elements", json=_block_ref(block['id']))
        response = registered.signed_delete(f"/api/projects/{project['id']}/blocks/{block['id']}")
        assert response.status_code == 409

    def test_delete_block_after_refs_removed(self, registered, project):
        block = registered.signed_post(f"/api/projects/{project['id']}/blocks", json=BLOCK).json()
        ref = registered.signed_post(f"/api/projects/{project['id']}/elements", json=_block_ref(block['id'])).json()
        registered.signed_delete(f"/api/projects/{project['id']}/elements/{ref['id']}")
        assert registered.signed_delete(f"/api/projects/{project['id']}/blocks/{block['id']}").status_code == 204


class TestLayerStyles:
    def test_linetype_and_lineweight_roundtrip(self, registered, project):
        document = registered.signed_put(
            f"/api/projects/{project['id']}/document",
            json={
                'design_settings': {
                    'layers': [
                        {
                            'id': 'axes', 'name': 'Axes', 'color': '#dc2626',
                            'visible': True, 'locked': False,
                            'linetype': 'center', 'lineweight': 0.35,
                        }
                    ]
                },
                'elements': [],
            },
        )
        assert document.status_code == 200, document.text
        layer = document.json()['design_settings']['layers'][0]
        assert layer['linetype'] == 'center'
        assert layer['lineweight'] == 0.35
