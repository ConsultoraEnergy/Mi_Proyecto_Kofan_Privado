import logging
from datetime import date, timedelta
from pathlib import Path

from bson import ObjectId
from fastapi import UploadFile

from backend.app.core.errors import Conflict, Forbidden, NotFound, ValidationFailed
from backend.app.core.permissions import Permission, has_permission
from backend.app.core.settings import get_settings
from backend.app.core.time import date_to_datetime, datetime_to_date, hotel_today, nights_between, utcnow
from backend.app.db.utils import page_params, parse_object_id, require_object_id
from backend.app.modules.audit import service as audit
from backend.app.modules.bookings import pricing, repository
from backend.app.modules.bookings.schemas import (
    BookingDetailOut,
    BookingOut,
    BookingPage,
    BookingSummary,
    BookingUpdate,
    ManualBookingIn,
    StatusEvent,
    WebBookingForm,
)
from backend.app.modules.bookings.state_machine import (
    EDITABLE_STATUSES,
    LABELS,
    BookingStatus,
    ensure_transition,
)
from backend.app.modules.folios import service as folios
from backend.app.modules.media import storage
from backend.app.modules.notifications import service as notifications
from backend.app.modules.rooms import repository as rooms_repository
from backend.app.modules.users import repository as users_repository

logger = logging.getLogger(__name__)

SYSTEM_ACTOR = "Sistema"
S = BookingStatus


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------


def _out_fields(doc: dict) -> dict:
    receipt = doc.get("receipt")
    history = doc.get("status_history", [])
    return dict(
        id=str(doc["_id"]),
        code=doc["code"],
        room={"id": str(doc["room_id"]), "number": doc["room"]["number"], "name": doc["room"]["name"]},
        user_id=str(doc["user_id"]) if doc.get("user_id") else None,
        guest=doc["guest"],
        companions=doc.get("companions", []),
        check_in=datetime_to_date(doc["check_in"]),
        check_out=datetime_to_date(doc["check_out"]),
        nights=doc["nights"],
        price_per_night=doc["price_per_night"],
        calculated_amount=doc.get("calculated_amount", doc["total_amount"]),
        total_amount=doc["total_amount"],
        deposit_percent=doc["deposit_percent"],
        deposit_amount=doc["deposit_amount"],
        status=doc["status"],
        payment_due_at=doc.get("payment_due_at"),
        has_receipt=bool(receipt),
        receipt_url=f"/bookings/{doc['_id']}/receipt" if receipt else None,
        notes=doc.get("notes"),
        status_reason=history[-1].get("reason") if history else None,
        source=doc["source"],
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),
    )


def to_out(doc: dict) -> BookingOut:
    return BookingOut(**_out_fields(doc))


def to_detail(doc: dict) -> BookingDetailOut:
    return BookingDetailOut(
        **_out_fields(doc),
        created_by=doc.get("created_by"),
        status_history=[StatusEvent(**e) for e in doc.get("status_history", [])],
    )


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


async def _bookable_room(room_id: str) -> dict:
    oid = parse_object_id(room_id)
    room = await rooms_repository.get(oid) if oid else None
    if not room or not room.get("is_active") or room.get("operational_status") == "out_of_service":
        raise NotFound("La habitación no existe o no está disponible para reservas.")
    return room


def _validate_dates(check_in: date, check_out: date) -> None:
    if check_in < hotel_today():
        raise ValidationFailed("La fecha de entrada no puede estar en el pasado.")
    pricing.validate_stay(check_in, check_out)


async def _get_or_404(booking_id: str) -> dict:
    booking = await repository.get(require_object_id(booking_id, "Reserva"))
    if not booking:
        raise NotFound("Reserva no encontrada.")
    return booking


def _is_owner(user: dict | None, booking: dict) -> bool:
    return bool(user and booking.get("user_id") and booking["user_id"] == user["_id"])


def _history_event(from_status: str | None, to_status: str, by: str | None, reason: str | None = None) -> dict:
    return {"from_status": from_status, "to_status": to_status, "at": utcnow(), "by": by, "reason": reason}


def _base_doc(room: dict, check_in: date, check_out: date, quote: pricing.Quote) -> dict:
    return {
        "room_id": room["_id"],
        "room": {"number": room["number"], "name": room["name"]},
        "check_in": date_to_datetime(check_in),
        "check_out": date_to_datetime(check_out),
        "nights": quote.nights,
        "price_per_night": quote.price_per_night,
        "calculated_amount": quote.total_amount,
        "total_amount": quote.total_amount,
        "deposit_percent": quote.deposit_percent,
        "deposit_amount": quote.deposit_amount,
        "companions": [],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


# ---------------------------------------------------------------------------
# Creación
# ---------------------------------------------------------------------------


async def create_web_booking(form: WebBookingForm, receipt: UploadFile, user: dict | None) -> BookingOut:
    """Reserva desde la web: el precio lo calcula el servidor (5.3) y el comprobante es obligatorio (RN-05)."""
    if form.accept_privacy_policy is not True:
        raise ValidationFailed("Debes aceptar la política de tratamiento de datos personales.")
    room = await _bookable_room(form.room_id)
    _validate_dates(form.check_in, form.check_out)
    quote = pricing.quote(room["price_per_night"], form.check_in, form.check_out)

    stored = await storage.save_private_receipt(receipt)
    doc = {
        **_base_doc(room, form.check_in, form.check_out, quote),
        "user_id": user["_id"] if user else None,
        "guest": form.model_dump(
            mode="json", include={"full_name", "email", "phone", "document_type", "document_number"}
        ),
        "notes": form.notes,
        "status": S.PENDING_VERIFICATION.value,
        "payment_due_at": None,
        "receipt": {"key": stored.key, "content_type": stored.content_type, "uploaded_at": utcnow()},
        "source": "web",
        "created_by": user["email"] if user else None,
        "status_history": [_history_event(None, S.PENDING_VERIFICATION.value, form.email)],
        "privacy_policy_accepted_at": utcnow(),
    }
    try:
        booking = await repository.insert_with_nights(doc, get_settings().booking_code_prefix)
    except BaseException:
        await storage.delete_private_receipt(stored.key)  # sin comprobantes huérfanos
        raise
    return to_out(booking)


async def create_manual_booking(actor: dict, data: ManualBookingIn) -> BookingDetailOut:
    """Reserva registrada por recepción: queda confirmada."""
    if data.total_amount is not None and not has_permission(actor["role"], Permission.BOOKINGS_OVERRIDE_PRICE):
        raise Forbidden("No tienes permiso para fijar un precio distinto a la tarifa.")
    room = await _bookable_room(data.room_id)
    _validate_dates(data.check_in, data.check_out)
    quote = pricing.quote(room["price_per_night"], data.check_in, data.check_out)

    doc = _base_doc(room, data.check_in, data.check_out, quote)
    if data.total_amount is not None:
        doc["total_amount"] = round(data.total_amount, 2)
        doc["deposit_percent"], doc["deposit_amount"] = pricing.deposit_for(doc["total_amount"])

    guest = data.guest.model_dump(mode="json")
    existing_user = await users_repository.get_by_email(guest["email"])
    doc.update(
        {
            "user_id": existing_user["_id"] if existing_user and existing_user.get("email_verified") else None,
            "guest": guest,
            "companions": [c.model_dump(mode="json") for c in data.companions],
            "notes": data.notes,
            "status": S.CONFIRMED.value,
            "payment_due_at": None,
            "receipt": None,
            "source": "manual",
            "created_by": actor["email"],
            "status_history": [
                _history_event(None, S.CONFIRMED.value, actor["email"], "Reserva registrada por el hotel")
            ],
        }
    )
    booking = await repository.insert_with_nights(doc, get_settings().booking_code_prefix)
    await audit.record("booking", booking["_id"], "create", actor["email"], label=booking["code"])
    return to_detail(booking)


# ---------------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------------


async def list_bookings(statuses: list[str] | None, q: str | None, page: int, limit: int) -> BookingPage:
    valid = {s.value for s in BookingStatus}
    statuses = [s for s in (statuses or []) if s in valid] or None
    skip, limit = page_params(page, limit)
    docs, total = await repository.search(statuses, q, skip, limit)
    counts = await repository.count_by_status([S.PENDING_VERIFICATION.value, S.PENDING_PAYMENT.value])
    return BookingPage(
        items=[to_detail(d) for d in docs],
        total=total,
        page=page,
        limit=limit,
        summary=BookingSummary(
            pending_verification=counts[S.PENDING_VERIFICATION.value],
            pending_payment=counts[S.PENDING_PAYMENT.value],
        ),
    )


async def my_bookings(user: dict) -> list[BookingOut]:
    return [to_out(d) for d in await repository.list_for_user(user["_id"])]


async def get_booking(user: dict, booking_id: str) -> BookingOut:
    booking = await _get_or_404(booking_id)
    if has_permission(user["role"], Permission.BOOKINGS_READ_ALL):
        return to_detail(booking)
    if _is_owner(user, booking):
        return to_out(booking)
    raise NotFound("Reserva no encontrada.")  # 404 para no revelar que existe


async def booked_ranges(room_id: str) -> list[dict]:
    oid = require_object_id(room_id, "Habitación")
    today = hotel_today()
    window = timedelta(days=get_settings().booked_dates_window_days)
    docs = await repository.booked_ranges(oid, today, today + window)
    return [{"check_in": datetime_to_date(d["check_in"]), "check_out": datetime_to_date(d["check_out"])} for d in docs]


# ---------------------------------------------------------------------------
# Comprobantes
# ---------------------------------------------------------------------------


async def receipt_file(user: dict, booking_id: str) -> tuple[Path, str]:
    booking = await _get_or_404(booking_id)
    allowed = _is_owner(user, booking) or has_permission(user["role"], Permission.BOOKINGS_VIEW_RECEIPTS)
    receipt = booking.get("receipt")
    path = storage.private_receipt_path(receipt["key"]) if (allowed and receipt) else None
    if path is None:
        raise NotFound("Comprobante no encontrado.")
    return path, booking["code"]


async def upload_receipt(user: dict, booking_id: str, file: UploadFile) -> BookingOut:
    """Nuevo comprobante (p. ej. tras un rechazo). Si la reserva esperaba pago, pasa a verificación."""
    booking = await _get_or_404(booking_id)
    if not (_is_owner(user, booking) or has_permission(user["role"], Permission.BOOKINGS_UPDATE)):
        raise NotFound("Reserva no encontrada.")
    status = BookingStatus(booking["status"])
    if status not in (S.PENDING_PAYMENT, S.PENDING_VERIFICATION):
        raise Conflict("Esta reserva ya no admite comprobantes.")

    stored = await storage.save_private_receipt(file)
    fields = {
        "receipt": {"key": stored.key, "content_type": stored.content_type, "uploaded_at": utcnow()},
        "status": S.PENDING_VERIFICATION.value,
        "payment_due_at": None,
    }
    push = None
    if status == S.PENDING_PAYMENT:
        push = {
            "status_history": _history_event(
                status.value, S.PENDING_VERIFICATION.value, user["email"], "Nuevo comprobante"
            )
        }
    updated = await repository.update(booking["_id"], fields, expected_status=status.value, push=push)
    if updated is None:
        await storage.delete_private_receipt(stored.key)
        raise Conflict("La reserva cambió mientras subías el comprobante. Recarga e intenta de nuevo.")
    if booking.get("receipt"):
        await storage.delete_private_receipt(booking["receipt"]["key"])
    return to_out(updated)


# ---------------------------------------------------------------------------
# Cambios de estado (6.4)
# ---------------------------------------------------------------------------

_NOTIFY = {
    S.CONFIRMED: (
        "¡Reserva confirmada!",
        "success",
        "bi-check-circle-fill",
        "Verificamos tu pago. Tu reserva {code} en '{room}' está confirmada. ¡Te esperamos!",
    ),
    S.PENDING_PAYMENT: (
        "Revisa tu comprobante",
        "warning",
        "bi-exclamation-triangle-fill",
        "No pudimos validar el pago de la reserva {code}: {reason}. Sube un nuevo comprobante.",
    ),
    S.CHECKED_IN: ("¡Bienvenido!", "info", "bi-house-door-fill", "Check-in registrado para la reserva {code}."),
    S.CHECKED_OUT: (
        "¡Gracias por tu visita!",
        "secondary",
        "bi-check2-all",
        "Check-out registrado para la reserva {code}.",
    ),
    S.CANCELLED: ("Reserva cancelada", "danger", "bi-x-circle-fill", "La reserva {code} fue cancelada: {reason}"),
}


async def change_status(
    actor_email: str, booking_id: str | ObjectId, target: BookingStatus, reason: str | None = None
) -> dict:
    booking = await repository.get(booking_id) if isinstance(booking_id, ObjectId) else await _get_or_404(booking_id)
    if booking is None:
        raise NotFound("Reserva no encontrada.")
    current = BookingStatus(booking["status"])
    ensure_transition(current, target, reason)

    today = hotel_today()
    if target == S.CHECKED_IN and datetime_to_date(booking["check_in"]) > today:
        raise Conflict(
            "El check-in solo se puede registrar desde la fecha de entrada. Edita las fechas si el huésped llegó antes."
        )

    fields: dict = {"status": target.value}
    if target == S.PENDING_PAYMENT:
        fields["payment_due_at"] = utcnow() + timedelta(hours=get_settings().booking_payment_deadline_hours)
    elif current == S.PENDING_PAYMENT:
        fields["payment_due_at"] = None

    updated = await repository.update(
        booking["_id"],
        fields,
        expected_status=current.value,
        push={"status_history": _history_event(current.value, target.value, actor_email, reason)},
    )
    if updated is None:
        raise Conflict("La reserva fue modificada por otra persona. Recarga e intenta de nuevo.")

    # Efectos colaterales
    if target == S.CANCELLED:
        await repository.release_nights(booking["_id"])
    elif target == S.CHECKED_IN:
        await folios.open_for_booking(updated, actor_email)
    elif target == S.CHECKED_OUT:
        await folios.close_for_booking(booking["_id"], actor_email)
        await repository.release_nights(booking["_id"], from_night=today)  # salida anticipada libera noches

    await audit.record(
        "booking",
        booking["_id"],
        f"status:{target.value}",
        actor_email,
        label=booking["code"],
        changes=[{"field": "status", "old": current.value, "new": target.value}],
    )

    if updated.get("user_id") and target in _NOTIFY:
        title, theme, icon, template = _NOTIFY[target]
        message = template.format(code=updated["code"], room=updated["room"]["name"], reason=reason or "")
        await notifications.notify_user(updated["user_id"], title, message, theme, icon)
    return updated


async def change_status_by_staff(
    actor: dict, booking_id: str, target: BookingStatus, reason: str | None
) -> BookingDetailOut:
    return to_detail(await change_status(actor["email"], booking_id, target, reason))


async def expire_unpaid_bookings() -> int:
    """6.2: cancela solo reservas 'pendiente de pago' cuyo plazo venció. Las que tienen comprobante
    por verificar NUNCA se cancelan automáticamente."""
    hours = get_settings().booking_payment_deadline_hours
    cancelled = 0
    for booking in await repository.expired_unpaid(utcnow()):
        try:
            await change_status(
                SYSTEM_ACTOR, booking["_id"], S.CANCELLED, f"no recibimos un comprobante válido en {hours} horas"
            )
            cancelled += 1
        except Conflict:
            continue  # alguien la modificó entretanto
    if cancelled:
        logger.info("Reservas canceladas por vencimiento del plazo de pago: %s", cancelled)
    return cancelled


# ---------------------------------------------------------------------------
# Edición (fechas, huésped, acompañantes)
# ---------------------------------------------------------------------------


async def update_booking(actor: dict, booking_id: str, data: BookingUpdate) -> BookingDetailOut:
    booking = await _get_or_404(booking_id)
    status = BookingStatus(booking["status"])
    if status not in EDITABLE_STATUSES:
        raise Conflict(f"No se puede editar una reserva en estado '{LABELS[status]}'.")
    if data.total_amount is not None and not has_permission(actor["role"], Permission.BOOKINGS_OVERRIDE_PRICE):
        raise Forbidden("No tienes permiso para fijar un precio distinto a la tarifa.")

    fields: dict = {}
    old_in, old_out = datetime_to_date(booking["check_in"]), datetime_to_date(booking["check_out"])
    new_in, new_out = data.check_in or old_in, data.check_out or old_out
    dates_changed = (new_in, new_out) != (old_in, old_out)

    if dates_changed:
        if status == S.CHECKED_IN and new_in != old_in:
            raise ValidationFailed("El huésped ya hizo check-in: solo se puede cambiar la fecha de salida.")
        if status != S.CHECKED_IN and new_in < hotel_today():
            raise ValidationFailed("La fecha de entrada no puede estar en el pasado.")
        # La tarifa por noche queda fija desde la creación de la reserva.
        quote = pricing.quote(booking["price_per_night"], new_in, new_out)

        old_nights, new_nights = set(nights_between(old_in, old_out)), set(nights_between(new_in, new_out))
        to_add, to_remove = sorted(new_nights - old_nights), sorted(old_nights - new_nights)
        await repository.reserve_nights(booking["room_id"], booking["_id"], to_add)  # Conflict si choca
        await repository.release_nights(booking["_id"], only=to_remove)
        fields.update(
            {
                "check_in": date_to_datetime(new_in),
                "check_out": date_to_datetime(new_out),
                "nights": quote.nights,
                "calculated_amount": quote.total_amount,
                "total_amount": quote.total_amount,
            }
        )

    if data.total_amount is not None:
        fields["total_amount"] = round(data.total_amount, 2)
    if "total_amount" in fields:
        fields["deposit_percent"], fields["deposit_amount"] = pricing.deposit_for(fields["total_amount"])
    if data.guest is not None:
        fields["guest"] = data.guest.model_dump(mode="json")
    if data.companions is not None:
        fields["companions"] = [c.model_dump(mode="json") for c in data.companions]
    if "notes" in data.model_fields_set:
        fields["notes"] = data.notes
    if not fields:
        raise ValidationFailed("No hay cambios para guardar.")

    updated = await repository.update(booking["_id"], fields, expected_status=status.value)
    if updated is None:
        if dates_changed:  # deshacer el cambio de noches
            await repository.release_nights(booking["_id"], only=to_add)
            await repository.reserve_nights(booking["room_id"], booking["_id"], to_remove)
        raise Conflict("La reserva fue modificada por otra persona. Recarga e intenta de nuevo.")

    await folios.sync_with_booking(updated)
    await audit.record(
        "booking", booking["_id"], "update", actor["email"], label=booking["code"], changes=audit.diff(booking, fields)
    )
    return to_detail(updated)
