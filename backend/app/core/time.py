"""
Manejo de fechas (7.8).

- Instantes (created_at, updated_at...): datetime UTC con zona; la API los devuelve en ISO-8601.
- Fechas de calendario (check-in/check-out, noches): se guardan como datetime UTC a medianoche
  y la API las expone como `date` (YYYY-MM-DD).
- La lógica de negocio que depende de "hoy" usa la zona horaria del hotel (zoneinfo).
"""
from datetime import date, datetime, time, timedelta, timezone

from backend.app.core.settings import get_settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hotel_today() -> date:
    return datetime.now(get_settings().tz).date()


def date_to_datetime(value: date) -> datetime:
    """Fecha de calendario -> datetime UTC a medianoche (formato de almacenamiento)."""
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def datetime_to_date(value: datetime | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def ensure_utc(value: datetime | None) -> datetime | None:
    """PyMongo devuelve datetimes sin zona (en UTC) salvo que se configure tz_aware."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def nights_between(check_in: date, check_out: date) -> list[date]:
    return [check_in + timedelta(days=i) for i in range((check_out - check_in).days)]


def start_of_month_utc(today: date | None = None) -> datetime:
    """Inicio del mes en curso según la zona del hotel, expresado en UTC."""
    settings = get_settings()
    today = today or hotel_today()
    local_start = datetime.combine(today.replace(day=1), time.min, tzinfo=settings.tz)
    return local_start.astimezone(timezone.utc)
