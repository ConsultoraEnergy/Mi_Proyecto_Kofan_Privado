from datetime import date

from fastapi import UploadFile

from backend.app.core.errors import Conflict, NotFound, ValidationFailed
from backend.app.core.settings import get_settings
from backend.app.db.utils import page_params, parse_object_id, require_object_id
from backend.app.modules.audit import service as audit
from backend.app.modules.bookings import pricing
from backend.app.modules.bookings import repository as bookings_repository
from backend.app.modules.media import storage
from backend.app.modules.rooms import repository
from backend.app.modules.rooms.schemas import (
    AvailabilityOut,
    QuoteOut,
    RoomIn,
    RoomOut,
    RoomPage,
    RoomTypeIn,
    RoomTypeOut,
    RoomTypeUpdate,
    RoomUpdate,
)


def type_to_out(doc: dict) -> RoomTypeOut:
    return RoomTypeOut(
        id=str(doc["_id"]),
        code=doc["code"],
        name=doc["name"],
        description=doc.get("description", ""),
        is_active=doc.get("is_active", True),
        sort_order=doc.get("sort_order", 0),
    )


def to_out(doc: dict, room_type: dict | None) -> RoomOut:
    return RoomOut(
        id=str(doc["_id"]),
        number=doc["number"],
        name=doc["name"],
        room_type=type_to_out(room_type) if room_type else None,
        description=doc.get("description", ""),
        price_per_night=doc["price_per_night"],
        capacity=doc["capacity"],
        bedrooms=doc.get("bedrooms", 1),
        beds=doc.get("beds", ""),
        amenities=doc.get("amenities", []),
        images=doc.get("images", []),
        main_image=doc.get("main_image"),
        is_active=doc["is_active"],
        operational_status=doc["operational_status"],
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


async def _with_types(docs: list[dict]) -> list[RoomOut]:
    types = await repository.get_types_by_ids([d["room_type_id"] for d in docs])
    return [to_out(d, types.get(d["room_type_id"])) for d in docs]


# ---------------------------------------------------------------------------
# Tipos de habitación
# ---------------------------------------------------------------------------


async def list_types(include_inactive: bool) -> list[RoomTypeOut]:
    return [type_to_out(d) for d in await repository.list_types(include_inactive)]


async def create_type(actor: dict, data: RoomTypeIn) -> RoomTypeOut:
    doc = await repository.insert_type(data.model_dump())
    await audit.record("room_type", doc["_id"], "create", actor["email"], label=doc["name"])
    return type_to_out(doc)


async def update_type(actor: dict, type_id: str, data: RoomTypeUpdate) -> RoomTypeOut:
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        raise ValidationFailed("No hay datos para actualizar.")
    doc = await repository.update_type(require_object_id(type_id, "Tipo de habitación"), fields)
    if not doc:
        raise NotFound("Tipo de habitación no encontrado.")
    await audit.record("room_type", doc["_id"], "update", actor["email"], label=doc["name"])
    return type_to_out(doc)


async def _require_type(type_id: str) -> dict:
    oid = parse_object_id(type_id)
    room_type = await repository.get_type(oid) if oid else None
    if not room_type:
        raise ValidationFailed("El tipo de habitación no existe.")
    return room_type


# ---------------------------------------------------------------------------
# Habitaciones
# ---------------------------------------------------------------------------


async def _get_doc(room_id: str, *, include_inactive: bool) -> dict:
    oid = parse_object_id(room_id)
    room = await repository.get(oid) if oid else None
    if not room or (not include_inactive and not room.get("is_active")):
        raise NotFound("Habitación no encontrada.")
    return room


async def list_rooms(
    *, include_inactive: bool, room_type: str | None, q: str | None, page: int, limit: int
) -> RoomPage:
    type_id = None
    if room_type:
        type_oid = parse_object_id(room_type)
        found = await repository.get_type_by_code(room_type) or (
            await repository.get_type(type_oid) if type_oid else None
        )
        if not found:
            return RoomPage(items=[], total=0, page=page, limit=limit)
        type_id = found["_id"]
    skip, limit = page_params(page, limit)
    docs, total = await repository.search(
        include_inactive=include_inactive, room_type_id=type_id, q=q, skip=skip, limit=limit
    )
    return RoomPage(items=await _with_types(docs), total=total, page=page, limit=limit)


async def get_room(room_id: str, *, include_inactive: bool) -> RoomOut:
    doc = await _get_doc(room_id, include_inactive=include_inactive)
    return to_out(doc, await repository.get_type(doc["room_type_id"]))


async def create_room(actor: dict, data: RoomIn) -> RoomOut:
    room_type = await _require_type(data.room_type_id)
    doc = await repository.insert(
        {
            **data.model_dump(mode="json", exclude={"room_type_id"}),
            "room_type_id": room_type["_id"],
            "images": [],
            "main_image": None,
            "created_by": actor["email"],
            "updated_by": actor["email"],
        }
    )
    await audit.record("room", doc["_id"], "create", actor["email"], label=doc["name"])
    return to_out(doc, room_type)


async def update_room(actor: dict, room_id: str, data: RoomUpdate) -> RoomOut:
    before = await _get_doc(room_id, include_inactive=True)
    fields = data.model_dump(mode="json", exclude_unset=True)
    if not fields:
        raise ValidationFailed("No hay datos para actualizar.")
    if "room_type_id" in fields:
        fields["room_type_id"] = (await _require_type(fields["room_type_id"]))["_id"]
    if "main_image" in fields and fields["main_image"] not in before.get("images", []):
        raise ValidationFailed("La imagen principal debe ser una de las fotos de la habitación.")
    updated = await repository.update(before["_id"], {**fields, "updated_by": actor["email"]})
    await audit.record(
        "room", before["_id"], "update", actor["email"], label=before["name"], changes=audit.diff(before, fields)
    )
    return to_out(updated, await repository.get_type(updated["room_type_id"]))


async def delete_room(actor: dict, room_id: str) -> None:
    room = await _get_doc(room_id, include_inactive=True)
    if await bookings_repository.room_has_bookings(room["_id"]):
        raise Conflict("La habitación tiene reservas registradas. Desactívala en lugar de eliminarla.")
    await repository.delete(room["_id"])
    for url in room.get("images", []):
        await storage.delete_public_file(url)
    await audit.record("room", room["_id"], "delete", actor["email"], label=room["name"])


async def add_images(actor: dict, room_id: str, files: list[UploadFile]) -> RoomOut:
    room = await _get_doc(room_id, include_inactive=True)
    urls = await storage.save_public_images(files)
    if not urls:
        raise ValidationFailed("Adjunta al menos una imagen.")
    set_fields = {"updated_by": actor["email"]}
    if not room.get("main_image"):
        set_fields["main_image"] = urls[0]
    updated = await repository.update(room["_id"], set_fields, {"$push": {"images": {"$each": urls}}})
    await audit.record(
        "room",
        room["_id"],
        "add_images",
        actor["email"],
        label=room["name"],
        changes=[{"field": "images", "old": None, "new": urls}],
    )
    return to_out(updated, await repository.get_type(updated["room_type_id"]))


async def remove_image(actor: dict, room_id: str, url: str) -> RoomOut:
    room = await _get_doc(room_id, include_inactive=True)
    images = room.get("images", [])
    if url not in images:
        raise NotFound("La imagen no pertenece a esta habitación.")
    remaining = [i for i in images if i != url]
    set_fields = {"images": remaining, "updated_by": actor["email"]}
    if room.get("main_image") == url:
        set_fields["main_image"] = remaining[0] if remaining else None
    updated = await repository.update(room["_id"], set_fields)
    await storage.delete_public_file(url)
    await audit.record(
        "room",
        room["_id"],
        "remove_image",
        actor["email"],
        label=room["name"],
        changes=[{"field": "images", "old": url, "new": None}],
    )
    return to_out(updated, await repository.get_type(updated["room_type_id"]))


# ---------------------------------------------------------------------------
# Cotización y disponibilidad (públicas)
# ---------------------------------------------------------------------------


def _quote_out(room: dict, check_in: date, check_out: date) -> QuoteOut:
    q = pricing.quote(room["price_per_night"], check_in, check_out)
    return QuoteOut(
        room_id=str(room["_id"]),
        check_in=check_in,
        check_out=check_out,
        nights=q.nights,
        price_per_night=q.price_per_night,
        total_amount=q.total_amount,
        deposit_percent=q.deposit_percent,
        deposit_amount=q.deposit_amount,
        currency=get_settings().currency,
    )


async def quote(room_id: str, check_in: date, check_out: date) -> QuoteOut:
    return _quote_out(await _get_doc(room_id, include_inactive=False), check_in, check_out)


async def find_availability(room_type_code: str, check_in: date, check_out: date, guests: int) -> AvailabilityOut:
    pricing.validate_stay(check_in, check_out)
    room_type = await repository.get_type_by_code(room_type_code.strip().lower())
    if not room_type or not room_type.get("is_active"):
        raise NotFound("Tipo de habitación no encontrado.")
    occupied = await bookings_repository.occupied_room_ids(check_in, check_out)
    room = await repository.find_cheapest_available(room_type["_id"], guests, occupied)
    if not room:
        raise NotFound(
            f"No hay habitaciones '{room_type['name']}' disponibles para {guests} huésped(es) en esas fechas.",
            code="no_availability",
        )
    return AvailabilityOut(room=to_out(room, room_type), quote=_quote_out(room, check_in, check_out))
