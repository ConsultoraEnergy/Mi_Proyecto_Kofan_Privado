"""
Pruebas de la Fase 0 (bloqueantes de seguridad) — ver CLAUDE.md, sección 13.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

import pytest
from bson import ObjectId
from fastapi.routing import APIRoute
from PIL import Image

from backend.core.security import create_access_token, create_refresh_token
from conftest import _login_headers, make_png_bytes

pytestmark = pytest.mark.asyncio

ROOT_DIR = Path(__file__).resolve().parents[1]
FAKE_ID = "65a1b2c3d4e5f60718293a4b"

# Endpoints accesibles sin autenticación (decisión explícita; ver docs/ENDPOINTS_ACCESO.md).
PUBLIC_ENDPOINTS = {
    ("POST", "/auth/login"),
    ("POST", "/register/"),
    ("GET", "/rooms/public"),
    ("GET", "/rooms/public/{room_id}"),
    ("GET", "/rooms/"),
    ("GET", "/rooms/{room_id}"),
    ("GET", "/rooms/{room_id}/booked-dates"),
    ("GET", "/config"),
    ("GET", "/gallery/"),
    ("GET", "/busqueda/disponibilidad"),
    ("POST", "/api/reservas/invitado"),
}

# Endpoints para cualquier usuario autenticado (cliente o admin).
AUTHENTICATED_ENDPOINTS = {
    ("GET", "/users/me"),
    ("PATCH", "/users/update-me"),
    ("PATCH", "/users/delete-me"),
    ("POST", "/api/reservas/"),
    ("GET", "/api/reservas/mis-reservas"),
    ("GET", "/api/reservas/{reserva_id}/comprobante"),
    ("GET", "/api/notificaciones/mis-avisos"),
    ("PATCH", "/api/notificaciones/read-all"),
}


def _all_endpoints():
    from backend.main import app

    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
                yield method, route.path


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", FAKE_ID, path)


# ---------------------------------------------------------------------------
# 5.1 / 5.2 — Auditoría de autorización de TODOS los endpoints
# ---------------------------------------------------------------------------

async def test_todo_endpoint_no_publico_exige_autenticacion(api_client):
    fallos = []
    for method, path in _all_endpoints():
        if (method, path) in PUBLIC_ENDPOINTS:
            continue
        response = await api_client.request(method, _concrete(path))
        if response.status_code != 401:
            fallos.append(f"{method} {path} -> {response.status_code}")
    assert not fallos, "Endpoints accesibles sin token:\n" + "\n".join(fallos)


async def test_endpoints_de_admin_rechazan_a_un_cliente(api_client, client_headers):
    fallos = []
    for method, path in _all_endpoints():
        if (method, path) in PUBLIC_ENDPOINTS | AUTHENTICATED_ENDPOINTS:
            continue
        response = await api_client.request(method, _concrete(path), headers=client_headers)
        if response.status_code != 403:
            fallos.append(f"{method} {path} -> {response.status_code}")
    assert not fallos, "Endpoints de admin accesibles para un cliente:\n" + "\n".join(fallos)


async def test_la_lista_de_endpoints_documentados_esta_al_dia():
    """Si se agrega/renombra un endpoint público o de cliente, hay que actualizar las listas."""
    existentes = set(_all_endpoints())
    obsoletos = (PUBLIC_ENDPOINTS | AUTHENTICATED_ENDPOINTS) - existentes
    assert not obsoletos, f"Endpoints listados que ya no existen: {obsoletos}"


async def test_facturas_requieren_admin(api_client, client_headers, admin_headers):
    anon = await api_client.get(f"/invoices/by-booking/{FAKE_ID}")
    cliente = await api_client.get(f"/invoices/by-booking/{FAKE_ID}", headers=client_headers)
    admin = await api_client.get(f"/invoices/by-booking/{FAKE_ID}", headers=admin_headers)
    assert anon.status_code == 401
    assert cliente.status_code == 403
    assert admin.status_code == 404  # pasa la autorización; la factura no existe


async def test_cliente_no_puede_crear_habitaciones(api_client, client_headers, png_bytes, test_db):
    response = await api_client.post(
        "/rooms/create-with-images",
        data={"room_number": "999", "name": "Pirata", "price": "1", "capacity": "2", "type": "cabins"},
        files={"images": ("x.png", png_bytes, "image/png")},
        headers=client_headers,
    )
    assert response.status_code == 403
    assert await test_db.rooms.count_documents({"room_number": "999"}) == 0


# ---------------------------------------------------------------------------
# 5.4 / 5.9 / 5.12 — Tokens, cuentas inactivas y mensajes de login
# ---------------------------------------------------------------------------

async def test_refresh_token_no_sirve_como_access_token(api_client, client_user):
    refresh = create_refresh_token({"sub": str(client_user["_id"])})
    response = await api_client.get("/users/me", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401


async def test_token_sin_claim_type_es_rechazado(api_client, client_user):
    from jose import jwt
    from backend.core.config import ALGORITHM, SECRET

    legacy = jwt.encode(
        {"sub": str(client_user["_id"]), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        SECRET,
        algorithm=ALGORITHM,
    )
    response = await api_client.get("/users/me", headers={"Authorization": f"Bearer {legacy}"})
    assert response.status_code == 401


async def test_access_token_valido_funciona(api_client, client_user):
    access = create_access_token({"sub": str(client_user["_id"])})
    response = await api_client.get("/users/me", headers={"Authorization": f"Bearer {access}"})
    assert response.status_code == 200


async def test_token_con_sub_invalido_responde_401_no_500(api_client):
    access = create_access_token({"sub": "no-es-un-object-id"})
    response = await api_client.get("/users/me", headers={"Authorization": f"Bearer {access}"})
    assert response.status_code == 401


async def test_usuario_suspendido_pierde_acceso(api_client, test_db, client_user, client_headers):
    assert (await api_client.get("/users/me", headers=client_headers)).status_code == 200

    await test_db.users.update_one({"_id": client_user["_id"]}, {"$set": {"is_active": False}})

    assert (await api_client.get("/users/me", headers=client_headers)).status_code == 401
    login = await api_client.post(
        "/auth/login", data={"username": client_user["email"], "password": "Cliente123*"}
    )
    assert login.status_code == 401


async def test_login_no_revela_si_el_correo_existe(api_client, client_user):
    inexistente = await api_client.post(
        "/auth/login", data={"username": "nadie@kofan.test", "password": "loquesea123"}
    )
    clave_mala = await api_client.post(
        "/auth/login", data={"username": client_user["email"], "password": "loquesea123"}
    )
    assert inexistente.status_code == clave_mala.status_code == 401
    assert inexistente.json()["detail"] == clave_mala.json()["detail"]


async def test_arranque_falla_sin_secret_key_segura():
    for valor in ["", "mysecretkey", "corta"]:
        env = {**os.environ, "SECRET_KEY": valor}
        result = subprocess.run(
            [sys.executable, "-c", "import backend.core.config"],
            cwd=ROOT_DIR, env=env, capture_output=True, text=True,
        )
        assert result.returncode != 0, f"El backend arrancó con SECRET_KEY={valor!r}"
        assert "SECRET_KEY" in result.stderr


# ---------------------------------------------------------------------------
# 5.5 / 5.10 — Registro
# ---------------------------------------------------------------------------

def _nuevo_registro(**extra):
    data = {
        "tipo_persona": "natural",
        "full_name": "Atacante",
        "type_document": "CC",
        "number_document": "55555555",
        "email": "victima@example.com",
        "country": "Colombia",
        "city": "Mocoa",
        "password": "Atacante123*",
    }
    data.update(extra)
    return data


async def test_registro_no_vincula_reservas_de_otro_por_correo(api_client, test_db, sample_room):
    reserva = await test_db.bookings.insert_one({
        "habitacion_id": sample_room["_id"],
        "cliente_email": "victima@example.com",
        "cliente_id": None,
        "estado": "confirmada",
    })

    response = await api_client.post("/register/", json=_nuevo_registro())
    assert response.status_code == 201

    guardada = await test_db.bookings.find_one({"_id": reserva.inserted_id})
    assert guardada["cliente_id"] is None


async def test_vinculacion_usa_igualdad_exacta_no_regex(test_db, sample_room):
    from backend.services.user_service import link_guest_bookings_to_user

    await test_db.bookings.insert_many([
        {"cliente_email": "aXb@example.com", "cliente_id": None},  # "." de un regex coincidiría
        {"cliente_email": "a.b@example.com", "cliente_id": None},
    ])
    vinculadas = await link_guest_bookings_to_user("A.B@example.com", str(ObjectId()))
    assert vinculadas == 1


async def test_registro_publico_exige_contrasena(api_client):
    sin_clave = await api_client.post("/register/", json=_nuevo_registro(password=None))
    corta = await api_client.post("/register/", json=_nuevo_registro(password="123"))
    assert sin_clave.status_code == 400
    assert corta.status_code == 400


async def test_registro_publico_no_permite_elegir_rol(api_client, test_db):
    response = await api_client.post("/register/", json=_nuevo_registro(role="admin"))
    assert response.status_code == 201
    user = await test_db.users.find_one({"email": "victima@example.com"})
    assert user["role"] == "client"


# ---------------------------------------------------------------------------
# 5.8 — Gestión de usuarios
# ---------------------------------------------------------------------------

async def test_router_admin_duplicado_eliminado(api_client, admin_headers):
    response = await api_client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 404


async def test_actualizar_usuario_no_devuelve_password(api_client, admin_headers, client_user):
    response = await api_client.patch(
        f"/users/{client_user['_id']}", json={"full_name": "Nuevo Nombre"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert "password" not in response.json()["user"]


# ---------------------------------------------------------------------------
# 5.3 — Precio calculado en el backend
# ---------------------------------------------------------------------------

def _payload_reserva(room, **extra):
    data = {
        "habitacion_id": str(room["_id"]),
        "fecha_entrada": "2027-03-10",
        "fecha_salida": "2027-03-13",  # 3 noches
        "monto_total": "1",  # intento de manipulación: debe ignorarse
        "cliente_nombre": "Huésped",
        "cliente_email": "Huesped@Example.com",
        "cliente_celular": "3200000000",
    }
    data.update(extra)
    return data


async def test_precio_lo_calcula_el_servidor(api_client, test_db, sample_room, png_bytes):
    response = await api_client.post(
        "/api/reservas/invitado",
        data=_payload_reserva(sample_room),
        files={"comprobante": ("pago.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["monto_total"] == 3 * 180000
    assert body["anticipo"] == 3 * 180000 * 0.5
    assert body["noches"] == 3

    reserva = await test_db.bookings.find_one({"_id": ObjectId(body["reserva_id"])})
    assert reserva["monto_total"] == 540000
    assert reserva["precio_noche"] == 180000
    assert reserva["estado"] == "pendiente"
    assert reserva["cliente_email"] == "huesped@example.com"


async def test_reserva_autenticada_tambien_ignora_monto(api_client, client_headers, sample_room, png_bytes):
    response = await api_client.post(
        "/api/reservas/",
        data=_payload_reserva(sample_room),
        files={"comprobante": ("pago.png", png_bytes, "image/png")},
        headers=client_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["monto_total"] == 540000


async def test_fechas_invertidas_son_rechazadas(api_client, sample_room, png_bytes, storage_dirs):
    response = await api_client.post(
        "/api/reservas/invitado",
        data=_payload_reserva(sample_room, fecha_entrada="2027-03-13", fecha_salida="2027-03-10"),
        files={"comprobante": ("pago.png", png_bytes, "image/png")},
    )
    assert response.status_code == 400
    # El comprobante de una reserva fallida no queda huérfano en disco
    assert list(storage_dirs["private"].iterdir()) == []


async def test_habitacion_inactiva_no_se_puede_reservar(api_client, test_db, sample_room, png_bytes):
    await test_db.rooms.update_one({"_id": sample_room["_id"]}, {"$set": {"active": False}})
    response = await api_client.post(
        "/api/reservas/invitado",
        data=_payload_reserva(sample_room),
        files={"comprobante": ("pago.png", png_bytes, "image/png")},
    )
    assert response.status_code == 404


async def test_reserva_web_exige_comprobante(api_client, sample_room):
    response = await api_client.post("/api/reservas/invitado", data=_payload_reserva(sample_room))
    assert response.status_code == 422


async def test_reserva_admin_calcula_precio_y_queda_confirmada(api_client, admin_headers, test_db, sample_room):
    payload = {
        "habitacion_id": str(sample_room["_id"]),
        "fecha_entrada": "2027-05-01",
        "fecha_salida": "2027-05-03",
        "cliente_nombre": "Walk-in",
        "cliente_email": "walkin@example.com",
        "cliente_celular": "3000000000",
    }
    response = await api_client.post("/api/reservas/admin", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    assert response.json()["monto_total"] == 360000

    reserva = await test_db.bookings.find_one({"_id": ObjectId(response.json()["reserva_id"])})
    assert reserva["estado"] == "confirmada"
    assert reserva["creado_por"] == "admin@kofan.test"


async def test_reserva_admin_permite_precio_negociado(api_client, admin_headers, test_db, sample_room):
    payload = {
        "habitacion_id": str(sample_room["_id"]),
        "fecha_entrada": "2027-06-01",
        "fecha_salida": "2027-06-03",
        "cliente_nombre": "Convenio",
        "cliente_email": "convenio@example.com",
        "monto_total": 300000,
    }
    response = await api_client.post("/api/reservas/admin", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    reserva = await test_db.bookings.find_one({"_id": ObjectId(response.json()["reserva_id"])})
    assert reserva["monto_total"] == 300000
    assert reserva["monto_calculado"] == 360000
    assert reserva["anticipo"] == 150000


# ---------------------------------------------------------------------------
# 5.6 — Comprobantes privados
# ---------------------------------------------------------------------------

async def _crear_reserva_con_comprobante(api_client, room, contenido, nombre="pago.png", tipo="image/png", headers=None):
    return await api_client.post(
        "/api/reservas/" if headers else "/api/reservas/invitado",
        data=_payload_reserva(room),
        files={"comprobante": (nombre, contenido, tipo)},
        headers=headers or {},
    )


async def test_comprobante_se_guarda_en_almacenamiento_privado(
    api_client, test_db, sample_room, png_bytes, storage_dirs
):
    response = await _crear_reserva_con_comprobante(api_client, sample_room, png_bytes)
    reserva = await test_db.bookings.find_one({"_id": ObjectId(response.json()["reserva_id"])})

    clave = reserva["comprobante_archivo"]
    assert (storage_dirs["private"] / clave).exists()
    assert list(storage_dirs["public"].iterdir()) == []
    assert "comprobante_url" not in reserva

    publico = await api_client.get(f"/static/uploads/{clave}")
    assert publico.status_code == 404


async def test_acceso_al_comprobante(
    api_client, test_db, sample_room, png_bytes, admin_headers, client_headers, client_user
):
    # Reserva de un invitado
    response = await _crear_reserva_con_comprobante(api_client, sample_room, png_bytes)
    url = f"/api/reservas/{response.json()['reserva_id']}/comprobante"

    assert (await api_client.get(url)).status_code == 401
    assert (await api_client.get(url, headers=client_headers)).status_code == 404  # no es suya

    admin = await api_client.get(url, headers=admin_headers)
    assert admin.status_code == 200
    assert admin.headers["content-type"] == "image/png"
    assert admin.headers["x-content-type-options"] == "nosniff"
    assert Image.open(BytesIO(admin.content)).format == "PNG"

    # Reserva propia del cliente
    propia = await _crear_reserva_con_comprobante(
        api_client, sample_room, png_bytes, headers=client_headers
    )
    # (misma habitación y fechas -> choque; usamos otras fechas)
    if propia.status_code != 200:
        propia = await api_client.post(
            "/api/reservas/",
            data=_payload_reserva(sample_room, fecha_entrada="2027-08-01", fecha_salida="2027-08-02"),
            files={"comprobante": ("pago.png", png_bytes, "image/png")},
            headers=client_headers,
        )
    assert propia.status_code == 200, propia.text
    url_propia = f"/api/reservas/{propia.json()['reserva_id']}/comprobante"
    assert (await api_client.get(url_propia, headers=client_headers)).status_code == 200


async def test_listado_admin_expone_endpoint_y_no_la_ruta_del_archivo(
    api_client, sample_room, png_bytes, admin_headers
):
    response = await _crear_reserva_con_comprobante(api_client, sample_room, png_bytes)
    reserva_id = response.json()["reserva_id"]

    listado = await api_client.get("/api/reservas/admin/todas", headers=admin_headers)
    reserva = next(r for r in listado.json()["reservas"] if r["id"] == reserva_id)
    assert reserva["comprobante_url"] == f"/api/reservas/{reserva_id}/comprobante"


async def test_comprobante_pdf_es_aceptado(api_client, sample_room, admin_headers):
    pdf = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << >>\n%%EOF"
    response = await _crear_reserva_con_comprobante(
        api_client, sample_room, pdf, nombre="pago.pdf", tipo="application/pdf"
    )
    assert response.status_code == 200, response.text
    url = f"/api/reservas/{response.json()['reserva_id']}/comprobante"
    descarga = await api_client.get(url, headers=admin_headers)
    assert descarga.headers["content-type"] == "application/pdf"


async def test_pdf_con_javascript_es_rechazado(api_client, sample_room):
    pdf = b"%PDF-1.4\n1 0 obj << /OpenAction << /S /JavaScript /JS (alert(1)) >> >> endobj\n%%EOF"
    response = await _crear_reserva_con_comprobante(
        api_client, sample_room, pdf, nombre="pago.pdf", tipo="application/pdf"
    )
    assert response.status_code == 400


async def test_comprobante_legado_en_carpeta_publica_sigue_accesible_para_admin(
    api_client, test_db, sample_room, admin_headers, storage_dirs, png_bytes
):
    nombre = "a" * 32 + ".png"
    (storage_dirs["public"] / nombre).write_bytes(png_bytes)
    reserva = await test_db.bookings.insert_one({
        "habitacion_id": sample_room["_id"],
        "comprobante_url": f"/static/uploads/{nombre}",
        "estado": "pendiente",
    })
    response = await api_client.get(
        f"/api/reservas/{reserva.inserted_id}/comprobante", headers=admin_headers
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 5.11 — Subida de archivos
# ---------------------------------------------------------------------------

async def test_html_disfrazado_de_imagen_es_rechazado(api_client, admin_headers, storage_dirs):
    response = await api_client.post(
        "/gallery/",
        files={"file": ("foto.png", b"<html><script>alert(1)</script></html>", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert list(storage_dirs["public"].iterdir()) == []


async def test_svg_es_rechazado(api_client, admin_headers):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    response = await api_client.post(
        "/gallery/", files={"file": ("x.svg", svg, "image/png")}, headers=admin_headers
    )
    assert response.status_code == 400


async def test_extension_se_deriva_del_contenido(api_client, admin_headers, png_bytes):
    response = await api_client.post(
        "/gallery/", files={"file": ("malicioso.html", png_bytes, "text/html")}, headers=admin_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["url"].endswith(".png")


async def test_archivo_demasiado_grande_es_rechazado(api_client, admin_headers, monkeypatch):
    from backend.services import storage_service

    monkeypatch.setattr(storage_service, "MAX_IMAGE_SIZE_MB", 1)
    grande = make_png_bytes() + b"\0" * (1024 * 1024 + 10)
    response = await api_client.post(
        "/gallery/", files={"file": ("big.png", grande, "image/png")}, headers=admin_headers
    )
    assert response.status_code == 413


async def test_imagen_se_recodifica_sin_exif(api_client, admin_headers, storage_dirs):
    exif = Image.Exif()
    exif[0x010F] = "CamaraSecreta"  # Make
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (200, 10, 10)).save(buffer, "JPEG", exif=exif.tobytes())

    response = await api_client.post(
        "/gallery/", files={"file": ("foto.jpg", buffer.getvalue(), "image/jpeg")}, headers=admin_headers
    )
    assert response.status_code == 200, response.text

    guardada = storage_dirs["public"] / response.json()["url"].rsplit("/", 1)[-1]
    with Image.open(guardada) as img:
        assert img.format == "JPEG"
        assert not img.getexif()
    assert b"CamaraSecreta" not in guardada.read_bytes()


async def test_si_una_imagen_es_invalida_no_se_guarda_ninguna(api_client, admin_headers, storage_dirs, png_bytes):
    response = await api_client.post(
        "/rooms/create-with-images",
        data={"room_number": "301", "name": "Lote", "price": "100000", "capacity": "2", "type": "cabins"},
        files=[
            ("images", ("ok.png", png_bytes, "image/png")),
            ("images", ("mala.png", b"no soy una imagen", "image/png")),
        ],
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert list(storage_dirs["public"].iterdir()) == []


async def test_borrado_no_permite_path_traversal(storage_dirs, tmp_path):
    from backend.services.storage_service import delete_public_file

    victima = tmp_path / "importante.txt"
    victima.write_text("no borrar")
    assert await delete_public_file("/static/uploads/../importante.txt") is False
    assert victima.exists()


# ---------------------------------------------------------------------------
# 6.2 — Bot de cancelación
# ---------------------------------------------------------------------------

async def test_bot_solo_cancela_pendientes_sin_comprobante_vencidas(test_db, client_user):
    from backend.core.config import BOOKING_PENDING_EXPIRATION_HOURS
    from backend.services.task_service import cancelar_reservas_vencidas

    ahora = datetime.now(timezone.utc)
    viejo = ahora - timedelta(hours=BOOKING_PENDING_EXPIRATION_HOURS + 1)
    reciente = ahora - timedelta(minutes=30)

    ids = {}
    for nombre, doc in {
        "vencida_sin_comprobante": {"created_at": viejo, "cliente_id": client_user["_id"]},
        "vencida_con_comprobante": {"created_at": viejo, "comprobante_archivo": "b" * 32 + ".png"},
        "vencida_con_comprobante_legado": {"created_at": viejo, "comprobante_url": "/static/uploads/x.png"},
        "reciente_sin_comprobante": {"created_at": reciente},
    }.items():
        result = await test_db.bookings.insert_one({"estado": "pendiente", **doc})
        ids[nombre] = result.inserted_id

    confirmada = await test_db.bookings.insert_one({"estado": "confirmada", "created_at": viejo})

    canceladas = await cancelar_reservas_vencidas()
    assert canceladas == 1

    async def estado(_id):
        return (await test_db.bookings.find_one({"_id": _id}))["estado"]

    assert await estado(ids["vencida_sin_comprobante"]) == "cancelada"
    assert await estado(ids["vencida_con_comprobante"]) == "pendiente"
    assert await estado(ids["vencida_con_comprobante_legado"]) == "pendiente"
    assert await estado(ids["reciente_sin_comprobante"]) == "pendiente"
    assert await estado(confirmada.inserted_id) == "confirmada"

    # El cliente recibe una notificación en su panel
    assert await test_db.notifications.count_documents({"user_id": client_user["_id"]}) == 1
