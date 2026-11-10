"""
Errores de dominio. Los servicios lanzan estas excepciones (nunca HTTPException) y un manejador
global las traduce a respuestas HTTP con el formato {"detail": <mensaje>, "code": <código>}.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ValidationFailed(DomainError):
    status_code = 400
    code = "validation_failed"


class Unauthorized(DomainError):
    status_code = 401
    code = "unauthorized"


class Forbidden(DomainError):
    status_code = 403
    code = "forbidden"


class NotFound(DomainError):
    status_code = 404
    code = "not_found"


class Conflict(DomainError):
    status_code = 409
    code = "conflict"


class PayloadTooLarge(DomainError):
    status_code = 413
    code = "payload_too_large"


class ServiceUnavailable(DomainError):
    status_code = 503
    code = "service_unavailable"


async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    # Starlette tipa los manejadores con `Exception`; uno específico de DomainError es válido en ejecución.
    app.add_exception_handler(DomainError, _domain_error_handler)  # type: ignore[arg-type]
