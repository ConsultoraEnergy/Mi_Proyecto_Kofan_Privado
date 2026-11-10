"""
Logging estructurado y correlación de peticiones.

- `configure_logging()` instala un único handler en el logger raíz: JSON (una línea por evento, apto
  para agregadores de logs) o texto legible para desarrollo. Los loggers de uvicorn se redirigen a
  ese handler y su access log se reemplaza por el de `RequestContextMiddleware`.
- `RequestContextMiddleware` asigna a cada petición un request-id (respeta `X-Request-ID` entrante si
  es válido), lo publica en la cabecera de respuesta, lo agrega a todos los logs emitidos durante la
  petición y registra una línea de acceso con estado y duración. Si la aplicación lanza una excepción
  no controlada, responde 500 con el request-id (sin filtrar detalles internos al cliente).
"""

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.sentry import tag_request

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
_QUIET_PATHS = {"/health", "/ready"}

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

access_logger = logging.getLogger("backend.access")
error_logger = logging.getLogger("backend.errors")

# Atributos estándar de LogRecord: todo lo demás se considera un campo `extra` del evento.
_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime", "request_id"}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            event["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _RECORD_ATTRS and not key.startswith("_"):
                event[key] = value
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(name)s%(rid)s: %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", None)
        record.rid = f" [{rid}]" if rid else ""
        return super().format(record)


def configure_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configura el logging de la aplicación. Es idempotente (se puede llamar varias veces)."""
    root = logging.getLogger()
    for handler in [h for h in root.handlers if getattr(h, "_kawari", False)]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler._kawari = True  # type: ignore[attr-defined]
    handler.setFormatter(JsonFormatter() if fmt == "json" else TextFormatter())
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)
    root.setLevel(level.upper())

    # uvicorn trae sus propios handlers: se eliminan para que todo salga por el handler raíz.
    for name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
    # El access log de uvicorn se reemplaza por el del middleware (incluye request-id y duración).
    uv_access = logging.getLogger("uvicorn.access")
    uv_access.handlers.clear()
    uv_access.propagate = False
    # Librerías ruidosas
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def _incoming_request_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", []):
        if name == b"x-request-id":
            candidate = value.decode("latin-1")
            return candidate if _REQUEST_ID_RE.match(candidate) else None
    return None


class RequestContextMiddleware:
    """Middleware ASGI puro (no usa BaseHTTPMiddleware, así no rompe streaming ni contextvars)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _incoming_request_id(scope) or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        tag_request(request_id)
        started = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER.lower().encode(), request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            error_logger.exception("Error no controlado en %s %s", scope["method"], scope["path"])
            if response_started:
                raise
            status_code = 500
            await _send_internal_error(send_wrapper, request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            level = logging.DEBUG if scope["path"] in _QUIET_PATHS and status_code < 400 else logging.INFO
            access_logger.log(
                level,
                "%s %s %s %.1fms",
                scope["method"],
                scope["path"],
                status_code,
                duration_ms,
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)


async def _send_internal_error(send: Send, request_id: str) -> None:
    body = json.dumps(
        {
            "detail": "Ocurrió un error interno. Si persiste, reporta este código.",
            "code": "internal_error",
            "request_id": request_id,
        }
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 500,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})
