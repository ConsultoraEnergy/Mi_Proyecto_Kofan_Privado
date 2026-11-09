from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Code = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[a-z0-9-]{2,40}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
RoomNumber = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Amenity = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class OperationalStatus(StrEnum):
    """Estado operativo (6.5). La ocupación NO se guarda aquí: se deriva de las reservas."""
    AVAILABLE = "available"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Tipos de habitación (catálogo, reemplaza la detección por regex RN-10) ---

class RoomTypeIn(_Strict):
    code: Code
    name: Name
    description: str = Field(default="", max_length=1000)
    is_active: bool = True
    sort_order: int = 0


class RoomTypeUpdate(_Strict):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None
    sort_order: int | None = None


class RoomTypeOut(BaseModel):
    id: str
    code: str
    name: str
    description: str = ""
    is_active: bool
    sort_order: int = 0


# --- Habitaciones ---

class RoomIn(_Strict):
    number: RoomNumber
    name: Name
    room_type_id: str
    description: str = Field(default="", max_length=3000)
    price_per_night: float = Field(gt=0)
    capacity: int = Field(ge=1, le=50)
    bedrooms: int = Field(default=1, ge=1, le=20)
    beds: str = Field(default="", max_length=200)
    amenities: list[Amenity] = Field(default_factory=list, max_length=50)
    is_active: bool = True
    operational_status: OperationalStatus = OperationalStatus.AVAILABLE


class RoomUpdate(_Strict):
    number: RoomNumber | None = None
    name: Name | None = None
    room_type_id: str | None = None
    description: str | None = Field(default=None, max_length=3000)
    price_per_night: float | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, ge=1, le=50)
    bedrooms: int | None = Field(default=None, ge=1, le=20)
    beds: str | None = Field(default=None, max_length=200)
    amenities: list[Amenity] | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    operational_status: OperationalStatus | None = None
    main_image: str | None = None


class RoomOut(BaseModel):
    id: str
    number: str
    name: str
    room_type: RoomTypeOut | None = None
    description: str = ""
    price_per_night: float
    capacity: int
    bedrooms: int = 1
    beds: str = ""
    amenities: list[str] = []
    images: list[str] = []
    main_image: str | None = None
    is_active: bool
    operational_status: OperationalStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RoomPage(BaseModel):
    items: list[RoomOut]
    total: int
    page: int
    limit: int


class BookedRange(BaseModel):
    check_in: date
    check_out: date


class QuoteOut(BaseModel):
    room_id: str
    check_in: date
    check_out: date
    nights: int
    price_per_night: float
    total_amount: float
    deposit_percent: int
    deposit_amount: float
    currency: str


class AvailabilityOut(BaseModel):
    room: RoomOut
    quote: QuoteOut
