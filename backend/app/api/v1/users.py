from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from backend.app.api.deps import CurrentUser, require_permission
from backend.app.core.permissions import Permission, Role
from backend.app.modules.users import service
from backend.app.modules.users.schemas import (
    ChangePasswordIn,
    UserCreateByStaff,
    UserOut,
    UserPage,
    UserStatusIn,
    UserUpdateByStaff,
    UserUpdateMe,
)

router = APIRouter(prefix="/users", tags=["users"])


# --- Autoservicio ---


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser):
    return service.to_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(data: UserUpdateMe, user: CurrentUser):
    return await service.update_me(user, data)


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: ChangePasswordIn, user: CurrentUser):
    await service.change_password(user, data)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_me(user: CurrentUser):
    await service.deactivate_me(user)


# --- Gestión por el personal ---


@router.get("", response_model=UserPage)
async def list_users(
    _: Annotated[dict, Depends(require_permission(Permission.USERS_READ))],
    q: str | None = Query(default=None, max_length=100),
    role: Role | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await service.list_users(q, role.value if role else None, page, limit)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateByStaff,
    background: BackgroundTasks,
    actor: Annotated[dict, Depends(require_permission(Permission.USERS_CREATE))],
):
    return await service.create_by_staff(actor, data, background)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, _: Annotated[dict, Depends(require_permission(Permission.USERS_READ))]):
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    data: UserUpdateByStaff,
    actor: Annotated[dict, Depends(require_permission(Permission.USERS_UPDATE))],
):
    return await service.update_by_staff(actor, user_id, data)


@router.patch("/{user_id}/status", response_model=UserOut)
async def set_user_status(
    user_id: str,
    data: UserStatusIn,
    actor: Annotated[dict, Depends(require_permission(Permission.USERS_UPDATE))],
):
    return await service.set_status(actor, user_id, data.is_active)
