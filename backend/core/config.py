import os
from pathlib import Path
from dotenv import load_dotenv

# Cargamos el .env desde la carpeta backend/
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"La variable de entorno {name} debe ser un número entero.") from exc


# --- SEGURIDAD JWT ---
# Sin valor por defecto: si falta o es débil, el servidor NO arranca (5.7).
SECRET = os.getenv("SECRET_KEY", "")
_MIN_SECRET_LENGTH = 32
_INSECURE_SECRETS = {"mysecretkey", "secret", "changeme", "change-me"}

if len(SECRET) < _MIN_SECRET_LENGTH or SECRET.lower() in _INSECURE_SECRETS:
    raise RuntimeError(
        "SECRET_KEY no está definida o es insegura. Defínela en backend/.env con al menos "
        f"{_MIN_SECRET_LENGTH} caracteres aleatorios, por ejemplo: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- RESERVAS ---
# Porcentaje del total que se cobra como anticipo (RN-04).
DEPOSIT_PERCENT = _env_int("DEPOSIT_PERCENT", 50)
# Horas que puede permanecer una reserva "pendiente" SIN comprobante antes de cancelarse (6.2).
BOOKING_PENDING_EXPIRATION_HOURS = _env_int("BOOKING_PENDING_EXPIRATION_HOURS", 48)
# Cada cuántos minutos se revisan las reservas vencidas.
BOOKING_EXPIRATION_CHECK_MINUTES = _env_int("BOOKING_EXPIRATION_CHECK_MINUTES", 15)

# --- ARCHIVOS ---
# Público: fotos de habitaciones, galería y logo (servido en /static/uploads).
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
# Privado: comprobantes de pago. NUNCA se monta como estático (5.6).
PRIVATE_UPLOAD_DIR = os.getenv("PRIVATE_UPLOAD_DIR") or os.path.join(BASE_DIR, "private_uploads")
MAX_IMAGE_SIZE_MB = _env_int("MAX_IMAGE_SIZE_MB", 8)
MAX_RECEIPT_SIZE_MB = _env_int("MAX_RECEIPT_SIZE_MB", 5)
