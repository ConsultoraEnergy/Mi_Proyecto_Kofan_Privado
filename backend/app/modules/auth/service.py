"""
Autenticación (5.4, 5.5, 5.9, 5.10, 5.12 y backlog Fase 1):
login, refresh con rotación, logout, verificación de correo y recuperación de contraseña.
"""

import logging
from dataclasses import dataclass

from fastapi import BackgroundTasks
from pydantic import BaseModel

from backend.app.core.errors import Unauthorized
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.core.time import utcnow
from backend.app.modules.auth import tokens
from backend.app.modules.bookings import repository as bookings_repository
from backend.app.modules.notifications import service as notifications
from backend.app.modules.notifications.email import send_email
from backend.app.modules.users import repository as users_repository
from backend.app.modules.users.schemas import UserOut
from backend.app.modules.users.service import get_active_user, to_out

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Correo o contraseña incorrectos"


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 (esquema OAuth2, no un secreto)
    expires_in: int
    user: UserOut


class VerifyEmailOut(BaseModel):
    message: str
    linked_bookings: int


@dataclass
class Session:
    token: TokenOut
    refresh_token: str


def _token_out(user: dict) -> TokenOut:
    access_token, expires_in = create_access_token(str(user["_id"]))
    return TokenOut(access_token=access_token, expires_in=expires_in, user=to_out(user))


async def login(email: str, password: str) -> Session:
    user = await users_repository.get_by_email(email)
    password_ok = verify_password(password, user.get("password_hash") if user else None)
    if not (user and password_ok and user.get("is_active", True)):
        logger.info("Intento de login fallido")
        raise Unauthorized(INVALID_CREDENTIALS, code="invalid_credentials")

    await users_repository.update(user["_id"], {"last_login_at": utcnow()})
    refresh = await tokens.issue_refresh_token(user["_id"])
    return Session(token=_token_out(user), refresh_token=refresh)


async def refresh(raw_refresh_token: str | None) -> Session:
    user_id, new_refresh = await tokens.rotate_refresh_token(raw_refresh_token)
    try:
        user = await get_active_user(str(user_id))
    except Unauthorized:
        await tokens.revoke_all_for_user(user_id)
        raise
    return Session(token=_token_out(user), refresh_token=new_refresh)


async def logout(raw_refresh_token: str | None) -> None:
    await tokens.revoke_refresh_token(raw_refresh_token)


async def _mark_email_verified(user: dict) -> int:
    """Marca el correo como verificado y, solo entonces, vincula las reservas de invitado (5.5)."""
    if user.get("email_verified"):
        return 0
    await users_repository.update(user["_id"], {"email_verified": True, "email_verified_at": utcnow()})
    return await bookings_repository.link_guest_bookings(user["email"], user["_id"])


async def verify_email(raw: str) -> VerifyEmailOut:
    token = await tokens.consume_email_token(raw, {tokens.EmailTokenPurpose.VERIFY_EMAIL})
    user = await users_repository.get_by_id(token["user_id"])
    if user is None:
        raise Unauthorized("La cuenta ya no existe.")
    linked = await _mark_email_verified(user)
    return VerifyEmailOut(message="¡Correo verificado!", linked_bookings=linked)


async def forgot_password(email: str, background: BackgroundTasks) -> None:
    """Siempre responde igual (no revela si el correo está registrado)."""
    user = await users_repository.get_by_email(email)
    if not user or not user.get("is_active", True):
        return
    raw = await tokens.create_email_token(user["_id"], tokens.EmailTokenPurpose.RESET_PASSWORD)
    background.add_task(send_email, notifications.password_reset_email(user["email"], user["full_name"], raw))


async def reset_password(raw: str, new_password: str) -> None:
    token = await tokens.consume_email_token(
        raw, {tokens.EmailTokenPurpose.RESET_PASSWORD, tokens.EmailTokenPurpose.SET_PASSWORD}
    )
    user = await users_repository.get_by_id(token["user_id"])
    if user is None or not user.get("is_active", True):
        raise Unauthorized("La cuenta no está disponible.")
    await users_repository.update(user["_id"], {"password_hash": hash_password(new_password)})
    await tokens.revoke_all_for_user(user["_id"])
    # Usar un enlace enviado a su correo demuestra que el usuario controla esa dirección.
    await _mark_email_verified(user)
