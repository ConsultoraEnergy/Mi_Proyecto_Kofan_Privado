"""
Migra los comprobantes de pago antiguos (guardados en la carpeta PÚBLICA static/uploads)
al almacenamiento privado (5.6).

Uso, desde la raíz del repositorio:

    python -m backend.scripts.migrar_comprobantes_privados            # simulación (no cambia nada)
    python -m backend.scripts.migrar_comprobantes_privados --aplicar  # ejecuta la migración

Por cada reserva con `comprobante_url = /static/uploads/<archivo>`:
  1. mueve el archivo a PRIVATE_UPLOAD_DIR,
  2. guarda `comprobante_archivo = <archivo>` y elimina `comprobante_url`.
Es idempotente: se puede ejecutar varias veces.
"""
import argparse
import asyncio
import os
import re
import shutil
from pathlib import Path

from backend.core.config import PRIVATE_UPLOAD_DIR, UPLOAD_DIR
from backend.db.client import db

PREFIJO = "/static/uploads/"
NOMBRE_RE = re.compile(r"^([0-9a-f]{32})\.(jpg|jpeg|png|webp|pdf)$", re.IGNORECASE)


async def migrar(aplicar: bool) -> None:
    os.makedirs(PRIVATE_UPLOAD_DIR, exist_ok=True)
    query = {
        "comprobante_url": {"$regex": f"^{re.escape(PREFIJO)}"},
        "comprobante_archivo": {"$in": [None, ""]},
    }
    movidos, faltantes, invalidos = 0, 0, 0

    async for reserva in db.bookings.find(query, {"comprobante_url": 1}):
        nombre = reserva["comprobante_url"][len(PREFIJO):]
        match = NOMBRE_RE.match(nombre)
        if not match:
            invalidos += 1
            print(f"[OMITIDO] Reserva {reserva['_id']}: nombre de archivo inesperado '{nombre}'")
            continue

        nuevo_nombre = f"{match.group(1).lower()}.{match.group(2).lower()}"
        origen = Path(UPLOAD_DIR) / nombre
        destino = Path(PRIVATE_UPLOAD_DIR) / nuevo_nombre

        if not origen.exists() and not destino.exists():
            faltantes += 1
            print(f"[FALTA]   Reserva {reserva['_id']}: no existe {origen}")
            continue

        print(f"[MOVER]   Reserva {reserva['_id']}: {nombre} -> privado/{nuevo_nombre}")
        if aplicar:
            if origen.exists():
                shutil.move(str(origen), str(destino))
            await db.bookings.update_one(
                {"_id": reserva["_id"]},
                {"$set": {"comprobante_archivo": nuevo_nombre}, "$unset": {"comprobante_url": ""}},
            )
        movidos += 1

    modo = "APLICADO" if aplicar else "SIMULACIÓN (usa --aplicar para ejecutar)"
    print(f"\n{modo}: {movidos} a migrar/migrados, {faltantes} sin archivo, {invalidos} omitidos.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="Ejecuta la migración (por defecto solo simula).")
    args = parser.parse_args()
    asyncio.run(migrar(args.aplicar))


if __name__ == "__main__":
    main()
