import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

print(f"📂 Buscando .env en: {ENV_PATH}")

load_dotenv(dotenv_path=ENV_PATH)

uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("❌ ¡ALERTA! MONGO_URI está vacío. El archivo .env no está ahí o está vacío.")

try:
    client = AsyncIOMotorClient(uri)
    db = client.kofan_hospedaje_db 
    print("✅ ¡Conexión asíncrona preparada para MongoDB Atlas!")
except Exception as e:
    print(f"❌ Error al configurar la conexión: {e}")