"""
Integración opcional con Sentry. Solo se activa si SENTRY_DSN tiene valor.

Los errores llegan a Sentry por dos vías: excepciones no controladas (registradas con
`logger.exception` por RequestContextMiddleware, que la LoggingIntegration convierte en evento) y
cualquier `logger.error(...)` explícito. Cada evento lleva la etiqueta `request_id`, que coincide con
la cabecera X-Request-ID devuelta al cliente y con los logs.

`send_default_pii=False`: no se envían cuerpos, cookies, cabeceras de autorización ni IPs (Ley 1581).
"""

import logging

import sentry_sdk

from backend.app.core.settings import Settings

logger = logging.getLogger(__name__)


def init_sentry(settings: Settings) -> bool:
    if settings.sentry_dsn is None or not settings.sentry_dsn.get_secret_value():
        return False
    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        environment=settings.app_env,
        release=settings.app_release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )
    logger.info("Sentry activado (entorno=%s)", settings.app_env)
    return True


def tag_request(request_id: str) -> None:
    """Asocia el request-id al scope de Sentry de la petición actual (no-op si Sentry está apagado)."""
    sentry_sdk.set_tag("request_id", request_id)
