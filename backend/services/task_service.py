import logging
from datetime import datetime, timedelta, timezone

from backend.core.config import BOOKING_PENDING_EXPIRATION_HOURS
from backend.db.client import db
from backend.services.notifications_service import crear_notificacion_panel

logger = logging.getLogger(__name__)

SIN_COMPROBANTE = {"$in": [None, ""]}  # coincide con null, vacío o campo inexistente


async def cancelar_reservas_vencidas() -> int:
    """
    Cancela reservas "pendiente" que superaron el plazo de pago SIN haber enviado comprobante (6.2).

    Las reservas pendientes que SÍ tienen comprobante están esperando que el hotel verifique
    el pago: nunca se cancelan automáticamente (antes el bot las cancelaba a los 2 minutos).
    Devuelve cuántas reservas se cancelaron.
    """
    ahora = datetime.now(timezone.utc)
    limite_tiempo = ahora - timedelta(hours=BOOKING_PENDING_EXPIRATION_HOURS)

    filtro = {
        "estado": "pendiente",
        "created_at": {"$lt": limite_tiempo},
        "comprobante_archivo": SIN_COMPROBANTE,
        "comprobante_url": SIN_COMPROBANTE,  # comprobantes guardados antes de la migración
    }

    candidatas = await db.bookings.find(filtro, {"_id": 1, "cliente_id": 1}).to_list(length=None)
    motivo = (
        "Cancelación automática: no se recibió el comprobante de pago en "
        f"{BOOKING_PENDING_EXPIRATION_HOURS} horas."
    )

    canceladas = 0
    for reserva in candidatas:
        # Se repite el filtro en la actualización: si el admin la confirmó entretanto, no se toca.
        resultado = await db.bookings.update_one(
            {"_id": reserva["_id"], **filtro},
            {"$set": {
                "estado": "cancelada",
                "motivo_actualizacion": motivo,
                "updated_at": ahora,
                "actualizado_por": "Sistema (Bot)",
            }},
        )
        if resultado.modified_count == 0:
            continue
        canceladas += 1

        if reserva.get("cliente_id"):
            try:
                await crear_notificacion_panel(
                    user_id=str(reserva["cliente_id"]),
                    titulo="Reserva Cancelada",
                    mensaje=motivo + " Si ya realizaste el pago, contáctanos.",
                    tipo="danger",
                    icono="bi-x-circle-fill",
                )
            except Exception:
                logger.exception("No se pudo notificar la cancelación de la reserva %s", reserva["_id"])

    if canceladas:
        logger.info("Se cancelaron automáticamente %s reservas sin comprobante de pago.", canceladas)
    return canceladas
