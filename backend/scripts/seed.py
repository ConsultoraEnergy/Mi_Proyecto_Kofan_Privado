"""
Semilla idempotente de la base de datos de Kawari.

    python -m backend.scripts.seed                 # índices, ajustes, tipos de habitación y admin
    python -m backend.scripts.seed --demo-rooms    # además, habitaciones de ejemplo

Variables usadas (backend/.env):
    SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD, SEED_ADMIN_NAME
Si no se define SEED_ADMIN_PASSWORD se genera una aleatoria y se muestra UNA sola vez.
Ejecutarla varias veces no duplica nada ni sobrescribe cambios hechos desde el panel.
"""

import argparse
import asyncio
import os
import secrets

from backend.app.core.security import hash_password
from backend.app.core.settings import get_settings
from backend.app.core.time import utcnow
from backend.app.db import client as mongo
from backend.app.db.indexes import ensure_database
from backend.app.modules.cms.service import ensure_defaults

ROOM_TYPES = [
    {"code": "cabin", "name": "Cabaña", "description": "Cabaña independiente.", "sort_order": 1},
    {"code": "family", "name": "Habitación familiar", "description": "Para grupos y familias.", "sort_order": 2},
    {"code": "single", "name": "Habitación individual", "description": "Para una o dos personas.", "sort_order": 3},
]

DEMO_ROOMS = [
    {
        "number": "101",
        "name": "Cabaña del Río",
        "type": "cabin",
        "price_per_night": 220000,
        "capacity": 4,
        "bedrooms": 2,
        "beds": "1 doble, 2 sencillas",
        "amenities": ["Wifi", "Baño privado", "Terraza"],
    },
    {
        "number": "201",
        "name": "Familiar Jardín",
        "type": "family",
        "price_per_night": 180000,
        "capacity": 5,
        "bedrooms": 2,
        "beds": "2 dobles, 1 sencilla",
        "amenities": ["Wifi", "Baño privado"],
    },
    {
        "number": "301",
        "name": "Individual Bosque",
        "type": "single",
        "price_per_night": 95000,
        "capacity": 2,
        "bedrooms": 1,
        "beds": "1 doble",
        "amenities": ["Wifi"],
    },
]


async def seed_database(db, demo_rooms: bool = False) -> None:
    mongo.use_database(db)
    await ensure_database(db)
    await ensure_defaults()
    print("✓ Índices, validadores y ajustes del sitio")

    now = utcnow()
    for room_type in ROOM_TYPES:
        await db.room_types.update_one(
            {"code": room_type["code"]},
            {"$setOnInsert": {**room_type, "is_active": True, "created_at": now, "updated_at": now}},
            upsert=True,
        )
    print(f"✓ Tipos de habitación: {', '.join(str(t['code']) for t in ROOM_TYPES)}")

    email = os.getenv("SEED_ADMIN_EMAIL", "admin@kawari.local").strip().lower()
    if await db.users.find_one({"email": email}):
        print(f"✓ Administrador ya existe: {email}")
    else:
        password = os.getenv("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(14)
        await db.users.insert_one(
            {
                "email": email,
                "full_name": os.getenv("SEED_ADMIN_NAME", "Administrador"),
                "password_hash": hash_password(password),
                "role": "admin",
                "is_active": True,
                "email_verified": True,
                "created_at": now,
                "updated_at": now,
            }
        )
        print(f"✓ Administrador creado: {email}")
        if not os.getenv("SEED_ADMIN_PASSWORD"):
            print(f"  Contraseña generada (guárdala, no se volverá a mostrar): {password}")

    if demo_rooms:
        types = {t["code"]: t["_id"] for t in await db.room_types.find({}).to_list(None)}
        for room in DEMO_ROOMS:
            data = {k: v for k, v in room.items() if k != "type"}
            await db.rooms.update_one(
                {"number": room["number"]},
                {
                    "$setOnInsert": {
                        **data,
                        "room_type_id": types[room["type"]],
                        "description": "",
                        "images": [],
                        "main_image": None,
                        "is_active": True,
                        "operational_status": "available",
                        "created_at": now,
                        "updated_at": now,
                        "created_by": "seed",
                    }
                },
                upsert=True,
            )
        print(f"✓ Habitaciones de ejemplo: {len(DEMO_ROOMS)}")


async def seed(demo_rooms: bool) -> None:
    settings = get_settings()
    db = await mongo.connect(settings)
    try:
        print(f"Base de datos: {settings.mongo_db_name}")
        await seed_database(db, demo_rooms)
    finally:
        await mongo.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Semilla idempotente de Hotel Kawari")
    parser.add_argument("--demo-rooms", action="store_true", help="Crear habitaciones de ejemplo")
    args = parser.parse_args()
    asyncio.run(seed(args.demo_rooms))


if __name__ == "__main__":
    main()
