from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.app.modules.bookings.state_machine import BookingStatus
from backend.app.modules.users.schemas import (
    DocumentNumber,
    DocumentType,
    Name,
    NormalizedEmail,
    Phone,
)

Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GuestIn(_Strict):
    full_name: Name
    email: NormalizedEmail
    phone: Phone | None = None
    document_type: DocumentType | None = None
    document_number: DocumentNumber | None = None


class Companion(_Strict):
    full_name: Name
    document_type: DocumentType | None = None
    document_number: DocumentNumber | None = None
    relationship: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)] = ""


class WebBookingForm(BaseModel):
    """Formulario multipart de la reserva web (con comprobante adjunto aparte).
    No usa extra="forbid": FastAPI le pasa todos los campos del formulario, incluido el archivo."""

    model_config = ConfigDict(extra="ignore")

    room_id: str
    check_in: date
    check_out: date
    full_name: Name
    email: NormalizedEmail
    phone: Phone
    document_type: DocumentType | None = None
    document_number: DocumentNumber | None = None
    notes: Notes | None = None
    accept_privacy_policy: bool = False


class ManualBookingIn(_Strict):
    room_id: str
    check_in: date
    check_out: date
    guest: GuestIn
    companions: list[Companion] = Field(default_factory=list, max_length=20)
    notes: Notes | None = None
    # Precio negociado (requiere permiso bookings:override_price). Si no se envía, se calcula.
    total_amount: float | None = Field(default=None, gt=0)


class BookingUpdate(_Strict):
    check_in: date | None = None
    check_out: date | None = None
    guest: GuestIn | None = None
    companions: list[Companion] | None = Field(default=None, max_length=20)
    notes: Notes | None = None
    total_amount: float | None = Field(default=None, gt=0)


class StatusChangeIn(_Strict):
    status: BookingStatus
    reason: Reason | None = None


class StatusEvent(BaseModel):
    from_status: BookingStatus | None = None
    to_status: BookingStatus
    at: datetime
    by: str | None = None
    reason: str | None = None


class BookingRoom(BaseModel):
    id: str
    number: str
    name: str


class GuestOut(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    document_type: str | None = None
    document_number: str | None = None


class BookingOut(BaseModel):
    id: str
    code: str
    room: BookingRoom
    user_id: str | None = None
    guest: GuestOut
    companions: list[Companion] = []
    check_in: date
    check_out: date
    nights: int
    price_per_night: float
    calculated_amount: float
    total_amount: float
    deposit_percent: int
    deposit_amount: float
    status: BookingStatus
    payment_due_at: datetime | None = None
    has_receipt: bool
    # Ruta relativa a /api/v1 para descargar el comprobante con el token (None si no hay).
    receipt_url: str | None = None
    notes: str | None = None
    status_reason: str | None = None
    source: str
    created_at: datetime
    updated_at: datetime | None = None


class BookingDetailOut(BookingOut):
    """Vista del personal: incluye auditoría de estados y quién la creó."""

    created_by: str | None = None
    status_history: list[StatusEvent] = []


class BookingSummary(BaseModel):
    pending_verification: int
    pending_payment: int


class BookingPage(BaseModel):
    items: list[BookingDetailOut]
    total: int
    page: int
    limit: int
    summary: BookingSummary
