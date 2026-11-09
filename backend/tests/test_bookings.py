import asyncio
from datetime import timedelta

from bson import ObjectId

from backend.app.core.time import date_to_datetime, hotel_today, utcnow
from backend.app.modules.bookings.service import expire_unpaid_bookings
from backend.tests.conftest import create_room, create_user, future, login, make_png, web_booking, web_booking_form


async def _status(api, headers, booking_id, status, reason=None):
    body = {"status": status} | ({"reason": reason} if reason else {})
    return await api.post(f"/bookings/{booking_id}/status", json=body, headers=headers)


# ---------------------------------------------------------------------------
# Creación y precio (5.3)
# ---------------------------------------------------------------------------

async def test_precio_lo_calcula_el_servidor(api, db, room):
    response = await web_booking(api, room, future(10), future(13), total_amount="1", price_per_night="1")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["nights"] == 3
    assert body["total_amount"] == 600000
    assert body["deposit_amount"] == 300000 and body["deposit_percent"] == 50
    assert body["status"] == "pending_verification"
    assert body["code"].startswith("KW-")
    assert body["has_receipt"] is True and body["receipt_url"] == f"/bookings/{body['id']}/receipt"
    assert await db.room_nights.count_documents({"booking_id": ObjectId(body["id"])}) == 3


async def test_reserva_requiere_comprobante_y_consentimiento(api, room):
    sin_archivo = await api.post("/bookings", data=web_booking_form(room, future(2), future(3)))
    sin_consentimiento = await web_booking(api, room, future(2), future(3), accept_privacy_policy="false")
    assert sin_archivo.status_code == 422
    assert sin_consentimiento.status_code == 400


async def test_validaciones_de_fechas(api, room):
    pasado = await web_booking(api, room, hotel_today() - timedelta(days=1), future(2))
    invertidas = await web_booking(api, room, future(5), future(3))
    muy_larga = await web_booking(api, room, future(1), future(80))
    assert pasado.status_code == invertidas.status_code == muy_larga.status_code == 400


async def test_habitacion_inactiva_o_fuera_de_servicio_no_se_reserva(api, db, room, room_types):
    await db.rooms.update_one({"_id": room["_id"]}, {"$set": {"is_active": False}})
    fuera = await create_room(db, room_types["single"], "999", 90000, operational_status="out_of_service")
    assert (await web_booking(api, room, future(2), future(3))).status_code == 404
    assert (await web_booking(api, fuera, future(2), future(3))).status_code == 404


async def test_reserva_autenticada_queda_vinculada(api, client_user, client_headers, room):
    response = await web_booking(api, room, future(2), future(4), headers=client_headers)
    assert response.json()["user_id"] == str(client_user["_id"])
    mine = await api.get("/bookings/mine", headers=client_headers)
    assert [b["id"] for b in mine.json()] == [response.json()["id"]]


# ---------------------------------------------------------------------------
# Anti doble reserva (6.1)
# ---------------------------------------------------------------------------

async def test_solapamiento_responde_409_y_checkout_libre(api, room):
    assert (await web_booking(api, room, future(10), future(12))).status_code == 201
    choque = await web_booking(api, room, future(11), future(13))
    assert choque.status_code == 409 and choque.json()["code"] == "room_unavailable"
    # RN-03: el día de salida queda libre para una nueva entrada
    assert (await web_booking(api, room, future(12), future(14))).status_code == 201


async def test_reservas_concurrentes_solo_una_gana(api, db, room, storage_dirs):
    respuestas = await asyncio.gather(*[
        web_booking(api, room, future(20), future(23), email=f"persona{i}@example.com") for i in range(8)
    ])
    codigos = sorted(r.status_code for r in respuestas)
    assert codigos == [201] + [409] * 7, codigos
    assert await db.bookings.count_documents({}) == 1
    assert await db.room_nights.count_documents({}) == 3
    # Los comprobantes de las 7 reservas rechazadas no quedan huérfanos
    assert len(list(storage_dirs["private"].iterdir())) == 1


async def test_cancelar_libera_las_noches(api, admin_headers, room):
    booking = (await web_booking(api, room, future(5), future(7))).json()
    assert (await _status(api, admin_headers, booking["id"], "cancelled", "Solicitud del huésped")).status_code == 200
    assert (await web_booking(api, room, future(5), future(7))).status_code == 201


# ---------------------------------------------------------------------------
# Máquina de estados (6.4)
# ---------------------------------------------------------------------------

async def test_transiciones_invalidas_son_rechazadas(api, admin_headers, room):
    booking = (await web_booking(api, room, future(1), future(2))).json()
    response = await _status(api, admin_headers, booking["id"], "checked_out")
    assert response.status_code == 409 and response.json()["code"] == "invalid_transition"

    await _status(api, admin_headers, booking["id"], "cancelled", "prueba")
    revivir = await _status(api, admin_headers, booking["id"], "confirmed")
    assert revivir.status_code == 409


async def test_cancelar_y_rechazar_exigen_motivo(api, admin_headers, room):
    booking = (await web_booking(api, room, future(1), future(2))).json()
    assert (await _status(api, admin_headers, booking["id"], "cancelled")).status_code == 400
    assert (await _status(api, admin_headers, booking["id"], "pending_payment")).status_code == 400


async def test_rechazo_de_comprobante_y_nuevo_envio(api, anon, db, client_user, client_headers, admin_headers, room):
    booking = (await web_booking(api, room, future(3), future(5), headers=client_headers)).json()

    rechazo = await _status(anon, admin_headers, booking["id"], "pending_payment", "el valor no coincide")
    assert rechazo.status_code == 200
    assert rechazo.json()["payment_due_at"] is not None
    assert rechazo.json()["status_history"][-1]["reason"] == "el valor no coincide"

    aviso = await db.notifications.find_one({"user_id": client_user["_id"]})
    assert "el valor no coincide" in aviso["message"]

    nuevo = await api.post(f"/bookings/{booking['id']}/receipt",
                           files={"receipt": ("nuevo.png", make_png(color=(1, 2, 3)), "image/png")},
                           headers=client_headers)
    assert nuevo.status_code == 200, nuevo.text
    assert nuevo.json()["status"] == "pending_verification"
    assert nuevo.json()["payment_due_at"] is None


async def test_flujo_completo_con_folio(api, admin_headers, db, room):
    booking = (await web_booking(api, room, hotel_today(), future(2))).json()
    bid = booking["id"]
    assert (await _status(api, admin_headers, bid, "confirmed")).status_code == 200
    assert (await api.get(f"/folios/by-booking/{bid}", headers=admin_headers)).status_code == 404

    assert (await _status(api, admin_headers, bid, "checked_in")).status_code == 200
    folio = (await api.get(f"/folios/by-booking/{bid}", headers=admin_headers)).json()
    assert folio["number"] == 1 and folio["status"] == "open" and folio["total_amount"] == 400000

    folio = (await api.post(f"/folios/{folio['id']}/charges", json={"description": "Cena", "amount": 50000},
                            headers=admin_headers)).json()
    folio = (await api.post(f"/folios/{folio['id']}/charges", json={"description": "Lavandería", "amount": 20000},
                            headers=admin_headers)).json()
    assert folio["total_amount"] == 470000
    folio = (await api.delete(f"/folios/{folio['id']}/charges/{folio['charges'][1]['id']}", headers=admin_headers)).json()
    assert folio["total_amount"] == 450000

    assert (await _status(api, admin_headers, bid, "checked_out")).status_code == 200
    folio = (await api.get(f"/folios/by-booking/{bid}", headers=admin_headers)).json()
    assert folio["status"] == "closed"
    cerrado = await api.post(f"/folios/{folio['id']}/charges", json={"description": "Tarde", "amount": 1000},
                             headers=admin_headers)
    assert cerrado.status_code == 409

    # Salida anticipada: las noches desde hoy quedan libres
    assert await db.room_nights.count_documents({"booking_id": ObjectId(bid)}) == 0


async def test_no_se_hace_check_in_antes_de_la_fecha(api, admin_headers, room):
    booking = (await web_booking(api, room, future(3), future(4))).json()
    await _status(api, admin_headers, booking["id"], "confirmed")
    assert (await _status(api, admin_headers, booking["id"], "checked_in")).status_code == 409


async def test_numeracion_de_folios_es_consecutiva(api, admin_headers, db, room_types):
    numeros = []
    for i in range(3):
        room = await create_room(db, room_types["single"], f"5{i}", 100000)
        booking = (await web_booking(api, room, hotel_today(), future(1))).json()
        await _status(api, admin_headers, booking["id"], "confirmed")
        await _status(api, admin_headers, booking["id"], "checked_in")
        numeros.append((await api.get(f"/folios/by-booking/{booking['id']}", headers=admin_headers)).json()["number"])
    assert numeros == [1, 2, 3]


# ---------------------------------------------------------------------------
# Vencimiento del plazo de pago (6.2)
# ---------------------------------------------------------------------------

async def test_bot_solo_cancela_pendientes_de_pago_vencidas(api, admin_headers, db, room_types):
    rooms = [await create_room(db, room_types["single"], f"7{i}", 100000) for i in range(3)]
    vencida, vigente, por_verificar = [(await web_booking(api, r, future(3), future(4))).json()["id"] for r in rooms]
    for bid in (vencida, vigente):
        await _status(api, admin_headers, bid, "pending_payment", "comprobante ilegible")
    await db.bookings.update_one({"_id": ObjectId(vencida)}, {"$set": {"payment_due_at": utcnow() - timedelta(minutes=1)}})

    assert await expire_unpaid_bookings() == 1
    estados = {str(b["_id"]): b["status"] for b in await db.bookings.find().to_list(None)}
    assert estados == {vencida: "cancelled", vigente: "pending_payment", por_verificar: "pending_verification"}
    assert await db.room_nights.count_documents({"booking_id": ObjectId(vencida)}) == 0


# ---------------------------------------------------------------------------
# Edición de reservas
# ---------------------------------------------------------------------------

async def test_editar_fechas_valida_disponibilidad_y_recalcula(api, admin_headers, db, room):
    a = (await web_booking(api, room, future(10), future(12))).json()
    b = (await web_booking(api, room, future(14), future(16))).json()

    choque = await api.patch(f"/bookings/{a['id']}", json={"check_out": future(15).isoformat()}, headers=admin_headers)
    assert choque.status_code == 409
    assert await db.room_nights.count_documents({"booking_id": ObjectId(a["id"])}) == 2  # nada cambió

    ok = await api.patch(f"/bookings/{a['id']}", json={"check_out": future(14).isoformat()}, headers=admin_headers)
    assert ok.status_code == 200, ok.text
    assert ok.json()["nights"] == 4 and ok.json()["total_amount"] == 800000
    noches = await db.room_nights.find({"booking_id": ObjectId(a["id"])}).sort("night", 1).to_list(None)
    assert [n["night"] for n in noches] == [date_to_datetime(future(d)) for d in range(10, 14)]
    assert b  # la otra reserva sigue intacta
    auditoria = await api.get(f"/audit-logs?entity=booking&entity_id={a['id']}", headers=admin_headers)
    assert any(log["action"] == "update" for log in auditoria.json()["items"])


async def test_precio_negociado_solo_para_admin(api, anon, admin_headers, receptionist_headers, room):
    payload = {
        "room_id": str(room["_id"]), "check_in": future(30).isoformat(), "check_out": future(32).isoformat(),
        "guest": {"full_name": "Convenio Empresa", "email": "convenio@example.com"}, "total_amount": 300000,
    }
    assert (await anon.post("/bookings/manual", json=payload, headers=receptionist_headers)).status_code == 403
    response = await anon.post("/bookings/manual", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "confirmed" and body["source"] == "manual"
    assert body["total_amount"] == 300000 and body["calculated_amount"] == 400000 and body["deposit_amount"] == 150000


async def test_recepcion_crea_reserva_manual_con_tarifa(anon, receptionist_headers, room):
    payload = {
        "room_id": str(room["_id"]), "check_in": future(1).isoformat(), "check_out": future(2).isoformat(),
        "guest": {"full_name": "Walk In", "email": "walkin@example.com"},
        "companions": [{"full_name": "Acompañante Uno", "relationship": "Pareja"}],
    }
    response = await anon.post("/bookings/manual", json=payload, headers=receptionist_headers)
    assert response.status_code == 201, response.text
    assert response.json()["total_amount"] == 200000
    assert response.json()["created_by"] == "recepcion@example.com"


# ---------------------------------------------------------------------------
# Comprobantes privados (5.6) y acceso a reservas
# ---------------------------------------------------------------------------

async def test_acceso_a_comprobante_y_reserva(api, anon, db, admin_headers, receptionist_headers, client_headers, room):
    booking = (await web_booking(api, room, future(2), future(3))).json()  # de un invitado
    url = booking["receipt_url"]

    assert (await anon.get(url)).status_code == 401
    assert (await anon.get(url, headers=client_headers)).status_code == 404  # no es suya
    assert (await anon.get(f"/bookings/{booking['id']}", headers=client_headers)).status_code == 404
    for headers in (admin_headers, receptionist_headers):
        response = await anon.get(url, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["x-content-type-options"] == "nosniff"

    other = await create_user(db, "otro@example.com")
    other_headers = await login(anon, other["email"])
    assert (await anon.get(url, headers=other_headers)).status_code == 404


async def test_comprobante_no_es_publico(api, db, storage_dirs, room):
    booking = (await web_booking(api, room, future(2), future(3))).json()
    key = (await db.bookings.find_one({"_id": ObjectId(booking["id"])}))["receipt"]["key"]
    assert (storage_dirs["private"] / key).exists()
    assert list(storage_dirs["public"].iterdir()) == []
    from httpx import ASGITransport, AsyncClient
    from backend.app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as root:
        assert (await root.get(f"/static/uploads/{key}")).status_code == 404


async def test_listado_admin_resumen_global_y_filtros(api, admin_headers, db, room_types):
    for i in range(3):
        room = await create_room(db, room_types["single"], f"8{i}", 100000)
        await web_booking(api, room, future(2), future(3), email=f"g{i}@example.com")
    page = await api.get("/bookings?status=pending_verification&limit=1", headers=admin_headers)
    body = page.json()
    assert body["total"] == 3 and len(body["items"]) == 1
    assert body["summary"]["pending_verification"] == 3  # global, no solo la página (6.6)

    busqueda = await api.get("/bookings?q=g1@example", headers=admin_headers)
    assert busqueda.json()["total"] == 1


async def test_fechas_ocupadas_publicas(api, room):
    await web_booking(api, room, future(4), future(6))
    response = await api.get(f"/rooms/{room['_id']}/booked-dates")
    assert response.json() == [{"check_in": future(4).isoformat(), "check_out": future(6).isoformat()}]
