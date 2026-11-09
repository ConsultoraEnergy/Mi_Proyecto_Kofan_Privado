"""
Cálculo del precio de una reserva (5.3 / RN-04).

El precio SIEMPRE se calcula en el backend a partir de la tarifa guardada en la habitación.
Cualquier `monto_total` enviado por el cliente se ignora.
"""
from datetime import date

from fastapi import HTTPException, status

from backend.core.config import DEPOSIT_PERCENT


def _precio_noche(habitacion: dict) -> float:
    try:
        precio = float(habitacion.get("price"))
    except (TypeError, ValueError):
        precio = 0.0
    if precio <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La habitación no tiene una tarifa válida configurada. Contacta al hotel.",
        )
    return precio


def calcular_noches(fecha_entrada: date, fecha_salida: date) -> int:
    noches = (fecha_salida - fecha_entrada).days
    if noches < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de salida debe ser posterior a la fecha de entrada.",
        )
    return noches


def calcular_anticipo(monto_total: float, porcentaje: int = DEPOSIT_PERCENT) -> float:
    return round(monto_total * porcentaje / 100, 2)


def calcular_precio_reserva(habitacion: dict, fecha_entrada: date, fecha_salida: date) -> dict:
    """Devuelve el desglose de precio: noches, precio por noche, total y anticipo."""
    noches = calcular_noches(fecha_entrada, fecha_salida)
    precio_noche = _precio_noche(habitacion)
    monto_total = round(precio_noche * noches, 2)
    return {
        "noches": noches,
        "precio_noche": precio_noche,
        "monto_total": monto_total,
        "porcentaje_anticipo": DEPOSIT_PERCENT,
        "anticipo": calcular_anticipo(monto_total),
    }
