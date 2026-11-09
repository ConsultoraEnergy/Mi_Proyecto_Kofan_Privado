"""
Índices y validación de esquema ($jsonSchema) de las colecciones.

`ensure_database()` es idempotente: crea las colecciones con su validador si no existen,
actualiza el validador si ya existen (collMod) y crea los índices que falten.
"""
import logging

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

_DATE = {"bsonType": "date"}
_DATE_OR_NULL = {"bsonType": ["date", "null"]}
_OID = {"bsonType": "objectId"}
_OID_OR_NULL = {"bsonType": ["objectId", "null"]}
_STR = {"bsonType": "string"}
_NON_EMPTY_STR = {"bsonType": "string", "minLength": 1}
_STR_OR_NULL = {"bsonType": ["string", "null"]}
_BOOL = {"bsonType": "bool"}
_NUMBER = {"bsonType": ["int", "long", "double", "decimal"]}
_POSITIVE_NUMBER = {"bsonType": ["int", "long", "double", "decimal"], "minimum": 0, "exclusiveMinimum": True}
_NON_NEGATIVE_NUMBER = {"bsonType": ["int", "long", "double", "decimal"], "minimum": 0}
_POSITIVE_INT = {"bsonType": ["int", "long"], "minimum": 1}

BOOKING_STATUSES = [
    "pending_payment", "pending_verification", "confirmed", "checked_in", "checked_out", "cancelled",
]

VALIDATORS: dict[str, dict] = {
    "users": {
        "bsonType": "object",
        "required": ["email", "full_name", "role", "is_active", "email_verified", "created_at"],
        "properties": {
            "email": {"bsonType": "string", "pattern": "^[^A-Z\\s]+@[^A-Z\\s]+$"},
            "full_name": _NON_EMPTY_STR,
            "password_hash": _STR_OR_NULL,
            "role": {"enum": ["admin", "receptionist", "client"]},
            "is_active": _BOOL,
            "email_verified": _BOOL,
            "person_type": {"enum": ["natural", "legal", None]},
            "document_type": {"enum": ["CC", "CE", "PASSPORT", "NIT", "TI", None]},
            "document_number": _STR_OR_NULL,
            "created_at": _DATE,
        },
    },
    "room_types": {
        "bsonType": "object",
        "required": ["code", "name", "is_active"],
        "properties": {
            "code": {"bsonType": "string", "pattern": "^[a-z0-9-]+$"},
            "name": _NON_EMPTY_STR,
            "is_active": _BOOL,
            "sort_order": {"bsonType": ["int", "long"]},
        },
    },
    "rooms": {
        "bsonType": "object",
        "required": [
            "number", "name", "room_type_id", "price_per_night", "capacity",
            "is_active", "operational_status", "images", "amenities",
        ],
        "properties": {
            "number": _NON_EMPTY_STR,
            "name": _NON_EMPTY_STR,
            "room_type_id": _OID,
            "price_per_night": _POSITIVE_NUMBER,
            "capacity": _POSITIVE_INT,
            "bedrooms": _POSITIVE_INT,
            "is_active": _BOOL,
            "operational_status": {"enum": ["available", "cleaning", "maintenance", "out_of_service"]},
            "images": {"bsonType": "array", "items": _STR},
            "amenities": {"bsonType": "array", "items": _STR},
        },
    },
    "bookings": {
        "bsonType": "object",
        "required": [
            "code", "room_id", "guest", "check_in", "check_out", "nights", "price_per_night",
            "total_amount", "deposit_amount", "status", "source", "created_at",
        ],
        "properties": {
            "code": _NON_EMPTY_STR,
            "room_id": _OID,
            "user_id": _OID_OR_NULL,
            "guest": {
                "bsonType": "object",
                "required": ["full_name", "email"],
                "properties": {"full_name": _NON_EMPTY_STR, "email": _NON_EMPTY_STR},
            },
            "check_in": _DATE,
            "check_out": _DATE,
            "nights": _POSITIVE_INT,
            "price_per_night": _POSITIVE_NUMBER,
            "total_amount": _NON_NEGATIVE_NUMBER,
            "deposit_amount": _NON_NEGATIVE_NUMBER,
            "status": {"enum": BOOKING_STATUSES},
            "payment_due_at": _DATE_OR_NULL,
            "source": {"enum": ["web", "manual"]},
            "companions": {"bsonType": "array"},
            "status_history": {"bsonType": "array"},
            "created_at": _DATE,
        },
    },
    "room_nights": {
        "bsonType": "object",
        "required": ["room_id", "night", "booking_id"],
        "properties": {"room_id": _OID, "night": _DATE, "booking_id": _OID},
    },
    "folios": {
        "bsonType": "object",
        "required": ["number", "booking_id", "room_subtotal", "charges", "total_amount", "status", "opened_at"],
        "properties": {
            "number": _POSITIVE_INT,
            "booking_id": _OID,
            "room_subtotal": _NON_NEGATIVE_NUMBER,
            "charges": {"bsonType": "array"},
            "total_amount": _NON_NEGATIVE_NUMBER,
            "status": {"enum": ["open", "closed"]},
            "opened_at": _DATE,
            "closed_at": _DATE_OR_NULL,
        },
    },
}

INDEXES: dict[str, list[IndexModel]] = {
    "users": [
        IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
        IndexModel(
            [("document_number", ASCENDING)],
            unique=True,
            partialFilterExpression={"document_number": {"$type": "string"}},
            name="uniq_document_number",
        ),
        IndexModel([("role", ASCENDING), ("created_at", DESCENDING)], name="role_created"),
    ],
    "room_types": [IndexModel([("code", ASCENDING)], unique=True, name="uniq_code")],
    "rooms": [
        IndexModel([("number", ASCENDING)], unique=True, name="uniq_number"),
        IndexModel(
            [("room_type_id", ASCENDING), ("is_active", ASCENDING), ("price_per_night", ASCENDING)],
            name="type_active_price",
        ),
    ],
    "bookings": [
        IndexModel([("code", ASCENDING)], unique=True, name="uniq_code"),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created"),
        IndexModel([("guest.email", ASCENDING)], name="guest_email"),
        IndexModel(
            [("room_id", ASCENDING), ("status", ASCENDING), ("check_in", ASCENDING), ("check_out", ASCENDING)],
            name="room_status_dates",
        ),
        IndexModel([("status", ASCENDING), ("payment_due_at", ASCENDING)], name="status_payment_due"),
        IndexModel([("status", ASCENDING), ("check_in", DESCENDING)], name="status_check_in"),
        IndexModel([("updated_at", DESCENDING)], name="updated"),
    ],
    # 6.1: garantía a nivel de BD contra la doble reserva: una noche de una habitación
    # solo puede pertenecer a una reserva activa.
    "room_nights": [
        IndexModel([("room_id", ASCENDING), ("night", ASCENDING)], unique=True, name="uniq_room_night"),
        IndexModel([("booking_id", ASCENDING)], name="booking"),
    ],
    "folios": [
        IndexModel([("booking_id", ASCENDING)], unique=True, name="uniq_booking"),
        IndexModel([("number", ASCENDING)], unique=True, name="uniq_number"),
        IndexModel([("status", ASCENDING), ("closed_at", DESCENDING)], name="status_closed"),
    ],
    "gallery": [IndexModel([("category", ASCENDING), ("created_at", DESCENDING)], name="category_created")],
    "notifications": [IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_created")],
    "refresh_tokens": [
        IndexModel([("token_hash", ASCENDING)], unique=True, name="uniq_token"),
        IndexModel([("family_id", ASCENDING)], name="family"),
        IndexModel([("user_id", ASCENDING)], name="user"),
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires"),
    ],
    "email_tokens": [
        IndexModel([("token_hash", ASCENDING)], unique=True, name="uniq_token"),
        IndexModel([("user_id", ASCENDING), ("purpose", ASCENDING)], name="user_purpose"),
        IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires"),
    ],
    "audit_logs": [
        IndexModel([("entity", ASCENDING), ("created_at", DESCENDING)], name="entity_created"),
        IndexModel([("entity_id", ASCENDING), ("created_at", DESCENDING)], name="entity_id_created"),
    ],
}


async def _ensure_validator(db: AsyncDatabase, name: str, schema: dict, existing: set[str]) -> None:
    validator = {"$jsonSchema": schema}
    if name not in existing:
        await db.create_collection(name, validator=validator, validationLevel="strict", validationAction="error")
        return
    try:
        await db.command({"collMod": name, "validator": validator, "validationLevel": "strict"})
    except OperationFailure as exc:  # p. ej. el usuario de BD no tiene permiso collMod
        logger.warning("No se pudo actualizar el validador de %s: %s", name, exc)


async def ensure_database(db: AsyncDatabase) -> None:
    existing = set(await db.list_collection_names())
    for name, schema in VALIDATORS.items():
        await _ensure_validator(db, name, schema, existing)
    for name, indexes in INDEXES.items():
        await db[name].create_indexes(indexes)
