from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.errors import Forbidden, Unauthorized
from backend.app.core.permissions import Permission, has_permission
from backend.app.core.security import decode_access_token
from backend.app.modules.users.service import get_active_user

_bearer = HTTPBearer(auto_error=False)

_INVALID = "Sesión inválida o expirada. Inicia sesión de nuevo."


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized("Debes iniciar sesión.")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise Unauthorized(_INVALID)
    return await get_active_user(user_id)


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict | None:
    """Usuario si envió un token; None si es anónimo. Un token inválido sí es un error (401)."""
    if credentials is None:
        return None
    return await get_current_user(credentials)


def require_permission(*permissions: Permission):
    async def dependency(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        missing = [p for p in permissions if not has_permission(user["role"], p)]
        if missing:
            raise Forbidden("No tienes permiso para realizar esta acción.")
        return user

    return dependency


CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_optional_user)]
