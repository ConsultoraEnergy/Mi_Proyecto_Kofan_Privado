import re

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.app.core.errors import Conflict, NotFound
from backend.app.core.time import utcnow
from backend.app.db.client import get_db


def _collection():
    return get_db().users


def _duplicate_message(exc: DuplicateKeyError) -> str:
    text = str(exc)
    if "document_number" in text:
        return "El número de documento ya está registrado."
    return "El correo electrónico ya está registrado."


async def get_by_id(user_id: ObjectId) -> dict | None:
    return await _collection().find_one({"_id": user_id})


async def get_by_email(email: str) -> dict | None:
    return await _collection().find_one({"email": email.strip().lower()})


async def insert(doc: dict) -> dict:
    now = utcnow()
    doc = {**doc, "created_at": now, "updated_at": now}
    try:
        result = await _collection().insert_one(doc)
    except DuplicateKeyError as exc:
        raise Conflict(_duplicate_message(exc)) from exc
    doc["_id"] = result.inserted_id
    return doc


async def update(user_id: ObjectId, fields: dict) -> dict:
    """Actualiza y devuelve el documento. NotFound si se eliminó entre la lectura y la escritura."""
    try:
        updated = await _collection().find_one_and_update(
            {"_id": user_id},
            {"$set": {**fields, "updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as exc:
        raise Conflict(_duplicate_message(exc)) from exc
    if updated is None:
        raise NotFound("Usuario no encontrado.")
    return updated


async def search(query_text: str | None, role: str | None, skip: int, limit: int) -> tuple[list[dict], int]:
    query: dict = {}
    if role:
        query["role"] = role
    if query_text:
        pattern = re.escape(query_text.strip())  # 5.13: sin regex del cliente (evita ReDoS)
        query["$or"] = [
            {"full_name": {"$regex": pattern, "$options": "i"}},
            {"email": {"$regex": pattern, "$options": "i"}},
            {"document_number": {"$regex": pattern, "$options": "i"}},
        ]
    cursor = _collection().find(query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit), await _collection().count_documents(query)


async def count_by_role(role: str) -> int:
    return await _collection().count_documents({"role": role})
