"""Teams, invitations, roles and project sharing authorization."""

import uuid

import pytest
from conftest import _register

WALL = {'element_type': 'wall', 'x1': 0, 'y1': 0, 'x2': 400, 'y2': 0, 'length': 400, 'rotation': 0, 'properties': {}}


def _add_member(owner, invitee, team_id, role):
    response = owner.signed_post(f'/api/teams/{team_id}/invites', json={'role': role})
    assert response.status_code == 201, response.text
    token = response.json()['token']
    response = invitee.signed_post('/api/teams/invites/accept', json={'token': token})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture()
def owner(make_client):
    return _register(make_client())


@pytest.fixture()
def viewer(make_client):
    return _register(make_client())


@pytest.fixture()
def editor(make_client):
    return _register(make_client())


@pytest.fixture()
def team(owner):
    response = owner.signed_post('/api/teams', json={'name': 'Estructuras'})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def shared_project(owner, viewer, editor, team):
    response = owner.signed_post('/api/projects', json={'name': 'Compartido'})
    assert response.status_code == 201, response.text
    project = response.json()
    response = owner.signed_post(f"/api/teams/{team['id']}/projects", json={'project_id': project['id']})
    assert response.status_code == 201, response.text
    _add_member(owner, viewer, team['id'], 'viewer')
    _add_member(owner, editor, team['id'], 'editor')
    return project


class TestTeams:
    def test_create_lists_team_with_owner_role(self, owner, team):
        assert team['my_role'] == 'owner'
        assert team['member_count'] == 1
        response = owner.client.get('/api/teams')
        assert response.status_code == 200
        assert [item['id'] for item in response.json()] == [team['id']]

    def test_non_member_cannot_see_team(self, viewer, team):
        assert viewer.client.get(f"/api/teams/{team['id']}").status_code == 404

    def test_requires_device_proof(self, owner):
        assert owner.client.post('/api/teams', json={'name': 'x'}).status_code == 401

    def test_owner_can_rename_and_delete(self, owner, team):
        response = owner.signed_put(f"/api/teams/{team['id']}", json={'name': 'Renombrado'})
        assert response.status_code == 200
        assert response.json()['name'] == 'Renombrado'
        assert owner.signed_delete(f"/api/teams/{team['id']}").status_code == 204
        assert owner.client.get(f"/api/teams/{team['id']}").status_code == 404


class TestInvites:
    def test_invite_link_flow_adds_member(self, owner, viewer, team):
        response = owner.signed_post(f"/api/teams/{team['id']}/invites", json={'role': 'viewer'})
        assert response.status_code == 201, response.text
        data = response.json()
        assert data['accept_url'].endswith(f"/invites/{data['token']}")

        preview = viewer.client.get(f"/api/teams/invites/{data['token']}")
        assert preview.status_code == 200
        assert preview.json()['team_name'] == 'Estructuras'

        accepted = viewer.signed_post('/api/teams/invites/accept', json={'token': data['token']})
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()['my_role'] == 'viewer'
        assert accepted.json()['member_count'] == 2

        # A token is single use.
        assert viewer.client.get(f"/api/teams/invites/{data['token']}").status_code == 404

    def test_email_bound_invite_rejects_other_user(self, owner, viewer, team):
        response = owner.signed_post(f"/api/teams/{team['id']}/invites", json={'email': 'someone-else@example.com', 'role': 'editor'})
        token = response.json()['token']
        assert viewer.signed_post('/api/teams/invites/accept', json={'token': token}).status_code == 403

    def test_cannot_invite_as_owner(self, owner, team):
        assert owner.signed_post(f"/api/teams/{team['id']}/invites", json={'role': 'owner'}).status_code == 400

    def test_unknown_token(self, viewer):
        assert viewer.client.get(f'/api/teams/invites/{uuid.uuid4().hex}').status_code == 404

    def test_only_owner_can_invite(self, owner, editor, team):
        _add_member(owner, editor, team['id'], 'editor')
        assert editor.signed_post(f"/api/teams/{team['id']}/invites", json={'role': 'viewer'}).status_code == 403

    def test_owner_sees_pending_invites_and_revokes(self, owner, team):
        invite = owner.signed_post(f"/api/teams/{team['id']}/invites", json={'role': 'viewer'}).json()
        detail = owner.client.get(f"/api/teams/{team['id']}").json()
        assert [item['id'] for item in detail['invites']] == [invite['id']]
        assert owner.signed_delete(f"/api/teams/{team['id']}/invites/{invite['id']}").status_code == 204
        assert owner.client.get(f"/api/teams/invites/{invite['token']}").status_code == 404


class TestMembers:
    def test_owner_changes_role(self, owner, viewer, team):
        _add_member(owner, viewer, team['id'], 'viewer')
        detail = owner.client.get(f"/api/teams/{team['id']}").json()
        member = next(m for m in detail['members'] if m['user_id'] == viewer.user['id'])
        response = owner.signed('PATCH', f"/api/teams/{team['id']}/members/{member['id']}/role", json={'role': 'editor'})
        assert response.status_code == 200, response.text
        assert response.json()['role'] == 'editor'

    def test_editor_cannot_change_roles(self, owner, editor, viewer, team):
        _add_member(owner, editor, team['id'], 'editor')
        _add_member(owner, viewer, team['id'], 'viewer')
        detail = owner.client.get(f"/api/teams/{team['id']}").json()
        member = next(m for m in detail['members'] if m['user_id'] == viewer.user['id'])
        assert editor.signed('PATCH', f"/api/teams/{team['id']}/members/{member['id']}/role", json={'role': 'editor'}).status_code == 403

    def test_creator_keeps_ownership(self, owner, team):
        detail = owner.client.get(f"/api/teams/{team['id']}").json()
        member = detail['members'][0]
        assert owner.signed('PATCH', f"/api/teams/{team['id']}/members/{member['id']}/role", json={'role': 'viewer'}).status_code == 400
        assert owner.signed_delete(f"/api/teams/{team['id']}/members/{member['id']}").status_code == 400
        assert owner.signed_post(f"/api/teams/{team['id']}/leave").status_code == 400

    def test_member_can_leave(self, owner, viewer, team):
        _add_member(owner, viewer, team['id'], 'viewer')
        assert viewer.signed_post(f"/api/teams/{team['id']}/leave").status_code == 204
        assert viewer.client.get('/api/teams').json() == []


class TestProjectSharing:
    def test_shared_project_visible_to_members(self, viewer, editor, shared_project):
        for member, role in ((viewer, 'viewer'), (editor, 'editor')):
            listed = member.client.get('/api/projects').json()
            assert [p['id'] for p in listed] == [shared_project['id']]
            assert listed[0]['access_role'] == role
            detail = member.client.get(f"/api/projects/{shared_project['id']}")
            assert detail.status_code == 200
            assert detail.json()['access_role'] == role

    def test_owner_keeps_owner_role(self, owner, shared_project):
        detail = owner.client.get(f"/api/projects/{shared_project['id']}").json()
        assert detail['access_role'] == 'owner'

    def test_only_project_owner_can_share(self, owner, editor, team):
        _add_member(owner, editor, team['id'], 'editor')
        project = editor.signed_post('/api/projects', json={'name': 'Del editor'}).json()
        assert editor.signed_post(f"/api/teams/{team['id']}/projects", json={'project_id': project['id']}).status_code == 403
        # Team owner cannot share a project that is not theirs.
        assert owner.signed_post(f"/api/teams/{team['id']}/projects", json={'project_id': project['id']}).status_code == 404

    def test_unshare_removes_access(self, owner, viewer, team, shared_project):
        assert owner.signed_delete(f"/api/teams/{team['id']}/projects/{shared_project['id']}").status_code == 204
        assert viewer.client.get(f"/api/projects/{shared_project['id']}").status_code == 404

    def test_team_detail_lists_projects(self, owner, team, shared_project):
        detail = owner.client.get(f"/api/teams/{team['id']}").json()
        assert [p['id'] for p in detail['projects']] == [shared_project['id']]
        assert detail['project_count'] == 1


class TestViewerIsReadOnly:
    def test_viewer_reads(self, viewer, shared_project):
        pid = shared_project['id']
        assert viewer.client.get(f'/api/projects/{pid}/elements').status_code == 200
        assert viewer.client.get(f'/api/projects/{pid}/history').status_code == 200
        assert viewer.client.get(f'/api/projects/{pid}/load-cases').status_code == 200
        assert viewer.client.get(f'/api/projects/{pid}/loads').status_code == 200

    def test_viewer_mutations_are_forbidden(self, viewer, shared_project):
        pid = shared_project['id']
        assert viewer.signed_post(f'/api/projects/{pid}/elements', json=WALL).status_code == 403
        assert viewer.signed_put(f'/api/projects/{pid}', json={'name': 'Hack'}).status_code == 403
        assert viewer.signed_delete(f'/api/projects/{pid}').status_code == 403
        assert viewer.signed_put(f'/api/projects/{pid}/document', json={'elements': []}).status_code == 403
        assert viewer.signed_post(f'/api/projects/{pid}/history/undo').status_code == 403
        assert viewer.signed_post(f'/api/projects/{pid}/history/redo').status_code == 403
        assert viewer.signed_post(f'/api/projects/{pid}/history/1/restore').status_code == 403
        assert viewer.signed_post(f'/api/projects/{pid}/load-cases', json={'name': 'D', 'category': 'dead'}).status_code == 403

    def test_viewer_cannot_touch_existing_element_or_load(self, owner, viewer, shared_project):
        pid = shared_project['id']
        element = owner.signed_post(f'/api/projects/{pid}/elements', json=WALL).json()
        assert viewer.signed_put(f"/api/projects/{pid}/elements/{element['id']}", json={'length': 1}).status_code == 403
        assert viewer.signed_delete(f"/api/projects/{pid}/elements/{element['id']}").status_code == 403


class TestEditorCanEditButNotAdminister:
    def test_editor_mutates_project_content(self, editor, shared_project):
        pid = shared_project['id']
        created = editor.signed_post(f'/api/projects/{pid}/elements', json=WALL)
        assert created.status_code == 201, created.text
        assert editor.signed_put(f'/api/projects/{pid}', json={'name': 'Editado'}).status_code == 200
        saved = editor.signed_put(f'/api/projects/{pid}/document', json={'elements': [{**WALL, 'id': created.json()['id'], 'length': 500}]})
        assert saved.status_code == 200, saved.text
        assert editor.signed_post(f'/api/projects/{pid}/history/undo').status_code == 200
        case = editor.signed_post(f'/api/projects/{pid}/load-cases', json={'name': 'Dead', 'category': 'dead'})
        assert case.status_code == 201, case.text

    def test_editor_cannot_delete_or_move_project(self, editor, shared_project):
        pid = shared_project['id']
        assert editor.signed_delete(f'/api/projects/{pid}').status_code == 403
        assert editor.signed_put(f'/api/projects/{pid}', json={'folder_id': None}).status_code == 403


class TestPrivateProjectsUnchanged:
    def test_unrelated_user_gets_404(self, owner, viewer):
        project = owner.signed_post('/api/projects', json={'name': 'Privado'}).json()
        assert viewer.client.get(f"/api/projects/{project['id']}").status_code == 404
        assert viewer.signed_post(f"/api/projects/{project['id']}/elements", json=WALL).status_code == 404
