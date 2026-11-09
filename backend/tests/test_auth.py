from datetime import timedelta

import jwt
import pytest
from pydantic import ValidationError

from backend.app.core.settings import Settings, get_settings
from backend.app.core.time import utcnow
from backend.tests.conftest import PASSWORD, create_user, future, login, token_from_outbox, web_booking

REGISTER = {
    "email": "Nueva.Persona@Example.com",
    "password": "Una-Clave-Larga-1",
    "full_name": "Nueva Persona",
    "document_type": "CC",
    "document_number": "52000111",
    "phone": "3001112233",
    "country": "Colombia",
    "city": "Mocoa",
    "accept_privacy_policy": True,
}


def cookie_name() -> str:
    return get_settings().refresh_cookie_name


# --- Configuración ---

@pytest.mark.parametrize("secret", ["", "corta", "mysecretkey"])
def test_settings_rechaza_secret_key_insegura(secret):
    with pytest.raises(ValidationError):
        Settings(secret_key=secret, mongo_uri="mongodb://x")


def test_settings_exige_mongo_uri(monkeypatch):
    monkeypatch.delenv("MONGO_URI", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="x" * 40)


# --- Registro ---

async def test_registro_normaliza_correo_y_envia_verificacion(api, db):
    response = await api.post("/auth/register", json=REGISTER)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "nueva.persona@example.com"
    assert body["role"] == "client"
    assert body["email_verified"] is False
    assert "password" not in body and "password_hash" not in body
    assert token_from_outbox("/auth/verify-email")


async def test_registro_exige_consentimiento_de_datos(api):
    response = await api.post("/auth/register", json={**REGISTER, "accept_privacy_policy": False})
    assert response.status_code == 400


async def test_registro_exige_contrasena_fuerte(api):
    response = await api.post("/auth/register", json={**REGISTER, "password": "123"})
    assert response.status_code == 422


async def test_registro_no_permite_elegir_rol(api):
    response = await api.post("/auth/register", json={**REGISTER, "role": "admin"})
    assert response.status_code == 422  # extra="forbid"


async def test_registro_duplicado_responde_409(api):
    assert (await api.post("/auth/register", json=REGISTER)).status_code == 201
    dup_email = await api.post("/auth/register", json={**REGISTER, "document_number": "999999"})
    dup_doc = await api.post("/auth/register", json={**REGISTER, "email": "otra@example.com"})
    assert dup_email.status_code == 409 and "correo" in dup_email.json()["detail"]
    assert dup_doc.status_code == 409 and "documento" in dup_doc.json()["detail"]


# --- Login ---

async def test_login_mensaje_generico(api, client_user):
    inexistente = await api.post("/auth/login", data={"username": "nadie@x.com", "password": "loquesea123"})
    clave_mala = await api.post("/auth/login", data={"username": client_user["email"], "password": "loquesea123"})
    assert inexistente.status_code == clave_mala.status_code == 401
    assert inexistente.json()["detail"] == clave_mala.json()["detail"]


async def test_login_devuelve_usuario_permisos_y_cookie_httponly(api, receptionist):
    response = await api.post("/auth/login", data={"username": "RECEPCION@example.com", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "receptionist"
    assert "bookings:change_status" in body["user"]["permissions"]
    assert "refresh_token" not in body  # ya no viaja en el cuerpo
    set_cookie = response.headers["set-cookie"]
    assert cookie_name() in set_cookie and "HttpOnly" in set_cookie and "Path=/api/v1/auth" in set_cookie


async def test_usuario_suspendido_no_inicia_sesion_y_pierde_acceso(api, db, client_user, client_headers):
    assert (await api.get("/users/me", headers=client_headers)).status_code == 200
    await db.users.update_one({"_id": client_user["_id"]}, {"$set": {"is_active": False}})
    assert (await api.get("/users/me", headers=client_headers)).status_code == 401
    login_response = await api.post("/auth/login", data={"username": client_user["email"], "password": PASSWORD})
    assert login_response.status_code == 401


# --- Tokens ---

async def test_token_sin_tipo_access_es_rechazado(api, client_user):
    settings = get_settings()
    token = jwt.encode({"sub": str(client_user["_id"]), "exp": utcnow() + timedelta(minutes=5)},
                       settings.secret_key.get_secret_value(), algorithm="HS256")
    assert (await api.get("/users/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401


async def test_token_con_firma_ajena_es_rechazado(api, client_user):
    token = jwt.encode({"sub": str(client_user["_id"]), "type": "access", "exp": utcnow() + timedelta(minutes=5)},
                       "otro-secreto-de-al-menos-treinta-y-dos-chars", algorithm="HS256")
    assert (await api.get("/users/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401


async def test_refresh_con_cookie_valida_desde_otro_cliente_funciona(api, anon, client_user):
    """Control positivo: confirma que inyectar la cookie por cabecera sí se envía."""
    await login(api, client_user["email"])
    cookie = api.cookies.get(cookie_name())
    assert (await anon.post("/auth/refresh", headers={"Cookie": f"{cookie_name()}={cookie}"})).status_code == 200


async def test_refresh_rota_la_cookie_y_emite_access_token(api, client_user):
    await login(api, client_user["email"])
    primera = api.cookies.get(cookie_name())

    response = await api.post("/auth/refresh")
    assert response.status_code == 200, response.text
    segunda = api.cookies.get(cookie_name())
    assert segunda and segunda != primera
    me = await api.get("/users/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.status_code == 200


async def test_refresh_token_no_sirve_como_bearer(api, client_user):
    await login(api, client_user["email"])
    refresh = api.cookies.get(cookie_name())
    assert (await api.get("/users/me", headers={"Authorization": f"Bearer {refresh}"})).status_code == 401


async def test_reutilizar_refresh_rotado_revoca_la_familia(api, anon, db, client_user):
    await login(api, client_user["email"])
    robado = api.cookies.get(cookie_name())
    assert (await api.post("/auth/refresh")).status_code == 200  # el usuario legítimo rota

    # Simulamos que pasó el periodo de gracia y el atacante usa el token viejo
    await db.refresh_tokens.update_many({"revoked_at": {"$ne": None}},
                                        {"$set": {"revoked_at": utcnow() - timedelta(minutes=5)}})
    assert (await anon.post("/auth/refresh", headers={"Cookie": f"{cookie_name()}={robado}"})).status_code == 401

    # Toda la familia quedó revocada: la sesión legítima también debe volver a iniciar sesión
    assert (await api.post("/auth/refresh")).status_code == 401


async def test_logout_invalida_el_refresh(api, anon, client_user):
    await login(api, client_user["email"])
    cookie = api.cookies.get(cookie_name())
    assert (await api.post("/auth/logout")).status_code == 204
    assert api.cookies.get(cookie_name()) is None  # la cookie se borra en el navegador
    assert (await anon.post("/auth/refresh", headers={"Cookie": f"{cookie_name()}={cookie}"})).status_code == 401


async def test_refresh_sin_cookie_responde_401(anon):
    assert (await anon.post("/auth/refresh")).status_code == 401


async def test_suspender_usuario_invalida_sus_sesiones(api, db, admin_headers, anon, client_user):
    await login(api, client_user["email"])
    response = await anon.patch(f"/users/{client_user['_id']}/status", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 200
    assert (await api.post("/auth/refresh")).status_code == 401


# --- Verificación de correo y vinculación de reservas (5.5) ---

async def test_reservas_de_invitado_solo_se_vinculan_al_verificar(api, anon, db, room):
    await web_booking(anon, room, future(3), future(5), email="victima@example.com")
    await web_booking(anon, room, future(10), future(11), email="vXctima@example.com")  # no debe vincularse

    registro = await api.post("/auth/register", json={**REGISTER, "email": "victima@example.com"})
    assert registro.status_code == 201
    assert await db.bookings.count_documents({"user_id": {"$ne": None}}) == 0  # aún no verificado

    response = await api.post("/auth/verify-email", json={"token": token_from_outbox("/auth/verify-email")})
    assert response.status_code == 200
    assert response.json()["linked_bookings"] == 1


async def test_token_de_verificacion_es_de_un_solo_uso(api):
    await api.post("/auth/register", json=REGISTER)
    token = token_from_outbox("/auth/verify-email")
    assert (await api.post("/auth/verify-email", json={"token": token})).status_code == 200
    assert (await api.post("/auth/verify-email", json={"token": token})).status_code == 400


# --- Recuperación de contraseña ---

async def test_recuperar_contrasena(api, anon, client_user):
    response = await api.post("/auth/forgot-password", json={"email": client_user["email"]})
    assert response.status_code == 202
    await login(anon, client_user["email"])  # sesión abierta en otro dispositivo

    token = token_from_outbox("/auth/reset-password")
    assert (await api.post("/auth/reset-password", json={"token": token, "password": "Nueva-Clave-2026"})).status_code == 200

    assert (await anon.post("/auth/refresh")).status_code == 401  # se cerraron las sesiones
    await login(api, client_user["email"], "Nueva-Clave-2026")
    assert (await api.post("/auth/reset-password", json={"token": token, "password": "Otra-Clave-2026"})).status_code == 400


async def test_recuperar_contrasena_no_revela_si_el_correo_existe(api):
    from backend.app.modules.notifications.email import outbox

    response = await api.post("/auth/forgot-password", json={"email": "nadie@example.com"})
    assert response.status_code == 202
    assert outbox == []


async def test_usuario_creado_por_recepcion_define_su_contrasena(api, anon, receptionist_headers):
    nuevo = {"email": "walkin@example.com", "full_name": "Huésped Walk-in", "document_type": "CC", "document_number": "777777"}
    response = await anon.post("/users", json=nuevo, headers=receptionist_headers)
    assert response.status_code == 201, response.text

    # 5.10: no hay contraseña por defecto (ni el documento sirve)
    assert (await api.post("/auth/login", data={"username": "walkin@example.com", "password": "777777"})).status_code == 401

    token = token_from_outbox("/auth/reset-password")
    assert (await api.post("/auth/reset-password", json={"token": token, "password": "Mi-Clave-Propia-1"})).status_code == 200
    await login(api, "walkin@example.com", "Mi-Clave-Propia-1")


async def test_cambiar_contrasena(api, client_user, client_headers):
    mala = await api.post("/users/me/password", json={"current_password": "x" * 8, "new_password": "Otra-Clave-123"},
                          headers=client_headers)
    assert mala.status_code == 400
    ok = await api.post("/users/me/password", json={"current_password": PASSWORD, "new_password": "Otra-Clave-123"},
                        headers=client_headers)
    assert ok.status_code == 204
    await login(api, client_user["email"], "Otra-Clave-123")


async def test_eliminar_mi_cuenta_desactiva(api, client_user, client_headers):
    assert (await api.delete("/users/me", headers=client_headers)).status_code == 204
    assert (await api.get("/users/me", headers=client_headers)).status_code == 401


async def test_actualizar_perfil_no_permite_cambiar_rol(api, client_headers):
    response = await api.patch("/users/me", json={"role": "admin"}, headers=client_headers)
    assert response.status_code == 422
