import re

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.app.core.errors import Conflict, NotFound
from backend.app.core.time import utcnow
from backend.app.db.client import get_db

# --- Tipos ---


async def list_types(include_inactive: bool) -> list[dict]:
    query = {} if include_inactive else {"is_active": True}
    return await get_db().room_types.find(query).sort([("sort_order", 1), ("name", 1)]).to_list(None)


async def get_type(type_id: ObjectId) -> dict | None:
    return await get_db().room_types.find_one({"_id": type_id})


async def get_type_by_code(code: str) -> dict | None:
    return await get_db().room_types.find_one({"code": code})


async def get_types_by_ids(ids: list[ObjectId]) -> dict[ObjectId, dict]:
    docs = await get_db().room_types.find({"_id": {"$in": list(set(ids))}}).to_list(None)
    return {d["_id"]: d for d in docs}


async def insert_type(doc: dict) -> dict:
    now = utcnow()
    doc = {**doc, "created_at": now, "updated_at": now}
    try:
        result = await get_db().room_types.insert_one(doc)
    except DuplicateKeyError as exc:
        raise Conflict("Ya existe un tipo de habitación con ese código.") from exc
    return {**doc, "_id": result.inserted_id}


async def update_type(type_id: ObjectId, fields: dict) -> dict | None:
    return await get_db().room_types.find_one_and_update(
        {"_id": type_id}, {"$set": {**fields, "updated_at": utcnow()}}, return_document=ReturnDocument.AFTER
    )


# --- Habitaciones ---


async def get(room_id: ObjectId) -> dict | None:
    return await get_db().rooms.find_one({"_id": room_id})


async def insert(doc: dict) -> dict:
    now = utcnow()
    doc = {**doc, "created_at": now, "updated_at": now}
    try:
        result = await get_db().rooms.insert_one(doc)
    except DuplicateKeyError as exc:
        raise Conflict("Ya existe una habitación con ese número.") from exc
    return {**doc, "_id": result.inserted_id}


async def update(room_id: ObjectId, set_fields: dict, extra: dict | None = None) -> dict:
    """Actualiza y devuelve el documento. NotFound si se eliminó entre la lectura y la escritura."""
    operation = {"$set": {**set_fields, "updated_at": utcnow()}, **(extra or {})}
    try:
        updated = await get_db().rooms.find_one_and_update(
            {"_id": room_id}, operation, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as exc:
        raise Conflict("Ya existe una habitación con ese número.") from exc
    if updated is None:
        raise NotFound("Habitación no encontrada.")
    return updated


async def delete(room_id: ObjectId) -> bool:
    return (await get_db().rooms.delete_one({"_id": room_id})).deleted_count > 0


def _filters(*, include_inactive: bool, room_type_id: ObjectId | None, q: str | None) -> dict:
    query: dict = {}
    if not include_inactive:
        query["is_active"] = True
    if room_type_id:
        query["room_type_id"] = room_type_id
    if q:
        pattern = re.escape(q.strip())  # 5.13: búsqueda sin regex del cliente
        query["$or"] = [
            {"name": {"$regex": pattern, "$options": "i"}},
            {"number": {"$regex": pattern, "$options": "i"}},
        ]
    return query


async def search(
    *, include_inactive: bool, room_type_id: ObjectId | None, q: str | None, skip: int, limit: int
) -> tuple[list[dict], int]:
    query = _filters(include_inactive=include_inactive, room_type_id=room_type_id, q=q)
    # 8.4: conteo y página en una sola consulta
    result = await (
        await get_db().rooms.aggregate(
            [
                {"$match": query},
                {
                    "$facet": {
                        "items": [{"$sort": {"number": 1}}, {"$skip": skip}, {"$limit": limit}],
                        "total": [{"$count": "n"}],
                    }
                },
            ]
        )
    ).to_list(1)
    facet = result[0] if result else {"items": [], "total": []}
    return facet["items"], (facet["total"][0]["n"] if facet["total"] else 0)


async def find_cheapest_available(room_type_id: ObjectId, guests: int, excluded_ids: list[ObjectId]) -> dict | None:
    """8.3: el filtro, el orden y el límite se resuelven en MongoDB, no en Python."""
    return await get_db().rooms.find_one(
        {
            "room_type_id": room_type_id,
            "is_active": True,
            "operational_status": {"$ne": "out_of_service"},
            "capacity": {"$gte": guests},
            "_id": {"$nin": excluded_ids},
        },
        sort=[("price_per_night", 1), ("number", 1)],
    )


async def count(query: dict | None = None) -> int:
    return await get_db().rooms.count_documents(query or {})
