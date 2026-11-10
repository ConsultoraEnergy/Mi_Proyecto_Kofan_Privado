"""
Contraseñas (pwdlib + Argon2) y JWT de acceso (PyJWT).

El refresh token NO es un JWT: es un valor opaco aleatorio guardado (hasheado) en la colección
refresh_tokens, lo que permite rotarlo, revocarlo y detectar su reutilización.
"""

import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from backend.app.core.settings import get_settings
from backend.app.core.time import utcnow

ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"  # noqa: S105 (tipo de token, no un secreto)

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_password_hash = PasswordHash((Argon2Hasher(),))
_DUMMY_HASH = _password_hash.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Siempre ejecuta Argon2 (con un hash ficticio si no hay hash) para no filtrar por tiempo
    si el usuario existe."""
    if not password_hash:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: str) -> tuple[str, int]:
    """Devuelve (token, segundos de vigencia)."""
    settings = get_settings()
    expires_in = settings.access_token_expire_minutes * 60
    now = utcnow()
    payload = {
        "sub": user_id,
        "type": TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> str | None:
    """Devuelve el id del usuario si el token es un access token válido; None en otro caso."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        return None
    return payload.get("sub")


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Los tokens opacos (refresh, verificación, recuperación) se guardan solo hasheados."""
    return hashlib.sha256(token.encode()).hexdigest()
