"""
Tareas periódicas dentro del proceso web (temporal).

⚠️ Con varios workers/réplicas el job correría N veces. La operación es idempotente (cada
cancelación usa control optimista), pero en la Fase 3 debe moverse a un worker separado (ARQ).
Desactívalo con SCHEDULER_ENABLED=false en las réplicas que no deban ejecutarlo.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.app.core.settings import Settings
from backend.app.modules.bookings.service import expire_unpaid_bookings

logger = logging.getLogger(__name__)


def start_scheduler(settings: Settings) -> AsyncIOScheduler | None:
    if not settings.scheduler_enabled:
        return None
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        expire_unpaid_bookings,
        "interval",
        minutes=settings.booking_expiration_check_minutes,
        id="expire_unpaid_bookings",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler iniciado (revisión de pagos vencidos cada %s min).", settings.booking_expiration_check_minutes
    )
    return scheduler
