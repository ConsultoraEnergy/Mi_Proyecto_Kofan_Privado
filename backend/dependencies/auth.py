from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from backend.core.config import SECRET, ALGORITHM
from backend.core.security import TOKEN_TYPE_ACCESS
from backend.services.user_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Valida el access token y devuelve el usuario activo dueño del token."""
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise _credentials_exception()

    # 5.4: solo se aceptan access tokens (un refresh token de 7 días no abre sesión).
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise _credentials_exception()

    user_id = payload.get("sub")
    if not user_id:
        raise _credentials_exception()

    user = await get_user_by_id(user_id)
    if user is None:
        raise _credentials_exception()

    # 5.9: una cuenta suspendida o desactivada pierde el acceso inmediatamente.
    if user.get("is_active", True) is False:
        raise _credentials_exception()

    return user


async def required_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado")
    return user
