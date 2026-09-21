"""Versioned document endpoints: snapshots, per-element diffs, persisted undo/redo."""

import uuid

import pytest
from conftest import _register
from sqlalchemy import delete

from app.models.project import Project
from app.models.project_document import ProjectDocument

WALL = {'element_type': 'wall', 'x1': 0, 'y1': 0, 'x2': 400, 'y2': 0, 'length': 400, 'rotation': 0, 'properties': {'thickness': 0.15}}
COLUMN = {'element_type': 'column', 'x1': 50, 'y1': 50, 'x2': 51, 'y2': 50, 'length': 1, 'rotation': 0, 'properties': {'width': 0.3, 'depth': 0.3}}


@pytest.fixture()
def project(registered):
    response = registered.signed_post('/api/projects', json={'name': 'Versioned'})
    assert response.status_code == 201, response.text
    return response.json()


def _save(registered, project_id, elements, **extra):
    payload = {'elements': elements, **extra}
    return registered.signed_put(f"/api/projects/{project_id}/document", json=payload)


class TestSaveDocument:
    def test_creates_baseline_and_first_revision(self, registered, project):
        response = _save(registered, project['id'], [WALL])
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['revision'] == 2
        assert data['head_revision'] == 2
        assert data['can_undo'] is True
        assert data['can_redo'] is False
        assert [el['element_type'] for el in data['elements']] == ['wall']

    def test_records_per_element_diffs(self, registered, project):
        wall = _save(registered, project['id'], [WALL]).json()['elements'][0]
        moved_wall = {**WALL, 'id': wall['id'], 'y2': 100}
        response = _save(registered, project['id'], [moved_wall, COLUMN])
        assert response.json()['revision'] == 3

        history = registered.client.get(f"/api/projects/{project['id']}/history").json()
        latest = history['revisions'][0]
        assert latest['revision'] == 3
        operations = {change['operation'] for change in latest['changes']}
        assert operations == {'update', 'create'}

    def test_noop_save_does_not_create_revision(self, registered, project):
        wall = _save(registered, project['id'], [WALL]).json()['elements'][0]
        response = _save(registered, project['id'], [{**WALL, 'id': wall['id']}])
        assert response.json()['revision'] == 2
        history = registered.client.get(f"/api/projects/{project['id']}/history").json()
        assert len(history['revisions']) == 2

    def test_requires_device_proof(self, registered, project):
        response = registered.client.put(f"/api/projects/{project['id']}/document", json={'elements': [WALL]})
        assert response.status_code == 401

    def test_other_users_project_returns_404(self, registered, project, make_client):
        intruder = _register(make_client())
        response = intruder.signed_put(f"/api/projects/{project['id']}/document", json={'elements': [WALL]})
        assert response.status_code == 404


class TestUndoRedo:
    def test_undo_restores_previous_state(self, registered, project):
        _save(registered, project['id'], [WALL])
        _save(registered, project['id'], [WALL, COLUMN])

        response = registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['revision'] == 2
        assert data['can_undo'] is True
        assert data['can_redo'] is True
        assert [el['element_type'] for el in data['elements']] == ['wall']

        detail = registered.client.get(f"/api/projects/{project['id']}").json()
        assert [el['element_type'] for el in detail['elements']] == ['wall']
        assert detail['current_revision'] == 2

    def test_redo_reapplies_state(self, registered, project):
        _save(registered, project['id'], [WALL])
        _save(registered, project['id'], [WALL, COLUMN])
        registered.signed_post(f"/api/projects/{project['id']}/history/undo")

        response = registered.signed_post(f"/api/projects/{project['id']}/history/redo")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['revision'] == 3
        assert len(data['elements']) == 2
        assert data['can_redo'] is False

    def test_undo_to_baseline_empties_document(self, registered, project):
        _save(registered, project['id'], [WALL])
        response = registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        data = response.json()
        assert data['revision'] == 1
        assert data['elements'] == []
        assert data['can_undo'] is False

    def test_save_after_undo_truncates_future(self, registered, project):
        _save(registered, project['id'], [WALL])
        _save(registered, project['id'], [WALL, COLUMN])
        registered.signed_post(f"/api/projects/{project['id']}/history/undo")

        response = _save(registered, project['id'], [WALL, {**COLUMN, 'x1': 999, 'x2': 1000}])
        data = response.json()
        assert data['revision'] == 3
        assert data['head_revision'] == 3
        assert data['can_redo'] is False

        redo = registered.signed_post(f"/api/projects/{project['id']}/history/redo")
        assert redo.status_code == 409

    def test_undo_nothing_returns_409(self, registered, project):
        response = registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        assert response.status_code == 409

    def test_delete_and_undo_restores_element(self, registered, project):
        _save(registered, project['id'], [WALL])
        _save(registered, project['id'], [])
        assert registered.client.get(f"/api/projects/{project['id']}/elements").json() == []

        response = registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        elements = response.json()['elements']
        assert len(elements) == 1
        assert elements[0]['element_type'] == 'wall'


class TestRestore:
    def test_restore_jumps_to_revision(self, registered, project):
        _save(registered, project['id'], [WALL])
        _save(registered, project['id'], [WALL, COLUMN])
        response = registered.signed_post(f"/api/projects/{project['id']}/history/1/restore")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['revision'] == 1
        assert data['elements'] == []
        assert data['can_redo'] is True

    def test_restore_unknown_revision_404(self, registered, project):
        response = registered.signed_post(f"/api/projects/{project['id']}/history/99/restore")
        assert response.status_code == 404


class TestHistory:
    def test_history_lists_revisions_with_changes(self, registered, project):
        _save(registered, project['id'], [WALL])
        response = registered.client.get(f"/api/projects/{project['id']}/history")
        assert response.status_code == 200
        data = response.json()
        assert data['current_revision'] == 2
        assert data['head_revision'] == 2
        assert [rev['revision'] for rev in data['revisions']] == [2, 1]
        assert data['revisions'][0]['changes'][0]['operation'] == 'create'

    def test_other_users_history_returns_404(self, registered, project, make_client):
        intruder = _register(make_client())
        assert intruder.client.get(f"/api/projects/{project['id']}/history").status_code == 404


class TestLoadLinks:
    def test_undo_restores_load_element_link(self, registered, project):
        saved = _save(registered, project['id'], [WALL]).json()
        element_id = saved['elements'][0]['id']

        load_case = registered.signed_post(f"/api/projects/{project['id']}/load-cases", json={'name': 'Case'}).json()
        load = registered.signed_post(
            f"/api/projects/{project['id']}/loads",
            json={'load_case_id': load_case['id'], 'element_id': element_id, 'load_type': 'dead', 'magnitude': 2.5, 'unit': 'kN/m', 'direction': '-Y', 'position': {}},
        ).json()
        assert load['element_id'] == element_id

        _save(registered, project['id'], [])
        orphan = registered.client.get(f"/api/projects/{project['id']}/loads").json()
        assert orphan[0]['element_id'] is None

        registered.signed_post(f"/api/projects/{project['id']}/history/undo")
        relinked = registered.client.get(f"/api/projects/{project['id']}/loads").json()
        assert relinked[0]['element_id'] == element_id


class TestLegacyProjects:
    def test_baseline_created_lazily_for_project_without_history(self, registered, db_session):
        project = Project(user_id=uuid.UUID(registered.user['id']), name='Legacy', description='')
        db_session.add(project)
        db_session.flush()
        project_id = str(project.id)
        db_session.execute(delete(ProjectDocument).where(ProjectDocument.project_id == project.id))
        db_session.flush()

        response = _save(registered, project_id, [WALL])
        assert response.status_code == 200, response.text
        assert response.json()['revision'] == 2

        history = registered.client.get(f"/api/projects/{project_id}/history").json()
        assert history['revisions'][-1]['revision'] == 1
