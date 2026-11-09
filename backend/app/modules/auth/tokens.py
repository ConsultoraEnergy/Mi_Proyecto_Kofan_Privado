"""
Tokens opacos persistidos (solo se guarda su hash SHA-256):

- refresh_tokens: sesión de larga duración en cookie HttpOnly. Se rota en cada uso; si se reutiliza
  un token ya rotado (posible robo) se revoca toda la familia (todas las sesiones derivadas).
- email_tokens: enlaces de un solo uso (verificar correo, restablecer/definir contraseña).
"""
import uuid
from datetime import timedelta
from enum import StrEnum

from bson import ObjectId
from pymongo import ReturnDocument

from backend.app.core.errors import Unauthorized, ValidationFailed
from backend.app.core.security import generate_opaque_token, hash_token
from backend.app.core.settings import get_settings
from backend.app.core.time import ensure_utc, utcnow
from backend.app.db.client import get_db

# Si dos pestañas refrescan a la vez con el mismo token, la segunda no debe disparar la alarma de robo.
REFRESH_REUSE_GRACE_SECONDS = 30

_INVALID_SESSION = "Sesión inválida o expirada. Inicia sesión de nuevo."


class EmailTokenPurpose(StrEnum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"
    SET_PASSWORD = "set_password"


# ---------------------------------------------------------------------------
# Refresh tokens
# ---------------------------------------------------------------------------

async def issue_refresh_token(user_id: ObjectId, family_id: str | None = None) -> str:
    raw = generate_opaque_token()
    now = utcnow()
    await get_db().refresh_tokens.insert_one({
        "token_hash": hash_token(raw),
        "user_id": user_id,
        "family_id": family_id or uuid.uuid4().hex,
        "created_at": now,
        "expires_at": now + timedelta(days=get_settings().refresh_token_expire_days),
        "revoked_at": None,
        "replaced_by": None,
    })
    return raw


async def rotate_refresh_token(raw: str | None) -> tuple[ObjectId, str]:
    """Consume un refresh token y emite uno nuevo de la misma familia. Devuelve (user_id, nuevo_token)."""
    if not raw:
        raise Unauthorized(_INVALID_SESSION)
    tokens = get_db().refresh_tokens
    token_hash = hash_token(raw)
    now = utcnow()
    new_raw = generate_opaque_token()
    new_hash = hash_token(new_raw)

    current = await tokens.find_one_and_update(
        {"token_hash": token_hash, "revoked_at": None, "expires_at": {"$gt": now}},
        {"$set": {"revoked_at": now, "replaced_by": new_hash}},
        return_document=ReturnDocument.BEFORE,
    )
    if current is None:
        existing = await tokens.find_one({"token_hash": token_hash})
        if existing and existing.get("revoked_at"):
            revoked_at = ensure_utc(existing["revoked_at"])
            in_grace = existing.get("replaced_by") and (now - revoked_at).total_seconds() < REFRESH_REUSE_GRACE_SECONDS
            if not in_grace:
                # Reutilización de un token ya rotado: se asume robo y se cierran todas las sesiones de la familia.
                await revoke_family(existing["family_id"])
        raise Unauthorized(_INVALID_SESSION)

    await tokens.insert_one({
        "token_hash": new_hash,
        "user_id": current["user_id"],
        "family_id": current["family_id"],
        "created_at": now,
        "expires_at": now + timedelta(days=get_settings().refresh_token_expire_days),
        "revoked_at": None,
        "replaced_by": None,
    })
    return current["user_id"], new_raw


async def revoke_family(family_id: str) -> None:
    await get_db().refresh_tokens.update_many(
        {"family_id": family_id, "revoked_at": None}, {"$set": {"revoked_at": utcnow()}}
    )


async def revoke_refresh_token(raw: str | None) -> None:
    """Logout: invalida la sesión actual (toda su familia)."""
    if not raw:
        return
    token = await get_db().refresh_tokens.find_one({"token_hash": hash_token(raw)})
    if token:
        await revoke_family(token["family_id"])


async def revoke_all_for_user(user_id: ObjectId) -> None:
    await get_db().refresh_tokens.update_many(
        {"user_id": user_id, "revoked_at": None}, {"$set": {"revoked_at": utcnow()}}
    )


# ---------------------------------------------------------------------------
# Tokens de correo (un solo uso)
# ---------------------------------------------------------------------------

def _ttl(purpose: EmailTokenPurpose) -> timedelta:
    settings = get_settings()
    return {
        EmailTokenPurpose.VERIFY_EMAIL: timedelta(hours=settings.email_verification_expire_hours),
        EmailTokenPurpose.RESET_PASSWORD: timedelta(minutes=settings.password_reset_expire_minutes),
        EmailTokenPurpose.SET_PASSWORD: timedelta(hours=settings.set_password_expire_hours),
    }[purpose]


async def create_email_token(user_id: ObjectId, purpose: EmailTokenPurpose) -> str:
    tokens = get_db().email_tokens
    # Un enlace nuevo invalida los anteriores del mismo tipo.
    await tokens.delete_many({"user_id": user_id, "purpose": purpose.value, "used_at": None})
    raw = generate_opaque_token()
    now = utcnow()
    await tokens.insert_one({
        "token_hash": hash_token(raw),
        "user_id": user_id,
        "purpose": purpose.value,
        "created_at": now,
        "expires_at": now + _ttl(purpose),
        "used_at": None,
    })
    return raw


async def consume_email_token(raw: str, purposes: set[EmailTokenPurpose]) -> dict:
    token = await get_db().email_tokens.find_one_and_update(
        {
            "token_hash": hash_token(raw),
            "purpose": {"$in": [p.value for p in purposes]},
            "used_at": None,
            "expires_at": {"$gt": utcnow()},
        },
        {"$set": {"used_at": utcnow()}},
    )
    if token is None:
        raise ValidationFailed("El enlace no es válido o ya venció. Solicita uno nuevo.", code="invalid_token")
    return token
