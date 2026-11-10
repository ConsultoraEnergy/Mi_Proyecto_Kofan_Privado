from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from backend.app.api.deps import CurrentUser, OptionalUser, require_permission
from backend.app.core.permissions import Permission
from backend.app.modules.bookings import service
from backend.app.modules.bookings.schemas import (
    BookingDetailOut,
    BookingOut,
    BookingPage,
    BookingUpdate,
    ManualBookingIn,
    StatusChangeIn,
    WebBookingForm,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_web_booking(
    user: OptionalUser,
    form: Annotated[WebBookingForm, Form()],
    receipt: UploadFile = File(..., description="Comprobante de pago (JPEG, PNG, WebP o PDF)"),
):
    """Reserva web (invitado o con sesión). El precio lo calcula el servidor."""
    return await service.create_web_booking(form, receipt, user)


@router.post("/manual", response_model=BookingDetailOut, status_code=status.HTTP_201_CREATED)
async def create_manual_booking(
    data: ManualBookingIn,
    actor: Annotated[dict, Depends(require_permission(Permission.BOOKINGS_CREATE_MANUAL))],
):
    return await service.create_manual_booking(actor, data)


@router.get("", response_model=BookingPage)
async def list_bookings(
    _: Annotated[dict, Depends(require_permission(Permission.BOOKINGS_READ_ALL))],
    status_filter: str | None = Query(
        default=None, alias="status", max_length=200, description="Estados separados por coma"
    ),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    statuses = [s.strip() for s in status_filter.split(",")] if status_filter else None
    return await service.list_bookings(statuses, q, page, limit)


@router.get("/mine", response_model=list[BookingOut])
async def my_bookings(user: CurrentUser):
    return await service.my_bookings(user)


@router.get("/{booking_id}", response_model=BookingDetailOut | BookingOut)
async def get_booking(booking_id: str, user: CurrentUser):
    return await service.get_booking(user, booking_id)


@router.patch("/{booking_id}", response_model=BookingDetailOut)
async def update_booking(
    booking_id: str,
    data: BookingUpdate,
    actor: Annotated[dict, Depends(require_permission(Permission.BOOKINGS_UPDATE))],
):
    return await service.update_booking(actor, booking_id, data)


@router.post("/{booking_id}/status", response_model=BookingDetailOut)
async def change_status(
    booking_id: str,
    data: StatusChangeIn,
    actor: Annotated[dict, Depends(require_permission(Permission.BOOKINGS_CHANGE_STATUS))],
):
    return await service.change_status_by_staff(actor, booking_id, data.status, data.reason)


@router.get("/{booking_id}/receipt")
async def download_receipt(booking_id: str, user: CurrentUser):
    """Comprobante privado (5.6): solo el dueño de la reserva o el personal autorizado."""
    receipt, code = await service.receipt_file(user, booking_id)
    return Response(
        content=receipt.content,
        media_type=receipt.content_type,
        headers={
            "Content-Disposition": f'inline; filename="comprobante-{code}.{receipt.extension}"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{booking_id}/receipt", response_model=BookingOut)
async def upload_receipt(booking_id: str, user: CurrentUser, receipt: UploadFile = File(...)):
    return await service.upload_receipt(user, booking_id, receipt)
