from io import BytesIO

from PIL import Image

from backend.scripts.seed import seed_database
from backend.tests.conftest import create_room, future, make_png, web_booking

ROOM = {"number": "202", "name": "Suite Selva", "price_per_night": 150000, "capacity": 3, "amenities": ["Wifi"]}


async def test_crud_de_habitacion_con_tipo(api, admin_headers, room_types):
    payload = {**ROOM, "room_type_id": str(room_types["family"]["_id"])}
    created = await api.post("/rooms", json=payload, headers=admin_headers)
    assert created.status_code == 201, created.text
    room = created.json()
    assert room["room_type"]["code"] == "family" and room["operational_status"] == "available"

    dup = await api.post("/rooms", json=payload, headers=admin_headers)
    assert dup.status_code == 409

    updated = await api.patch(
        f"/rooms/{room['id']}", json={"price_per_night": 160000, "is_active": False}, headers=admin_headers
    )
    assert updated.json()["price_per_night"] == 160000

    assert (await api.get(f"/rooms/{room['id']}")).status_code == 404  # inactiva: oculta al público
    assert (await api.get(f"/rooms/{room['id']}", headers=admin_headers)).status_code == 200
    publicas = await api.get("/rooms")
    assert publicas.json()["total"] == 0

    logs = await api.get("/audit-logs?entity=room", headers=admin_headers)
    assert {"create", "update"} <= {log["action"] for log in logs.json()["items"]}


async def test_tipo_inexistente_y_datos_invalidos(api, admin_headers, room_types):
    sin_tipo = await api.post(
        "/rooms", json={**ROOM, "room_type_id": "65a1b2c3d4e5f60718293a4b"}, headers=admin_headers
    )
    precio_cero = await api.post(
        "/rooms",
        json={**ROOM, "room_type_id": str(room_types["cabin"]["_id"]), "price_per_night": 0},
        headers=admin_headers,
    )
    assert sin_tipo.status_code == 400
    assert precio_cero.status_code == 422


async def test_validador_de_mongo_rechaza_datos_corruptos(db, room_types):
    """6.6: aunque alguien escriba directo en la BD, el $jsonSchema impide tipos incorrectos."""
    import pytest
    from pymongo.errors import WriteError

    with pytest.raises(WriteError):
        await db.rooms.insert_one(
            {
                "number": "1",
                "name": "X",
                "room_type_id": room_types["cabin"]["_id"],
                "price_per_night": "barato",
                "capacity": "2",
                "is_active": "true",
                "operational_status": "available",
                "images": [],
                "amenities": [],
            }
        )


async def test_no_se_elimina_habitacion_con_reservas(api, admin_headers, room):
    await web_booking(api, room, future(2), future(3))
    response = await api.delete(f"/rooms/{room['_id']}", headers=admin_headers)
    assert response.status_code == 409


async def test_imagenes_de_habitacion(api, admin_headers, room, storage_dirs):
    response = await api.post(
        f"/rooms/{room['_id']}/images",
        headers=admin_headers,
        files=[("files", ("a.png", make_png(), "image/png")), ("files", ("b.png", make_png(), "image/png"))],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["images"]) == 2 and body["main_image"] == body["images"][0]

    removed = await api.delete(f"/rooms/{room['_id']}/images", params={"url": body["images"][0]}, headers=admin_headers)
    assert removed.json()["main_image"] == body["images"][1]
    assert len(list(storage_dirs["public"].iterdir())) == 1

    ajena = await api.delete(
        f"/rooms/{room['_id']}/images", params={"url": "/static/uploads/x.png"}, headers=admin_headers
    )
    assert ajena.status_code == 404


async def test_disponibilidad_elige_la_mas_barata_libre(api, db, room_types):
    cara = await create_room(db, room_types["cabin"], "C1", 300000, capacity=4)
    barata = await create_room(db, room_types["cabin"], "C2", 150000, capacity=4)
    await create_room(db, room_types["cabin"], "C3", 100000, capacity=2)  # sin capacidad suficiente

    params = {"room_type": "cabin", "check_in": future(5).isoformat(), "check_out": future(7).isoformat(), "guests": 3}
    first = await api.get("/availability", params=params)
    assert first.status_code == 200, first.text
    assert first.json()["room"]["id"] == str(barata["_id"])
    assert first.json()["quote"]["total_amount"] == 300000

    await web_booking(api, barata, future(6), future(8))
    second = await api.get("/availability", params=params)
    assert second.json()["room"]["id"] == str(cara["_id"])

    await web_booking(api, cara, future(5), future(6))
    assert (await api.get("/availability", params=params)).status_code == 404
    assert (await api.get("/availability", params={**params, "room_type": "no-existe"})).status_code == 404


async def test_cotizacion_publica(api, room):
    response = await api.get(
        f"/rooms/{room['_id']}/quote", params={"check_in": future(1).isoformat(), "check_out": future(4).isoformat()}
    )
    assert response.json()["total_amount"] == 600000 and response.json()["deposit_amount"] == 300000


# --- Subida de archivos (5.11) ---


async def test_galeria_valida_y_recodifica(api, admin_headers, storage_dirs):
    html = await api.post(
        "/gallery", files={"file": ("x.png", b"<html><script>alert(1)</script>", "image/png")}, headers=admin_headers
    )
    assert html.status_code == 400

    exif = Image.Exif()
    exif[0x010F] = "CamaraSecreta"
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (200, 10, 10)).save(buffer, "JPEG", exif=exif.tobytes())
    ok = await api.post(
        "/gallery",
        data={"category": "Habitaciones", "title": "Vista"},
        files={"file": ("foto.html", buffer.getvalue(), "text/html")},
        headers=admin_headers,
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["url"].endswith(".jpg") and ok.json()["category"] == "habitaciones"
    saved = storage_dirs["public"] / ok.json()["url"].rsplit("/", 1)[-1]
    assert b"CamaraSecreta" not in saved.read_bytes()

    listado = await api.get("/gallery", params={"category": "habitaciones"})
    assert len(listado.json()) == 1
    assert (await api.delete(f"/gallery/{ok.json()['id']}", headers=admin_headers)).status_code == 204
    assert not saved.exists()


async def test_archivo_demasiado_grande(api, admin_headers, monkeypatch):
    from backend.app.core.settings import get_settings

    monkeypatch.setattr(get_settings(), "max_image_size_mb", 1)
    grande = make_png() + b"\0" * (1024 * 1024 + 10)
    response = await api.post("/gallery", files={"file": ("big.png", grande, "image/png")}, headers=admin_headers)
    assert response.status_code == 413


async def test_comprobante_pdf_y_pdf_malicioso(api, room):
    pdf = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF"
    malo = b"%PDF-1.4\n1 0 obj << /OpenAction << /S /JavaScript /JS (x) >> >> endobj\n%%EOF"
    form = {
        "room_id": str(room["_id"]),
        "check_in": future(1).isoformat(),
        "check_out": future(2).isoformat(),
        "full_name": "Pdf Prueba",
        "email": "pdf@example.com",
        "phone": "3000000000",
        "accept_privacy_policy": "true",
    }
    assert (
        await api.post("/bookings", data=form, files={"receipt": ("p.pdf", malo, "application/pdf")})
    ).status_code == 400
    assert (
        await api.post("/bookings", data=form, files={"receipt": ("p.pdf", pdf, "application/pdf")})
    ).status_code == 201


# --- Ajustes, dashboard y notificaciones ---


async def test_ajustes_del_sitio(api, admin_headers, receptionist_headers):
    publicos = await api.get("/settings")
    assert publicos.json()["hotel_name"] == "Hotel Kawari" and publicos.json()["deposit_percent"] == 50

    nuevo = {
        **{k: v for k, v in publicos.json().items() if k not in ("logo_url", "deposit_percent")},
        "hotel_name": "Kawari Eco Lodge",
        "payment_instructions": "Bancolombia Ahorros 000-000",
    }
    assert (await api.put("/settings", json=nuevo, headers=receptionist_headers)).status_code == 403
    response = await api.put("/settings", json=nuevo, headers=admin_headers)
    assert response.status_code == 200, response.text
    assert (await api.get("/settings")).json()["payment_instructions"] == "Bancolombia Ahorros 000-000"

    logo = await api.post(
        "/settings/logo", files={"file": ("logo.png", make_png(), "image/png")}, headers=admin_headers
    )
    assert logo.json()["logo_url"].startswith("/static/uploads/")


async def test_dashboard(api, admin_headers, db, room):
    from backend.app.core.time import hotel_today

    booking = (await web_booking(api, room, hotel_today(), future(1))).json()
    await api.post(f"/bookings/{booking['id']}/status", json={"status": "confirmed"}, headers=admin_headers)
    response = await api.get("/dashboard", headers=admin_headers)
    assert response.status_code == 200, response.text
    stats = response.json()["stats"]
    assert stats["occupied_rooms"] == 1 and stats["sellable_rooms"] == 1 and stats["occupancy_percent"] == 100
    assert stats["arrivals_today"] == 1
    assert response.json()["recent_activity"][0]["code"] == booking["code"]


async def test_notificaciones(api, admin_headers, client_headers, room):
    booking = (await web_booking(api, room, future(2), future(3), headers=client_headers)).json()
    await api.post(f"/bookings/{booking['id']}/status", json={"status": "confirmed"}, headers=admin_headers)
    avisos = await api.get("/notifications", headers=client_headers)
    assert avisos.json()[0]["title"] == "¡Reserva confirmada!" and avisos.json()[0]["read"] is False
    assert (await api.post("/notifications/read-all", headers=client_headers)).json() == {"updated": 1}


# --- Seed ---


async def test_seed_es_idempotente(db, monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "Dueno@Example.com")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "Clave-Del-Dueno-1")
    for _ in range(2):
        await seed_database(db, demo_rooms=True)
    assert await db.room_types.count_documents({}) == 3
    assert await db.rooms.count_documents({}) == 3
    assert await db.users.count_documents({"role": "admin", "email": "dueno@example.com"}) == 1
    assert await db.settings.count_documents({}) == 1
