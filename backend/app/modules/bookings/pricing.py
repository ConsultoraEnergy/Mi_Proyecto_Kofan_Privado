"""
Precio de una reserva (5.3 / RN-04): se calcula SIEMPRE en el backend a partir de la tarifa de la
habitación. Fase 4: aquí se integrarán tarifas por temporada y estancia mínima.
"""

from dataclasses import dataclass
from datetime import date

from backend.app.core.errors import Conflict, ValidationFailed
from backend.app.core.settings import get_settings

MAX_NIGHTS = 60


@dataclass(frozen=True)
class Quote:
    nights: int
    price_per_night: float
    total_amount: float
    deposit_percent: int
    deposit_amount: float


def validate_stay(check_in: date, check_out: date) -> int:
    nights = (check_out - check_in).days
    if nights < 1:
        raise ValidationFailed("La fecha de salida debe ser posterior a la fecha de entrada.")
    if nights > MAX_NIGHTS:
        raise ValidationFailed(f"La estadía máxima es de {MAX_NIGHTS} noches.")
    return nights


def deposit_for(total_amount: float) -> tuple[int, float]:
    percent = get_settings().deposit_percent
    return percent, round(total_amount * percent / 100, 2)


def quote(price_per_night: float, check_in: date, check_out: date) -> Quote:
    nights = validate_stay(check_in, check_out)
    if not price_per_night or price_per_night <= 0:
        raise Conflict("La habitación no tiene una tarifa válida configurada.")
    total = round(float(price_per_night) * nights, 2)
    percent, deposit = deposit_for(total)
    return Quote(
        nights=nights,
        price_per_night=float(price_per_night),
        total_amount=total,
        deposit_percent=percent,
        deposit_amount=deposit,
    )
