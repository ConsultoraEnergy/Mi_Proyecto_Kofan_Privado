"""
Sondas para orquestadores y balanceadores (Docker, Kubernetes, Nginx, uptime monitors).

- `GET /health`: liveness. Solo indica que el proceso responde; no toca dependencias externas, para
  que una caída de MongoDB no provoque reinicios en cadena de la API.
- `GET /ready`: readiness. Verifica que MongoDB responde; 503 si no, para sacar la instancia del
  balanceador hasta que se recupere.

Viven fuera de `/api/v1` y del esquema OpenAPI porque no forman parte del contrato de la API; son
públicas y no exponen datos (ver backend/tests/test_observability.py).
"""

import asyncio
import logging

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from backend.app.db.client import get_db

logger = logging.getLogger(__name__)

READY_TIMEOUT_SECONDS = 2.0

router = APIRouter(tags=["health"], include_in_schema=False)


class HealthOut(BaseModel):
    status: str
    checks: dict[str, str] = {}


@router.get("/health", response_model=HealthOut)
async def health():
    return HealthOut(status="ok")


@router.get("/ready", response_model=HealthOut, responses={503: {"model": HealthOut}})
async def ready(response: Response):
    try:
        await asyncio.wait_for(get_db().command("ping"), timeout=READY_TIMEOUT_SECONDS)
        mongo_status = "ok"
    except Exception as exc:  # cualquier fallo (timeout, red, BD sin conectar) => no listo
        logger.warning("Readiness: MongoDB no responde (%s)", type(exc).__name__)
        mongo_status = "unavailable"

    if mongo_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthOut(status="unavailable", checks={"mongodb": mongo_status})
    return HealthOut(status="ok", checks={"mongodb": mongo_status})
