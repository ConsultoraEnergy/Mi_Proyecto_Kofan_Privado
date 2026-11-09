"""Registro de auditoría genérico (habitaciones, reservas, usuarios...)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from backend.app.core.time import utcnow
from backend.app.db.client import get_db
from backend.app.db.utils import page_params

_IGNORED_FIELDS = {"updated_at", "updated_by", "created_at", "created_by", "_id", "id"}


class Change(BaseModel):
    field: str
    old: Any = None
    new: Any = None


class AuditLogOut(BaseModel):
    id: str
    entity: str
    entity_id: str
    entity_label: str | None = None
    action: str
    actor: str | None = None
    changes: list[Change] = []
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    limit: int


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return str(value)


def diff(before: dict, after: dict) -> list[dict]:
    changes = []
    for key, new_value in after.items():
        if key in _IGNORED_FIELDS:
            continue
        old_value = before.get(key)
        if isinstance(old_value, list) and isinstance(new_value, list):
            if sorted(map(str, old_value)) == sorted(map(str, new_value)):
                continue
        elif old_value == new_value:
            continue
        changes.append({"field": key, "old": _jsonable(old_value), "new": _jsonable(new_value)})
    return changes


async def record(
    entity: str,
    entity_id: Any,
    action: str,
    actor: str | None,
    *,
    label: str | None = None,
    changes: list[dict] | None = None,
) -> None:
    await get_db().audit_logs.insert_one({
        "entity": entity,
        "entity_id": str(entity_id),
        "entity_label": label,
        "action": action,
        "actor": actor,
        "changes": changes or [],
        "created_at": utcnow(),
    })


async def list_logs(entity: str | None, entity_id: str | None, page: int, limit: int) -> AuditPage:
    skip, limit = page_params(page, limit)
    query: dict = {}
    if entity:
        query["entity"] = entity
    if entity_id:
        query["entity_id"] = entity_id
    db = get_db()
    docs = await db.audit_logs.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.audit_logs.count_documents(query)
    return AuditPage(
        items=[AuditLogOut(id=str(d.pop("_id")), **d) for d in docs],
        total=total,
        page=page,
        limit=limit,
    )
