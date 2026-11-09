import logging
import secrets
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.core.security import create_access_token, create_refresh_token, verify_password, hash_password
from backend.services.user_service import get_user_by_email

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"])

# 5.12: un único mensaje para correo inexistente, contraseña errónea o cuenta inactiva,
# para no revelar qué correos están registrados.
INVALID_CREDENTIALS_MESSAGE = "Correo o contraseña incorrectos"

_DUMMY_HASH: str | None = None


def _dummy_hash() -> str:
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
    return _DUMMY_HASH


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)

    # Siempre se ejecuta bcrypt (con un hash ficticio si el correo no existe) para que
    # el tiempo de respuesta tampoco delate qué correos están registrados.
    password_ok = verify_password(form_data.password, user.get("password") if user else _dummy_hash())

    credenciales_validas = (
        user is not None
        and password_ok
        and user.get("is_active", True) is not False  # 5.9
    )

    if not credenciales_validas:
        logger.info("Intento de login fallido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Usamos el ID del usuario (convertido a string) como "sub"
    user_id_str = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id_str})
    refresh_token = create_refresh_token(data={"sub": user_id_str})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
