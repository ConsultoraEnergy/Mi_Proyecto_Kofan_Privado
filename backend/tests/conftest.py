"""
Infraestructura de pruebas.

Se usa un MongoDB REAL (no un simulador): un `mongod` temporal en un puerto libre y una carpeta
temporal, que se destruye al terminar. Cada prueba usa su propia base de datos.

- Si existe la variable MONGO_TEST_URI, se usa ese servidor en lugar de lanzar uno.
- Si no, se busca `mongod` en MONGOD_PATH, en el PATH o en C:\\Program Files\\MongoDB\\Server\\*\\bin.
"""
import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

# --- Entorno de prueba: se fija ANTES de importar la aplicación ---
os.environ.update({
    "APP_ENV": "test",
    "SECRET_KEY": "test-secret-key-solo-para-pruebas-0123456789abcdef",
    "MONGO_URI": "mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=100",  # nunca Atlas
    "MONGO_DB_NAME": "kawari_test",
    "SCHEDULER_ENABLED": "false",
    "EMAIL_BACKEND": "console",
    "FRONTEND_URL": "http://frontend.test",
    "DEPOSIT_PERCENT": "50",
    "BOOKING_PAYMENT_DEADLINE_HOURS": "48",
})

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from PIL import Image  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from backend.app.core.security import hash_password  # noqa: E402
from backend.app.core.settings import get_settings  # noqa: E402
from backend.app.core.time import hotel_today, utcnow  # noqa: E402
from backend.app.db import client as mongo  # noqa: E402
from backend.app.db.indexes import ensure_database  # noqa: E402
from backend.app.modules.notifications import email as email_module  # noqa: E402

PASSWORD = "Clave-Segura-123"


# ---------------------------------------------------------------------------
# Servidor MongoDB de pruebas
# ---------------------------------------------------------------------------

def _find_mongod() -> str | None:
    candidates = [os.getenv("MONGOD_PATH"), shutil.which("mongod")]
    candidates += sorted(glob.glob(r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe"), reverse=True)
    return next((c for c in candidates if c and Path(c).exists()), None)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def mongo_uri():
    if os.getenv("MONGO_TEST_URI"):
        yield os.environ["MONGO_TEST_URI"]
        return
    mongod = _find_mongod()
    if not mongod:
        pytest.exit("No se encontró mongod. Instala MongoDB o define MONGO_TEST_URI.", returncode=2)

    dbpath = tempfile.mkdtemp(prefix="kawari-mongo-")
    port = _free_port()
    process = subprocess.Popen(
        [mongod, "--dbpath", dbpath, "--port", str(port), "--bind_ip", "127.0.0.1", "--quiet",
         "--setParameter", "diagnosticDataCollectionEnabled=false"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    uri = f"mongodb://127.0.0.1:{port}/?serverSelectionTimeoutMS=2000"
    deadline = time.time() + 30
    while True:
        try:
            MongoClient(uri).admin.command("ping")
            break
        except Exception:
            if time.time() > deadline or process.poll() is not None:
                process.kill()
                pytest.exit("No se pudo iniciar el mongod de pruebas.", returncode=2)
            time.sleep(0.2)
    yield uri
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
    shutil.rmtree(dbpath, ignore_errors=True)


@pytest.fixture(autouse=True)
def storage_dirs(tmp_path, monkeypatch):
    settings = get_settings()
    public, private = tmp_path / "uploads", tmp_path / "private"
    public.mkdir()
    private.mkdir()
    monkeypatch.setattr(settings, "upload_dir", public)
    monkeypatch.setattr(settings, "private_upload_dir", private)
    email_module.outbox.clear()
    return {"public": public, "private": private}


@pytest_asyncio.fixture
async def db(mongo_uri):
    client = mongo.create_client(mongo_uri)
    database = client[f"kawari_test_{uuid.uuid4().hex[:12]}"]
    await ensure_database(database)
    mongo.use_database(database)
    yield database
    mongo.use_database(None)
    await client.drop_database(database.name)
    await client.close()


@pytest_asyncio.fixture
async def api(db):
    from backend.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver/api/v1") as client:
        yield client


@pytest_asyncio.fixture
async def anon(db):
    """Segundo cliente sin cookies (otra persona / otro navegador)."""
    from backend.app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver/api/v1") as client:
        yield client


# ---------------------------------------------------------------------------
# Datos de prueba
# ---------------------------------------------------------------------------

async def create_user(db, email: str, role: str = "client", *, verified: bool = True, active: bool = True,
                      document: str | None = None, password: str = PASSWORD) -> dict:
    doc = {
        "email": email, "full_name": email.split("@")[0].title(), "password_hash": hash_password(password),
        "role": role, "is_active": active, "email_verified": verified, "person_type": "natural",
        "document_type": "CC" if document else None, "document_number": document,
        "created_at": utcnow(), "updated_at": utcnow(),
    }
    doc["_id"] = (await db.users.insert_one(doc)).inserted_id
    return doc


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> dict:
    response = await client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def admin(db):
    return await create_user(db, "admin@example.com", "admin")


@pytest_asyncio.fixture
async def receptionist(db):
    return await create_user(db, "recepcion@example.com", "receptionist")


@pytest_asyncio.fixture
async def client_user(db):
    return await create_user(db, "cliente@example.com", "client", document="1000001")


@pytest_asyncio.fixture
async def admin_headers(anon, admin):
    return await login(anon, admin["email"])


@pytest_asyncio.fixture
async def receptionist_headers(anon, receptionist):
    return await login(anon, receptionist["email"])


@pytest_asyncio.fixture
async def client_headers(anon, client_user):
    return await login(anon, client_user["email"])


@pytest_asyncio.fixture
async def room_types(db):
    now = utcnow()
    types = {}
    for i, (code, name) in enumerate([("cabin", "Cabaña"), ("family", "Familiar"), ("single", "Individual")]):
        doc = {"code": code, "name": name, "description": "", "is_active": True, "sort_order": i,
               "created_at": now, "updated_at": now}
        doc["_id"] = (await db.room_types.insert_one(doc)).inserted_id
        types[code] = doc
    return types


async def create_room(db, room_type: dict, number: str, price: float, capacity: int = 2, **extra) -> dict:
    doc = {
        "number": number, "name": f"Habitación {number}", "room_type_id": room_type["_id"], "description": "",
        "price_per_night": price, "capacity": capacity, "bedrooms": 1, "beds": "", "amenities": [],
        "images": [], "main_image": None, "is_active": True, "operational_status": "available",
        "created_at": utcnow(), "updated_at": utcnow(), **extra,
    }
    doc["_id"] = (await db.rooms.insert_one(doc)).inserted_id
    return doc


@pytest_asyncio.fixture
async def room(db, room_types):
    return await create_room(db, room_types["cabin"], "101", 200000, capacity=4)


def make_png(size=(4, 4), color=(20, 120, 60)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def future(days: int) -> date:
    return hotel_today() + timedelta(days=days)


def web_booking_form(room: dict, check_in: date, check_out: date, email: str = "huesped@example.com", **extra) -> dict:
    return {
        "room_id": str(room["_id"]),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "full_name": "Huésped Prueba",
        "email": email,
        "phone": "3001234567",
        "accept_privacy_policy": "true",
        **extra,
    }


async def web_booking(client: AsyncClient, room: dict, check_in: date, check_out: date, headers=None, **extra):
    return await client.post(
        "/bookings",
        data=web_booking_form(room, check_in, check_out, **extra),
        files={"receipt": ("pago.png", make_png(), "image/png")},
        headers=headers or {},
    )


def token_from_outbox(path: str) -> str:
    """Extrae el token del último correo enviado que contenga el enlace indicado."""
    for message in reversed(email_module.outbox):
        match = re.search(re.escape(path) + r"\?token=([\w-]+)", message.text)
        if match:
            return match.group(1)
    raise AssertionError(f"No hay correos con enlace a {path}")
