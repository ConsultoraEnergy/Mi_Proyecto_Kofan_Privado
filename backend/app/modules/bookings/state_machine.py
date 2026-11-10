"""
Máquina de estados de la reserva (6.4).

Flujo sin pasarela de pago (el huésped transfiere y sube el comprobante):

    pending_verification ──aprobar──▶ confirmed ──check-in──▶ checked_in ──check-out──▶ checked_out
        │   ▲                             │
        │   └──comprobante nuevo──┐       │
        ▼                         │       │
    pending_payment ◀──rechazar───┘       │
        │                                 │
        └──────────────┬──────────────────┘
                       ▼
                   cancelled   (también por vencimiento del plazo de pago)
"""

from enum import StrEnum

from backend.app.core.errors import Conflict, ValidationFailed


class BookingStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"  # falta comprobante (o fue rechazado)
    PENDING_VERIFICATION = "pending_verification"  # hay comprobante, el hotel debe revisarlo
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


S = BookingStatus

TRANSITIONS: dict[BookingStatus, frozenset[BookingStatus]] = {
    S.PENDING_PAYMENT: frozenset({S.PENDING_VERIFICATION, S.CONFIRMED, S.CANCELLED}),
    S.PENDING_VERIFICATION: frozenset({S.CONFIRMED, S.PENDING_PAYMENT, S.CANCELLED}),
    S.CONFIRMED: frozenset({S.CHECKED_IN, S.CANCELLED}),
    S.CHECKED_IN: frozenset({S.CHECKED_OUT}),
    S.CHECKED_OUT: frozenset(),
    S.CANCELLED: frozenset(),
}

# Estados que ocupan noches en el calendario de la habitación.
ACTIVE_STATUSES = frozenset({S.PENDING_PAYMENT, S.PENDING_VERIFICATION, S.CONFIRMED, S.CHECKED_IN})

# Estados en los que se pueden editar fechas y datos del huésped.
EDITABLE_STATUSES = ACTIVE_STATUSES

# Transiciones que exigen un motivo (se muestra al huésped).
REASON_REQUIRED = {
    (S.PENDING_VERIFICATION, S.PENDING_PAYMENT),  # comprobante rechazado
}

LABELS = {
    S.PENDING_PAYMENT: "Pendiente de pago",
    S.PENDING_VERIFICATION: "Pago por verificar",
    S.CONFIRMED: "Confirmada",
    S.CHECKED_IN: "Huésped en el hotel",
    S.CHECKED_OUT: "Finalizada",
    S.CANCELLED: "Cancelada",
}


def ensure_transition(current: BookingStatus, target: BookingStatus, reason: str | None) -> None:
    if target not in TRANSITIONS[current]:
        raise Conflict(
            f"No se puede pasar una reserva de '{LABELS[current]}' a '{LABELS[target]}'.",
            code="invalid_transition",
        )
    needs_reason = (current, target) in REASON_REQUIRED or target == S.CANCELLED
    if needs_reason and not (reason and reason.strip()):
        raise ValidationFailed("Indica el motivo de este cambio de estado.")
