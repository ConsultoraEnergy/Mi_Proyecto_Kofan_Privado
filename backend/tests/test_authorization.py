"""
Auditoría automática de autorización: recorre TODOS los endpoints publicados en el esquema OpenAPI.
Si se agrega un endpoint, debe quedar clasificado aquí (y en docs/ENDPOINTS_ACCESO.md).
"""
import re

import pytest

FAKE_ID = "65a1b2c3d4e5f60718293a4b"

PUBLIC = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/verify-email"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    ("GET", "/api/v1/room-types"),
    ("GET", "/api/v1/availability"),
    ("GET", "/api/v1/rooms"),
    ("GET", "/api/v1/rooms/{room_id}"),
    ("GET", "/api/v1/rooms/{room_id}/booked-dates"),
    ("GET", "/api/v1/rooms/{room_id}/quote"),
    ("POST", "/api/v1/bookings"),
    ("GET", "/api/v1/gallery"),
    ("GET", "/api/v1/settings"),
}

AUTHENTICATED = {
    ("POST", "/api/v1/auth/resend-verification"),
    ("GET", "/api/v1/users/me"),
    ("PATCH", "/api/v1/users/me"),
    ("DELETE", "/api/v1/users/me"),
    ("POST", "/api/v1/users/me/password"),
    ("GET", "/api/v1/bookings/mine"),
    ("GET", "/api/v1/bookings/{booking_id}"),
    ("GET", "/api/v1/bookings/{booking_id}/receipt"),
    ("POST", "/api/v1/bookings/{booking_id}/receipt"),
    ("GET", "/api/v1/notifications"),
    ("POST", "/api/v1/notifications/read-all"),
}

# Endpoints de personal que la recepción SÍ puede usar (el resto es solo admin).
RECEPTIONIST_ALLOWED = {
    ("GET", "/api/v1/users"),
    ("POST", "/api/v1/users"),
    ("GET", "/api/v1/users/{user_id}"),
    ("PATCH", "/api/v1/users/{user_id}"),
    ("PATCH", "/api/v1/users/{user_id}/status"),
    ("GET", "/api/v1/bookings"),
    ("POST", "/api/v1/bookings/manual"),
    ("PATCH", "/api/v1/bookings/{booking_id}"),
    ("POST", "/api/v1/bookings/{booking_id}/status"),
    ("GET", "/api/v1/folios/by-booking/{booking_id}"),
    ("POST", "/api/v1/folios/{folio_id}/charges"),
    ("DELETE", "/api/v1/folios/{folio_id}/charges/{charge_id}"),
    ("GET", "/api/v1/dashboard"),
}


def all_endpoints() -> set[tuple[str, str]]:
    from backend.app.main import app

    return {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
    }


def concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", FAKE_ID, path).removeprefix("/api/v1")


def test_todos_los_endpoints_estan_clasificados():
    endpoints = all_endpoints()
    staff = endpoints - PUBLIC - AUTHENTICATED
    assert len(endpoints) > 40
    assert (PUBLIC | AUTHENTICATED | RECEPTIONIST_ALLOWED) <= endpoints, "Hay endpoints listados que ya no existen"
    assert staff, "Debe haber endpoints de personal"


async def test_endpoints_no_publicos_exigen_token(anon):
    fallos = []
    for method, path in sorted(all_endpoints() - PUBLIC):
        response = await anon.request(method, concrete(path))
        if response.status_code != 401:
            fallos.append(f"{method} {path} -> {response.status_code}")
    assert not fallos, "Accesibles sin token:\n" + "\n".join(fallos)


async def test_endpoints_de_personal_rechazan_clientes(anon, client_headers):
    fallos = []
    for method, path in sorted(all_endpoints() - PUBLIC - AUTHENTICATED):
        response = await anon.request(method, concrete(path), headers=client_headers)
        if response.status_code != 403:
            fallos.append(f"{method} {path} -> {response.status_code}")
    assert not fallos, "Accesibles para un cliente:\n" + "\n".join(fallos)


async def test_endpoints_solo_admin_rechazan_recepcion(anon, receptionist_headers):
    fallos = []
    for method, path in sorted(all_endpoints() - PUBLIC - AUTHENTICATED - RECEPTIONIST_ALLOWED):
        response = await anon.request(method, concrete(path), headers=receptionist_headers)
        if response.status_code != 403:
            fallos.append(f"{method} {path} -> {response.status_code}")
    assert not fallos, "Endpoints de admin accesibles para recepción:\n" + "\n".join(fallos)


async def test_recepcion_si_accede_a_sus_endpoints(anon, receptionist_headers):
    for method, path in sorted(RECEPTIONIST_ALLOWED):
        response = await anon.request(method, concrete(path), headers=receptionist_headers)
        assert response.status_code != 403, f"{method} {path} debería estar permitido a recepción"


async def test_recepcion_no_puede_crear_personal(anon, receptionist_headers):
    response = await anon.post("/users", json={"email": "nuevo.admin@x.com", "full_name": "Nuevo Admin", "role": "admin"},
                               headers=receptionist_headers)
    assert response.status_code == 403


async def test_recepcion_no_puede_editar_ni_suspender_admins(anon, admin, receptionist_headers):
    editar = await anon.patch(f"/users/{admin['_id']}", json={"full_name": "Hackeado"}, headers=receptionist_headers)
    suspender = await anon.patch(f"/users/{admin['_id']}/status", json={"is_active": False}, headers=receptionist_headers)
    assert editar.status_code == suspender.status_code == 403


async def test_recepcion_no_puede_ascender_un_cliente(anon, client_user, receptionist_headers):
    response = await anon.patch(f"/users/{client_user['_id']}", json={"role": "admin"}, headers=receptionist_headers)
    assert response.status_code == 403


async def test_admin_no_puede_suspenderse_ni_cambiar_su_rol(anon, admin, admin_headers):
    assert (await anon.patch(f"/users/{admin['_id']}/status", json={"is_active": False}, headers=admin_headers)).status_code == 403
    assert (await anon.patch(f"/users/{admin['_id']}", json={"role": "client"}, headers=admin_headers)).status_code == 403


async def test_ids_invalidos_responden_404_no_500(anon, admin_headers):
    for path in ["/users/no-es-un-id", "/rooms/no-es-un-id", "/bookings/no-es-un-id", "/folios/by-booking/xyz"]:
        response = await anon.get(path, headers=admin_headers)
        assert response.status_code == 404, f"{path} -> {response.status_code}"


@pytest.mark.parametrize("path", ["/rooms?include_inactive=true", "/room-types?include_inactive=true"])
async def test_ver_inactivos_requiere_permiso(anon, client_headers, path):
    assert (await anon.get(path)).status_code == 403
    assert (await anon.get(path, headers=client_headers)).status_code == 403
