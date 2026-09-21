"""Versioned document model for project editor state.

The live tables (``project_elements``, ``projects.design_settings``) always
reflect the document at ``projects.current_revision``. Every save appends a
``project_documents`` snapshot plus per-element ``element_revisions`` diffs and
moves the pointer forward, truncating any discarded "future" first. Undo/redo
move the pointer and re-apply the target snapshot, so history survives reloads
and is consistent for every reader of the project.
"""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_document import ElementRevision, ProjectDocument
from app.models.project_element import ElementType, ProjectElement
from app.models.structural_load import ElementLoad, LoadCase
from app.models.user import User
from app.schemas.document import DocumentPayload

ELEMENT_FIELDS = ('x1', 'y1', 'x2', 'y2', 'length', 'rotation', 'properties')


def _locked_owned_project(db: Session, user: User, project_id: UUID) -> Project:
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user.id).with_for_update()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    return project


def _serialize_element(element: ProjectElement) -> dict:
    return {
        'id': str(element.id),
        'element_type': str(element.element_type),
        'x1': element.x1,
        'y1': element.y1,
        'x2': element.x2,
        'y2': element.y2,
        'length': element.length,
        'rotation': element.rotation,
        'properties': element.properties,
        'created_at': element.created_at.isoformat() if element.created_at else None,
    }


def _list_elements(db: Session, project_id: UUID) -> list[ProjectElement]:
    return list(db.scalars(select(ProjectElement).where(ProjectElement.project_id == project_id).order_by(ProjectElement.created_at)).all())


def _load_links(db: Session, project_id: UUID) -> dict[str, list[str]]:
    rows = db.execute(
        select(ElementLoad.element_id, ElementLoad.id)
        .join(LoadCase, ElementLoad.load_case_id == LoadCase.id)
        .where(LoadCase.project_id == project_id, ElementLoad.element_id.is_not(None))
    ).all()
    links: dict[str, list[str]] = {}
    for element_id, load_id in rows:
        links.setdefault(str(element_id), []).append(str(load_id))
    return links


def _build_snapshot(db: Session, project: Project) -> dict:
    return {
        'elements': [_serialize_element(el) for el in _list_elements(db, project.id)],
        'design_settings': project.design_settings or {},
        'load_links': _load_links(db, project.id),
    }


def _head_revision(db: Session, project_id: UUID) -> int:
    return db.scalar(select(func.max(ProjectDocument.revision)).where(ProjectDocument.project_id == project_id)) or 0


def ensure_baseline(db: Session, project: Project) -> None:
    """Materialize revision 1 from the live state when a project has no history.

    Runs for new projects at creation time and lazily for projects that existed
    before versioning, so undo always has a state to return to.
    """
    if _head_revision(db, project.id) > 0:
        return
    snapshot = _build_snapshot(db, project)
    document = ProjectDocument(project_id=project.id, revision=1, snapshot=snapshot)
    db.add(document)
    db.flush()
    for data in snapshot['elements']:
        db.add(ElementRevision(document_id=document.id, project_id=project.id, revision=1, element_id=UUID(data['id']), operation='baseline', after=data))
    project.current_revision = 1
    db.flush()


def _apply_elements(db: Session, project: Project, elements_data: list[dict]) -> None:
    existing = {el.id: el for el in _list_elements(db, project.id)}
    seen: set[UUID] = set()
    for data in elements_data:
        raw_id = data.get('id')
        element_id = UUID(str(raw_id)) if raw_id else uuid4()
        if element_id in existing:
            element = existing[element_id]
            element.element_type = ElementType(data['element_type'])
            for field in ELEMENT_FIELDS:
                setattr(element, field, data[field])
        else:
            element = ProjectElement(
                id=element_id,
                project_id=project.id,
                element_type=ElementType(data['element_type']),
                **{field: data[field] for field in ELEMENT_FIELDS},
            )
            created_at = data.get('created_at')
            if created_at:
                element.created_at = datetime.fromisoformat(created_at)
            db.add(element)
        seen.add(element_id)
    for element in existing.values():
        if element.id not in seen:
            db.delete(element)
    db.flush()


def _restore_load_links(db: Session, snapshot: dict) -> None:
    for element_id, load_ids in (snapshot.get('load_links') or {}).items():
        if not load_ids:
            continue
        db.execute(
            update(ElementLoad)
            .where(ElementLoad.id.in_([UUID(load_id) for load_id in load_ids]), ElementLoad.element_id.is_(None))
            .values(element_id=UUID(element_id))
        )


def _apply_snapshot(db: Session, project: Project, snapshot: dict) -> None:
    _apply_elements(db, project, snapshot.get('elements') or [])
    if 'design_settings' in snapshot:
        project.design_settings = snapshot['design_settings'] or {}
    db.flush()
    _restore_load_links(db, snapshot)
    db.flush()


def refresh_current_snapshot_links(db: Session, project_id: UUID) -> None:
    """Sync the current revision's ``load_links`` with live ``element_loads``.

    Loads mutate outside the document save flow; keeping the current snapshot
    accurate lets undo/restore re-link loads that were attached after the
    revision was written.
    """
    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project or project.current_revision == 0:
        return
    document = db.scalar(
        select(ProjectDocument).where(
            ProjectDocument.project_id == project_id,
            ProjectDocument.revision == project.current_revision,
        )
    )
    if not document:
        return
    document.snapshot = {**document.snapshot, 'load_links': _load_links(db, project_id)}
    db.flush()


def _fields_changed(before: dict, after: dict) -> bool:
    return any(before.get(field) != after.get(field) for field in ('element_type', *ELEMENT_FIELDS))


def _document_state(db: Session, project: Project) -> dict:
    head = _head_revision(db, project.id)
    return {
        'revision': project.current_revision,
        'head_revision': head,
        'can_undo': project.current_revision > 1,
        'can_redo': project.current_revision < head,
        'elements': _list_elements(db, project.id),
        'design_settings': project.design_settings or {},
    }


def _document_at(db: Session, project_id: UUID, revision: int) -> ProjectDocument:
    document = db.scalar(
        select(ProjectDocument).where(ProjectDocument.project_id == project_id, ProjectDocument.revision == revision)
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Revision not found')
    return document


def save_document(db: Session, user: User, project_id: UUID, payload: DocumentPayload) -> dict:
    project = _locked_owned_project(db, user, project_id)
    ensure_baseline(db, project)
    before = {el.id: _serialize_element(el) for el in _list_elements(db, project.id)}
    previous_settings = project.design_settings or {}

    _apply_elements(db, project, [item.model_dump() for item in payload.elements])
    if payload.name is not None:
        project.name = payload.name
    settings_changed = False
    if payload.design_settings is not None:
        project.design_settings = payload.design_settings.model_dump(exclude_unset=True)
        settings_changed = project.design_settings != previous_settings
    db.flush()

    after = {UUID(data['id']): data for data in _build_snapshot(db, project)['elements']}
    changes: list[tuple[str, UUID, dict | None, dict | None]] = []
    for element_id, after_data in after.items():
        before_data = before.get(element_id)
        if before_data is None:
            changes.append(('create', element_id, None, after_data))
        elif _fields_changed(before_data, after_data):
            changes.append(('update', element_id, before_data, after_data))
    for element_id, before_data in before.items():
        if element_id not in after:
            changes.append(('delete', element_id, before_data, None))

    if not changes and not settings_changed:
        db.commit()
        return _document_state(db, project)

    db.execute(delete(ProjectDocument).where(ProjectDocument.project_id == project.id, ProjectDocument.revision > project.current_revision))
    revision = project.current_revision + 1
    document = ProjectDocument(project_id=project.id, revision=revision, snapshot=_build_snapshot(db, project))
    db.add(document)
    db.flush()
    for operation, element_id, before_data, after_data in changes:
        db.add(ElementRevision(document_id=document.id, project_id=project.id, revision=revision, element_id=element_id, operation=operation, before=before_data, after=after_data))
    project.current_revision = revision
    db.commit()
    return _document_state(db, project)


def undo_document(db: Session, user: User, project_id: UUID) -> dict:
    project = _locked_owned_project(db, user, project_id)
    ensure_baseline(db, project)
    if project.current_revision <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Nothing to undo')
    target = project.current_revision - 1
    _apply_snapshot(db, project, _document_at(db, project.id, target).snapshot)
    project.current_revision = target
    db.commit()
    return _document_state(db, project)


def redo_document(db: Session, user: User, project_id: UUID) -> dict:
    project = _locked_owned_project(db, user, project_id)
    ensure_baseline(db, project)
    head = _head_revision(db, project.id)
    if project.current_revision >= head:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Nothing to redo')
    target = project.current_revision + 1
    _apply_snapshot(db, project, _document_at(db, project.id, target).snapshot)
    project.current_revision = target
    db.commit()
    return _document_state(db, project)


def restore_revision(db: Session, user: User, project_id: UUID, revision: int) -> dict:
    project = _locked_owned_project(db, user, project_id)
    ensure_baseline(db, project)
    document = _document_at(db, project.id, revision)
    _apply_snapshot(db, project, document.snapshot)
    project.current_revision = revision
    db.commit()
    return _document_state(db, project)


def get_history(db: Session, user: User, project_id: UUID, limit: int = 100) -> dict:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    documents = db.scalars(
        select(ProjectDocument)
        .where(ProjectDocument.project_id == project.id)
        .order_by(ProjectDocument.revision.desc())
        .limit(limit)
    ).all()
    document_ids = [doc.id for doc in documents]
    revisions = (
        db.scalars(select(ElementRevision).where(ElementRevision.document_id.in_(document_ids))).all()
        if document_ids
        else []
    )
    changes_by_document: dict[UUID, list[ElementRevision]] = {}
    for change in revisions:
        changes_by_document.setdefault(change.document_id, []).append(change)
    return {
        'current_revision': project.current_revision,
        'head_revision': _head_revision(db, project.id),
        'revisions': [
            {
                'revision': doc.revision,
                'created_at': doc.created_at,
                'changes': [
                    {'element_id': change.element_id, 'operation': change.operation, 'before': change.before, 'after': change.after}
                    for change in changes_by_document.get(doc.id, [])
                ],
            }
            for doc in documents
        ],
    }
