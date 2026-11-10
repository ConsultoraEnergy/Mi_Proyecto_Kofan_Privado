"""
Folios de huésped (antes "invoices"). NO es una factura electrónica DIAN (ver CLAUDE.md §11).

- Se abre automáticamente en el check-in y se cierra en el check-out.
- Numeración consecutiva (colección counters).
- El total SIEMPRE lo calcula el servidor: subtotal de alojamiento + cargos (6.6).
"""

from datetime import date, datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.app.core.errors import Conflict, NotFound
from backend.app.core.time import datetime_to_date, utcnow
from backend.app.db.client import get_db
from backend.app.db.utils import require_object_id

_RECOMPUTE_TOTAL = {"$set": {"total_amount": {"$add": ["$room_subtotal", {"$sum": "$charges.amount"}]}}}


class ChargeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
    amount: float = Field(gt=0, le=100_000_000)


class ChargeOut(BaseModel):
    id: str
    description: str
    amount: float
    created_at: datetime
    created_by: str | None = None


class FolioOut(BaseModel):
    id: str
    number: int
    booking_id: str
    booking_code: str
    guest_name: str
    guest_email: str
    guest_document: str | None = None
    guest_phone: str | None = None
    room_number: str
    room_name: str
    check_in: date
    check_out: date
    nights: int
    room_subtotal: float
    charges: list[ChargeOut]
    total_amount: float
    status: str
    opened_at: datetime
    closed_at: datetime | None = None


def to_out(doc: dict) -> FolioOut:
    return FolioOut(
        id=str(doc["_id"]),
        number=doc["number"],
        booking_id=str(doc["booking_id"]),
        booking_code=doc.get("booking_code", ""),
        guest_name=doc["guest"]["full_name"],
        guest_email=doc["guest"]["email"],
        guest_document=doc["guest"].get("document_number"),
        guest_phone=doc["guest"].get("phone"),
        room_number=doc["room"]["number"],
        room_name=doc["room"]["name"],
        check_in=datetime_to_date(doc["check_in"]),
        check_out=datetime_to_date(doc["check_out"]),
        nights=doc.get("nights", 0),
        room_subtotal=doc["room_subtotal"],
        charges=[
            ChargeOut(id=str(c["id"]), **{k: v for k, v in c.items() if k != "id"}) for c in doc.get("charges", [])
        ],
        total_amount=doc["total_amount"],
        status=doc["status"],
        opened_at=doc["opened_at"],
        closed_at=doc.get("closed_at"),
    )


async def _next_number() -> int:
    counter = await get_db().counters.find_one_and_update(
        {"_id": "folio"}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    if counter is None:  # imposible con upsert + AFTER; protege el tipado
        raise RuntimeError("No se pudo generar el consecutivo de folio.")
    return counter["seq"]


async def open_for_booking(booking: dict, actor: str | None) -> dict:
    existing = await get_db().folios.find_one({"booking_id": booking["_id"]})
    if existing:
        return existing
    doc = {
        "number": await _next_number(),
        "booking_id": booking["_id"],
        "booking_code": booking["code"],
        "guest": booking["guest"],
        "room": booking["room"],
        "check_in": booking["check_in"],
        "check_out": booking["check_out"],
        "nights": booking["nights"],
        "room_subtotal": booking["total_amount"],
        "charges": [],
        "total_amount": booking["total_amount"],
        "status": "open",
        "opened_at": utcnow(),
        "opened_by": actor,
        "closed_at": None,
    }
    try:
        result = await get_db().folios.insert_one(doc)
    except DuplicateKeyError:  # otro proceso lo abrió al mismo tiempo
        concurrent = await get_db().folios.find_one({"booking_id": booking["_id"]})
        if concurrent is None:
            raise
        return concurrent
    return {**doc, "_id": result.inserted_id}


async def sync_with_booking(booking: dict) -> None:
    """Si cambian fechas o precio de una reserva en curso, el folio abierto se actualiza."""
    await get_db().folios.update_one(
        {"booking_id": booking["_id"], "status": "open"},
        [
            {
                "$set": {
                    "room_subtotal": booking["total_amount"],
                    "check_in": booking["check_in"],
                    "check_out": booking["check_out"],
                    "nights": booking["nights"],
                    "guest": {"$literal": booking["guest"]},
                }
            },
            _RECOMPUTE_TOTAL,
        ],
    )


async def close_for_booking(booking_id: ObjectId, actor: str | None) -> None:
    await get_db().folios.update_one(
        {"booking_id": booking_id, "status": "open"},
        {"$set": {"status": "closed", "closed_at": utcnow(), "closed_by": actor}},
    )


async def get_by_booking(booking_id: str) -> FolioOut:
    doc = await get_db().folios.find_one({"booking_id": require_object_id(booking_id, "Folio")})
    if not doc:
        raise NotFound("Esta reserva aún no tiene folio (se abre en el check-in).")
    return to_out(doc)


async def _get_open(folio_id: str) -> ObjectId:
    oid = require_object_id(folio_id, "Folio")
    doc = await get_db().folios.find_one({"_id": oid}, {"status": 1})
    if not doc:
        raise NotFound("Folio no encontrado.")
    if doc["status"] != "open":
        raise Conflict("El folio está cerrado; no se pueden modificar sus cargos.")
    return oid


async def add_charge(folio_id: str, data: ChargeIn, actor: str) -> FolioOut:
    oid = await _get_open(folio_id)
    charge = {
        "id": ObjectId(),
        "description": data.description,
        "amount": round(data.amount, 2),
        "created_at": utcnow(),
        "created_by": actor,
    }
    doc = await get_db().folios.find_one_and_update(
        {"_id": oid, "status": "open"},
        [{"$set": {"charges": {"$concatArrays": ["$charges", [{"$literal": charge}]]}}}, _RECOMPUTE_TOTAL],
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise Conflict("El folio se cerró mientras se agregaba el cargo.")
    return to_out(doc)


async def remove_charge(folio_id: str, charge_id: str, actor: str) -> FolioOut:
    oid = await _get_open(folio_id)
    charge_oid = require_object_id(charge_id, "Cargo")
    doc = await get_db().folios.find_one_and_update(
        {"_id": oid, "status": "open", "charges.id": charge_oid},
        [
            {"$set": {"charges": {"$filter": {"input": "$charges", "cond": {"$ne": ["$$this.id", charge_oid]}}}}},
            _RECOMPUTE_TOTAL,
        ],
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        raise NotFound("Cargo no encontrado.")
    return to_out(doc)


async def revenue_since(since: datetime) -> float:
    rows = await (
        await get_db().folios.aggregate(
            [
                {"$match": {"status": "closed", "closed_at": {"$gte": since}}},
                {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}},
            ]
        )
    ).to_list(1)
    return float(rows[0]["total"]) if rows else 0.0
