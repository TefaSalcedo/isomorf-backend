"""Material/section catalog endpoints and element references."""

import pytest
from conftest import _register


@pytest.fixture()
def project(registered):
    response = registered.signed_post('/api/projects', json={'name': 'With catalog'})
    assert response.status_code == 201, response.text
    return response.json()


class TestPresets:
    def test_lists_material_and_section_presets(self, registered):
        response = registered.client.get('/api/catalog/presets')
        assert response.status_code == 200
        data = response.json()
        assert any(m['key'] == 'concrete-28' for m in data['materials'])
        assert any(s['key'] == 'rect-30x30' for s in data['sections'])


class TestMaterials:
    def test_crud_material(self, registered, project):
        created = registered.signed_post(
            f"/api/projects/{project['id']}/materials",
            json={'name': "Concrete f'c=24 MPa", 'category': 'concrete', 'properties': {'fc_mpa': 24, 'elastic_modulus_mpa': 22500}},
        )
        assert created.status_code == 201, created.text
        material = created.json()
        assert material['properties']['fc_mpa'] == 24

        listed = registered.client.get(f"/api/projects/{project['id']}/materials")
        assert listed.status_code == 200
        assert [m['id'] for m in listed.json()] == [material['id']]

        updated = registered.signed_put(
            f"/api/projects/{project['id']}/materials/{material['id']}",
            json={'properties': {'fc_mpa': 25}},
        )
        assert updated.status_code == 200
        assert updated.json()['properties']['fc_mpa'] == 25

        assert registered.signed_delete(f"/api/projects/{project['id']}/materials/{material['id']}").status_code == 204
        assert registered.client.get(f"/api/projects/{project['id']}/materials").json() == []

    def test_other_users_project_returns_404(self, make_client):
        owner = _register(make_client())
        intruder = _register(make_client())
        owner_project = owner.signed_post('/api/projects', json={'name': 'P'}).json()
        response = intruder.signed_post(
            f"/api/projects/{owner_project['id']}/materials",
            json={'name': 'Intruder material'},
        )
        assert response.status_code == 404


class TestSections:
    def test_crud_section_with_material(self, registered, project):
        material = registered.signed_post(
            f"/api/projects/{project['id']}/materials",
            json={'name': 'Steel A-36', 'category': 'steel'},
        ).json()
        created = registered.signed_post(
            f"/api/projects/{project['id']}/sections",
            json={'name': 'W310×39', 'shape': 'i_shape', 'material_id': material['id'], 'dimensions': {'d': 0.31, 'bf': 0.165}},
        )
        assert created.status_code == 201, created.text
        section = created.json()
        assert section['material_id'] == material['id']

        assert registered.client.get(f"/api/projects/{project['id']}/sections").json()[0]['name'] == 'W310×39'
        assert registered.signed_delete(f"/api/projects/{project['id']}/sections/{section['id']}").status_code == 204

    def test_rejects_foreign_material(self, registered, project, make_client):
        other = _register(make_client())
        other_project = other.signed_post('/api/projects', json={'name': 'Other'}).json()
        foreign_material = other.signed_post(
            f"/api/projects/{other_project['id']}/materials",
            json={'name': 'Foreign'},
        ).json()
        response = registered.signed_post(
            f"/api/projects/{project['id']}/sections",
            json={'name': 'S', 'material_id': foreign_material['id']},
        )
        assert response.status_code == 400


class TestElementReferences:
    def test_element_with_material_and_section_roundtrip(self, registered, project):
        material = registered.signed_post(
            f"/api/projects/{project['id']}/materials",
            json={'name': "Concrete f'c=28", 'category': 'concrete'},
        ).json()
        section = registered.signed_post(
            f"/api/projects/{project['id']}/sections",
            json={'name': 'C30×30', 'shape': 'rectangular', 'dimensions': {'b': 0.3, 'h': 0.3}},
        ).json()
        element = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={
                'element_type': 'column', 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 1, 'length': 1, 'rotation': 0,
                'material_id': material['id'], 'section_id': section['id'], 'properties': {},
            },
        ).json()
        assert element['material_id'] == material['id']
        assert element['section_id'] == section['id']

    def test_new_element_types_accepted(self, registered, project):
        for element_type, coords in [
            ('slab', (0, 0, 400, 300)),
            ('footing', (0, 0, 150, 150)),
            ('stair', (0, 0, 300, 120)),
            ('ramp', (0, 0, 500, 120)),
            ('opening', (0, 0, 100, 100)),
            ('joist', (0, 0, 500, 0)),
            ('grade_beam', (0, 0, 500, 0)),
            ('brace', (0, 0, 300, 400)),
            ('pile', (0, 0, 1, 0)),
        ]:
            x1, y1, x2, y2 = coords
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            response = registered.signed_post(
                f"/api/projects/{project['id']}/elements",
                json={'element_type': element_type, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'length': length, 'rotation': 0, 'properties': {}},
            )
            assert response.status_code == 201, f'{element_type}: {response.text}'
            assert response.json()['element_type'] == element_type

    def test_deleting_material_nulls_element_reference(self, registered, project):
        material = registered.signed_post(
            f"/api/projects/{project['id']}/materials",
            json={'name': 'Temp', 'category': 'generic'},
        ).json()
        element = registered.signed_post(
            f"/api/projects/{project['id']}/elements",
            json={
                'element_type': 'beam', 'x1': 0, 'y1': 0, 'x2': 400, 'y2': 0, 'length': 400, 'rotation': 0,
                'material_id': material['id'], 'properties': {},
            },
        ).json()
        registered.signed_delete(f"/api/projects/{project['id']}/materials/{material['id']}")
        fetched = [e for e in registered.client.get(f"/api/projects/{project['id']}/elements").json() if e['id'] == element['id']][0]
        assert fetched['material_id'] is None


class TestDocumentSnapshotIncludesReferences:
    def test_document_roundtrip_keeps_material_reference(self, registered, project):
        material = registered.signed_post(
            f"/api/projects/{project['id']}/materials",
            json={'name': "Concrete f'c=28", 'category': 'concrete'},
        ).json()
        document = registered.signed_put(
            f"/api/projects/{project['id']}/document",
            json={
                'elements': [
                    {
                        'element_type': 'column', 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 1, 'length': 1, 'rotation': 0,
                        'material_id': material['id'], 'properties': {},
                    }
                ]
            },
        )
        assert document.status_code == 200, document.text
        assert document.json()['elements'][0]['material_id'] == material['id']

        undo = registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        assert undo.status_code == 200
        redo = registered.signed_post(f"/api/projects/{project['id']}/history/redo")
        assert redo.status_code == 200
        assert redo.json()['elements'][0]['material_id'] == material['id']
