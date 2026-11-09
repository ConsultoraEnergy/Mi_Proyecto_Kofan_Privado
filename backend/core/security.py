from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from backend.core.config import (
    SECRET,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Claim "type" para distinguir tokens: un refresh token NO sirve como access token (5.4).
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    if len(password) > 72:
        raise ValueError("La contraseña es demasiado larga (máximo 72 caracteres)")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode.update({
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_delta,
    })
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, TOKEN_TYPE_ACCESS, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict) -> str:
    return _create_token(data, TOKEN_TYPE_REFRESH, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
