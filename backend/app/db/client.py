"""
Conexión a MongoDB con la API async nativa de PyMongo (reemplaza a Motor, que está deprecado).

Los repositorios obtienen la base de datos con `get_db()` en cada llamada; así las pruebas pueden
apuntar a otra base con `use_database()`.
"""

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from backend.app.core.settings import Settings


class _MongoState:
    client: AsyncMongoClient | None = None
    db: AsyncDatabase | None = None


_state = _MongoState()


def create_client(uri: str) -> AsyncMongoClient:
    return AsyncMongoClient(uri, tz_aware=True, uuidRepresentation="standard", appname="hotel-kawari")


async def connect(settings: Settings) -> AsyncDatabase:
    _state.client = create_client(settings.mongo_uri.get_secret_value())
    _state.db = _state.client[settings.mongo_db_name]
    return _state.db


async def close() -> None:
    if _state.client is not None:
        await _state.client.close()
    _state.client = None
    _state.db = None


def use_database(db: AsyncDatabase | None) -> None:
    """Fija la base de datos activa (usado por las pruebas)."""
    _state.db = db


def get_db() -> AsyncDatabase:
    if _state.db is None:
        raise RuntimeError("La base de datos no está conectada. ¿Se ejecutó el lifespan de la app?")
    return _state.db
