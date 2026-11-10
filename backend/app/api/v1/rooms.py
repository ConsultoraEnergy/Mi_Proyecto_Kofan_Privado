from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from backend.app.api.deps import OptionalUser, require_permission
from backend.app.core.errors import Forbidden
from backend.app.core.permissions import Permission, has_permission
from backend.app.modules.bookings import service as bookings_service
from backend.app.modules.rooms import service
from backend.app.modules.rooms.schemas import (
    AvailabilityOut,
    BookedRange,
    QuoteOut,
    RoomIn,
    RoomOut,
    RoomPage,
    RoomTypeIn,
    RoomTypeOut,
    RoomTypeUpdate,
    RoomUpdate,
)

router = APIRouter(tags=["rooms"])

RoomsWriter = Annotated[dict, Depends(require_permission(Permission.ROOMS_WRITE))]


def _can_see_inactive(user: dict | None, requested: bool) -> bool:
    if not requested:
        return False
    if not user or not has_permission(user["role"], Permission.ROOMS_READ_ALL):
        raise Forbidden("No tienes permiso para ver habitaciones inactivas.")
    return True


# --- Tipos de habitación ---


@router.get("/room-types", response_model=list[RoomTypeOut])
async def list_room_types(user: OptionalUser, include_inactive: bool = False):
    return await service.list_types(_can_see_inactive(user, include_inactive))


@router.post("/room-types", response_model=RoomTypeOut, status_code=status.HTTP_201_CREATED)
async def create_room_type(data: RoomTypeIn, actor: RoomsWriter):
    return await service.create_type(actor, data)


@router.patch("/room-types/{type_id}", response_model=RoomTypeOut)
async def update_room_type(type_id: str, data: RoomTypeUpdate, actor: RoomsWriter):
    return await service.update_type(actor, type_id, data)


# --- Disponibilidad y cotización (públicas) ---


@router.get("/availability", response_model=AvailabilityOut)
async def availability(
    room_type: str = Query(min_length=2, max_length=40),
    check_in: date = Query(),
    check_out: date = Query(),
    guests: int = Query(default=1, ge=1, le=50),
):
    return await service.find_availability(room_type, check_in, check_out, guests)


# --- Habitaciones ---


@router.get("/rooms", response_model=RoomPage)
async def list_rooms(
    user: OptionalUser,
    room_type: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=100),
    include_inactive: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await service.list_rooms(
        include_inactive=_can_see_inactive(user, include_inactive), room_type=room_type, q=q, page=page, limit=limit
    )


@router.post("/rooms", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(data: RoomIn, actor: RoomsWriter):
    return await service.create_room(actor, data)


@router.get("/rooms/{room_id}", response_model=RoomOut)
async def get_room(room_id: str, user: OptionalUser):
    can_see_inactive = bool(user and has_permission(user["role"], Permission.ROOMS_READ_ALL))
    return await service.get_room(room_id, include_inactive=can_see_inactive)


@router.patch("/rooms/{room_id}", response_model=RoomOut)
async def update_room(room_id: str, data: RoomUpdate, actor: RoomsWriter):
    return await service.update_room(actor, room_id, data)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: str, actor: RoomsWriter):
    await service.delete_room(actor, room_id)


@router.post("/rooms/{room_id}/images", response_model=RoomOut)
async def add_room_images(room_id: str, actor: RoomsWriter, files: list[UploadFile] = File(...)):
    return await service.add_images(actor, room_id, files)


@router.delete("/rooms/{room_id}/images", response_model=RoomOut)
async def remove_room_image(room_id: str, actor: RoomsWriter, url: str = Query(max_length=300)):
    return await service.remove_image(actor, room_id, url)


@router.get("/rooms/{room_id}/booked-dates", response_model=list[BookedRange])
async def booked_dates(room_id: str):
    return await bookings_service.booked_ranges(room_id)


@router.get("/rooms/{room_id}/quote", response_model=QuoteOut)
async def quote(room_id: str, check_in: date = Query(), check_out: date = Query()):
    return await service.quote(room_id, check_in, check_out)
