"""Sondas de salud, request-id y manejo de errores no controlados."""

import json
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.core.logging import JsonFormatter, RequestContextMiddleware, RequestIdFilter, request_id_var
from backend.app.db import client as mongo


@pytest.fixture
async def root(db):
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client


async def test_health_no_depende_de_mongo(root):
    mongo.use_database(None)  # simula BD caída
    response = await root.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready_ok_con_mongo(root):
    response = await root.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"mongodb": "ok"}}


async def test_ready_503_sin_mongo(root):
    mongo.use_database(None)
    response = await root.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["mongodb"] == "unavailable"


async def test_toda_respuesta_lleva_request_id(root):
    response = await root.get("/health")
    assert len(response.headers["x-request-id"]) == 32


async def test_respeta_request_id_entrante_valido(root):
    response = await root.get("/health", headers={"X-Request-ID": "abc-123_XYZ.def"})
    assert response.headers["x-request-id"] == "abc-123_XYZ.def"


async def test_reemplaza_request_id_entrante_invalido(root):
    response = await root.get("/health", headers={"X-Request-ID": "x\ny<script>"})
    assert response.headers["x-request-id"] != "x\ny<script>"
    assert len(response.headers["x-request-id"]) == 32


async def test_error_no_controlado_responde_500_generico(caplog):
    async def failing_app(scope, receive, send):
        raise RuntimeError("detalle interno secreto")

    app = RequestContextMiddleware(failing_app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        with caplog.at_level(logging.ERROR, logger="backend.errors"):
            response = await client.get("/cualquier-ruta")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert body["request_id"] == response.headers["x-request-id"]
    assert "secreto" not in response.text
    assert any("Error no controlado" in r.getMessage() for r in caplog.records)


def test_formato_json_incluye_request_id_y_extras():
    token = request_id_var.set("req-0001")
    try:
        record = logging.LogRecord("kawari.test", logging.INFO, __file__, 1, "hola %s", ("mundo",), None)
        record.status = 201
        RequestIdFilter().filter(record)
        event = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert event["message"] == "hola mundo"
    assert event["request_id"] == "req-0001"
    assert event["status"] == 201
    assert event["level"] == "INFO"
