import pytest

pytestmark = pytest.mark.asyncio


async def test_login_exitoso_retorna_tokens(api_client, admin_user):
    response = await api_client.post(
        "/auth/login",
        data={"username": admin_user["email"], "password": "Admin123*"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"].lower() == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_falla_con_credenciales_invalidas(api_client, admin_user):
    response = await api_client.post(
        "/auth/login",
        data={"username": admin_user["email"], "password": "clave-incorrecta"},
    )

    assert response.status_code == 401
    # Mensaje genérico: no revela si el correo existe (5.12)
    assert response.json()["detail"] == "Correo o contraseña incorrectos"


async def test_crud_basico_de_usuario_con_perfil(api_client, admin_headers):
    nuevo_usuario = {
        "tipo_persona": "natural",
        "full_name": "Recepción Prueba",
        "type_document": "CC",
        "number_document": "123456789",
        "email": "recepcion@kofan.com",
        "country": "Colombia",
        "city": "Puerto Asís",
        "phone": "3101234567",
        "password": "Recepcion123*",
        "role": "client",
        "is_active": True,
    }

    crear = await api_client.post("/users/", json=nuevo_usuario, headers=admin_headers)
    assert crear.status_code == 201, f"Error de Validación de FastAPI: {crear.json()}"
    assert crear.status_code == 201
    user_id = crear.json()["user_id"]
    assert user_id

    login = await api_client.post(
    "/auth/login",
    data={"username": "recepcion@kofan.com", "password": nuevo_usuario["password"]},
    )
    assert login.status_code == 200
    token_data = login.json()
    user_headers = {"Authorization": f"{token_data['token_type']} {token_data['access_token']}"}

    perfil = await api_client.get("/users/me", headers=user_headers)
    assert perfil.status_code == 200
    assert perfil.json()["email"] == nuevo_usuario["email"]

    actualiza = await api_client.patch(
        "/users/update-me",
        json={"full_name": "Recepción Editada", "phone": "3205550000"},
        headers=user_headers,
    )
    assert actualiza.status_code == 200
    assert actualiza.json()["user"]["full_name"] == "Recepción Editada"
    assert actualiza.json()["user"]["phone"] == "3205550000"


async def test_creacion_de_reserva_y_bloqueo_por_solapamiento(api_client, sample_room, png_bytes):
    payload = {
        "habitacion_id": str(sample_room["_id"]),
        "fecha_entrada": "2026-04-20",
        "fecha_salida": "2026-04-22",
        "monto_total": "360000",
        "cliente_nombre": "Nelson Prueba",
        "cliente_email": "nelson@example.com",
        "cliente_celular": "3201234567",
        "observaciones": "Reserva de prueba",
    }

    comprobante = {"comprobante": ("pago.png", png_bytes, "image/png")}

    primera = await api_client.post("/api/reservas/invitado", data=payload, files=comprobante)
    assert primera.status_code == 200
    assert primera.json()["reserva_id"]

    segunda = await api_client.post(
        "/api/reservas/invitado",
        data={
            **payload,
            "cliente_email": "otro@example.com",
            "fecha_entrada": "2026-04-21",
            "fecha_salida": "2026-04-23",
        },
        files=comprobante,
    )

    assert segunda.status_code == 400
    assert "ya está reservada" in segunda.json()["detail"]


async def test_habitaciones_lista_general_y_publica_respetan_estados(api_client, test_db, sample_room):
    room_mantenimiento = {
        "room_number": "102",
        "name": "Habitación Mantenimiento",
        "description": "Bloqueada temporalmente",
        "price": 95000,
        "capacity": 1,
        "stock": 1,
        "images": [],
        "main_image": None,
        "active": False,
        "is_available": False,
        "type": "individual",
        "num_cuartos": 1,
        "tipo_camas": "1 cama sencilla",
        "amenities": [],
        "created_by": "admin@kofan.test",
        "updated_by": "admin@kofan.test",
    }
    result = await test_db.rooms.insert_one(room_mantenimiento)
    room_mantenimiento["_id"] = result.inserted_id

    listado = await api_client.get("/rooms/?page=1&limit=10")
    assert listado.status_code == 200
    data = listado.json()
    assert len(data["data"]) >= 2

    publicas = await api_client.get("/rooms/public")
    assert publicas.status_code == 200
    ids_publicos = {room["id"] for room in publicas.json()}

    assert str(sample_room["_id"]) in ids_publicos
    assert str(room_mantenimiento["_id"]) not in ids_publicos
