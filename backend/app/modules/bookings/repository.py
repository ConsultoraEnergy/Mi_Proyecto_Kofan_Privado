import re
import secrets
from datetime import date

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import BulkWriteError, DuplicateKeyError

from backend.app.core.errors import Conflict
from backend.app.core.time import date_to_datetime, nights_between, utcnow
from backend.app.db.client import get_db
from backend.app.modules.bookings.state_machine import ACTIVE_STATUSES

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin caracteres ambiguos (0/O, 1/I/L)
UNAVAILABLE_MESSAGE = "La habitación ya está reservada en esas fechas."


def _new_code(prefix: str) -> str:
    return prefix + "-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))


# ---------------------------------------------------------------------------
# Noches ocupadas (6.1): índice único (room_id, night)
# ---------------------------------------------------------------------------


async def reserve_nights(room_id: ObjectId, booking_id: ObjectId, nights: list[date]) -> None:
    """Ocupa las noches indicadas. Si alguna ya pertenece a otra reserva, deshace lo insertado
    por esta llamada y lanza Conflict. El índice único hace imposible la doble reserva aunque
    lleguen peticiones simultáneas."""
    if not nights:
        return
    now = utcnow()
    docs = [
        {
            "_id": ObjectId(),
            "room_id": room_id,
            "night": date_to_datetime(n),
            "booking_id": booking_id,
            "created_at": now,
        }
        for n in nights
    ]
    try:
        await get_db().room_nights.insert_many(docs, ordered=True)
    except BulkWriteError as exc:
        await get_db().room_nights.delete_many({"_id": {"$in": [d["_id"] for d in docs]}})
        raise Conflict(UNAVAILABLE_MESSAGE, code="room_unavailable") from exc


async def release_nights(booking_id: ObjectId, from_night: date | None = None, only: list[date] | None = None) -> None:
    query: dict = {"booking_id": booking_id}
    if from_night is not None:
        query["night"] = {"$gte": date_to_datetime(from_night)}
    if only is not None:
        query["night"] = {"$in": [date_to_datetime(n) for n in only]}
    await get_db().room_nights.delete_many(query)


async def occupied_room_ids(check_in: date, check_out: date) -> list[ObjectId]:
    return await get_db().room_nights.distinct(
        "room_id",
        {"night": {"$gte": date_to_datetime(check_in), "$lt": date_to_datetime(check_out)}},
    )


async def occupied_rooms_on(night: date) -> int:
    return len(await get_db().room_nights.distinct("room_id", {"night": date_to_datetime(night)}))


async def room_has_bookings(room_id: ObjectId) -> bool:
    return await get_db().bookings.count_documents({"room_id": room_id}, limit=1) > 0


# ---------------------------------------------------------------------------
# Reservas
# ---------------------------------------------------------------------------


async def insert_with_nights(doc: dict, code_prefix: str) -> dict:
    booking_id = ObjectId()
    doc = {**doc, "_id": booking_id}
    nights = nights_between(doc["check_in"].date(), doc["check_out"].date())
    await reserve_nights(doc["room_id"], booking_id, nights)
    try:
        for _ in range(5):
            doc["code"] = _new_code(code_prefix)
            try:
                await get_db().bookings.insert_one(doc)
                return doc
            except DuplicateKeyError:
                continue  # colisión de código: se genera otro
        raise RuntimeError("No se pudo generar un código de reserva único.")
    except BaseException:
        await release_nights(booking_id)
        raise


async def get(booking_id: ObjectId) -> dict | None:
    return await get_db().bookings.find_one({"_id": booking_id})


async def update(
    booking_id: ObjectId, set_fields: dict, *, expected_status: str | None = None, push: dict | None = None
) -> dict | None:
    """Actualización con control optimista del estado: si otro usuario cambió el estado entretanto,
    no se aplica y devuelve None."""
    query: dict = {"_id": booking_id}
    if expected_status is not None:
        query["status"] = expected_status
    operation: dict = {"$set": {**set_fields, "updated_at": utcnow()}}
    if push:
        operation["$push"] = push
    return await get_db().bookings.find_one_and_update(query, operation, return_document=ReturnDocument.AFTER)


async def link_guest_bookings(email: str, user_id: ObjectId) -> int:
    """Vincula reservas de invitado con igualdad EXACTA de correo. Solo tras verificar el email (5.5)."""
    result = await get_db().bookings.update_many(
        {"guest.email": email.strip().lower(), "user_id": None},
        {"$set": {"user_id": user_id, "updated_at": utcnow()}},
    )
    return result.modified_count


async def list_for_user(user_id: ObjectId) -> list[dict]:
    return await get_db().bookings.find({"user_id": user_id}).sort("check_in", -1).to_list(200)


async def search(statuses: list[str] | None, q: str | None, skip: int, limit: int) -> tuple[list[dict], int]:
    query: dict = {}
    if statuses:
        query["status"] = {"$in": statuses}
    if q:
        pattern = re.escape(q.strip())
        query["$or"] = [
            {"code": {"$regex": pattern, "$options": "i"}},
            {"guest.full_name": {"$regex": pattern, "$options": "i"}},
            {"guest.email": {"$regex": pattern, "$options": "i"}},
            {"guest.document_number": {"$regex": pattern, "$options": "i"}},
            {"room.number": {"$regex": pattern, "$options": "i"}},
        ]
    result = await (
        await get_db().bookings.aggregate(
            [
                {"$match": query},
                {
                    "$facet": {
                        "items": [{"$sort": {"check_in": -1, "created_at": -1}}, {"$skip": skip}, {"$limit": limit}],
                        "total": [{"$count": "n"}],
                    }
                },
            ]
        )
    ).to_list(1)
    facet = result[0] if result else {"items": [], "total": []}
    return facet["items"], (facet["total"][0]["n"] if facet["total"] else 0)


async def count_by_status(statuses: list[str]) -> dict[str, int]:
    rows = await (
        await get_db().bookings.aggregate(
            [
                {"$match": {"status": {"$in": statuses}}},
                {"$group": {"_id": "$status", "n": {"$sum": 1}}},
            ]
        )
    ).to_list(None)
    counts = {s: 0 for s in statuses}
    counts.update({r["_id"]: r["n"] for r in rows})
    return counts


async def booked_ranges(room_id: ObjectId, from_date: date, to_date: date) -> list[dict]:
    """8.4: solo reservas activas dentro de la ventana consultada."""
    return (
        await get_db()
        .bookings.find(
            {
                "room_id": room_id,
                "status": {"$in": [s.value for s in ACTIVE_STATUSES]},
                "check_out": {"$gt": date_to_datetime(from_date)},
                "check_in": {"$lt": date_to_datetime(to_date)},
            },
            {"check_in": 1, "check_out": 1, "_id": 0},
        )
        .sort("check_in", 1)
        .to_list(1000)
    )


async def expired_unpaid(now) -> list[dict]:
    return (
        await get_db()
        .bookings.find(
            {"status": "pending_payment", "payment_due_at": {"$lt": now}},
        )
        .to_list(500)
    )
