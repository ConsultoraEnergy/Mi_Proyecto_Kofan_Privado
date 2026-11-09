from fastapi import BackgroundTasks

from backend.app.core.errors import Forbidden, NotFound, Unauthorized, ValidationFailed
from backend.app.core.permissions import Permission, Role, has_permission, permissions_for
from backend.app.core.security import hash_password, verify_password
from backend.app.core.time import utcnow
from backend.app.db.utils import page_params, parse_object_id
from backend.app.modules.audit import service as audit
from backend.app.modules.auth import tokens
from backend.app.modules.notifications import service as notifications
from backend.app.modules.notifications.email import send_email
from backend.app.modules.users import repository
from backend.app.modules.users.schemas import (
    ChangePasswordIn,
    RegisterIn,
    UserCreateByStaff,
    UserOut,
    UserPage,
    UserUpdateByStaff,
    UserUpdateMe,
)


def to_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        email_verified=doc.get("email_verified", False),
        full_name=doc["full_name"],
        person_type=doc.get("person_type"),
        document_type=doc.get("document_type"),
        document_number=doc.get("document_number"),
        phone=doc.get("phone"),
        country=doc.get("country"),
        city=doc.get("city"),
        role=doc["role"],
        is_active=doc.get("is_active", True),
        permissions=sorted(p.value for p in permissions_for(doc["role"])),
        created_at=doc["created_at"],
    )


async def get_active_user(user_id: str) -> dict:
    """Usuario activo dueño de un token; Unauthorized si no existe o está suspendido (5.9)."""
    oid = parse_object_id(user_id)
    user = await repository.get_by_id(oid) if oid else None
    if user is None or not user.get("is_active", True):
        raise Unauthorized("Sesión inválida o expirada. Inicia sesión de nuevo.")
    return user


async def _get_or_404(user_id: str) -> dict:
    oid = parse_object_id(user_id)
    user = await repository.get_by_id(oid) if oid else None
    if user is None:
        raise NotFound("Usuario no encontrado.")
    return user


async def _send_verification(user: dict, background: BackgroundTasks) -> None:
    raw = await tokens.create_email_token(user["_id"], tokens.EmailTokenPurpose.VERIFY_EMAIL)
    background.add_task(send_email, notifications.verification_email(user["email"], user["full_name"], raw))


# ---------------------------------------------------------------------------
# Registro público y autoservicio
# ---------------------------------------------------------------------------

async def register(data: RegisterIn, background: BackgroundTasks) -> UserOut:
    if data.accept_privacy_policy is not True:
        raise ValidationFailed("Debes aceptar la política de tratamiento de datos personales.")
    fields = data.model_dump(mode="json", exclude={"password", "accept_privacy_policy"})
    user = await repository.insert({
        **fields,
        "password_hash": hash_password(data.password),
        "role": Role.CLIENT.value,
        "is_active": True,
        "email_verified": False,
        "privacy_policy_accepted_at": utcnow(),
    })
    await _send_verification(user, background)
    return to_out(user)


async def resend_verification(user: dict, background: BackgroundTasks) -> None:
    if user.get("email_verified"):
        raise ValidationFailed("Tu correo ya está verificado.")
    await _send_verification(user, background)


async def update_me(user: dict, data: UserUpdateMe) -> UserOut:
    fields = data.model_dump(mode="json", exclude_unset=True)
    if not fields:
        raise ValidationFailed("No enviaste datos para actualizar.")
    return to_out(await repository.update(user["_id"], fields))


async def change_password(user: dict, data: ChangePasswordIn) -> None:
    if not verify_password(data.current_password, user.get("password_hash")):
        raise ValidationFailed("La contraseña actual no es correcta.")
    await repository.update(user["_id"], {"password_hash": hash_password(data.new_password)})
    await tokens.revoke_all_for_user(user["_id"])


async def deactivate_me(user: dict) -> None:
    await repository.update(user["_id"], {"is_active": False})
    await tokens.revoke_all_for_user(user["_id"])


# ---------------------------------------------------------------------------
# Gestión por el personal (admin / recepción)
# ---------------------------------------------------------------------------

def _require_staff_management(actor: dict, *, target_role: str | None = None) -> None:
    """Solo quien tiene users:manage_staff puede crear/editar personal o asignar roles de personal."""
    if target_role in (None, Role.CLIENT.value):
        return
    if not has_permission(actor["role"], Permission.USERS_MANAGE_STAFF):
        raise Forbidden("No tienes permiso para gestionar cuentas del personal.")


async def list_users(query_text: str | None, role: str | None, page: int, limit: int) -> UserPage:
    skip, limit = page_params(page, limit)
    docs, total = await repository.search(query_text, role, skip, limit)
    return UserPage(items=[to_out(d) for d in docs], total=total, page=page, limit=limit)


async def get_user(user_id: str) -> UserOut:
    return to_out(await _get_or_404(user_id))


async def create_by_staff(actor: dict, data: UserCreateByStaff, background: BackgroundTasks) -> UserOut:
    _require_staff_management(actor, target_role=data.role.value)
    # 5.10: sin contraseña por defecto. El usuario recibe un enlace de un solo uso para definirla.
    user = await repository.insert({
        **data.model_dump(mode="json"),
        "role": data.role.value,
        "password_hash": None,
        "is_active": True,
        "email_verified": False,
        "created_by": actor["email"],
    })
    raw = await tokens.create_email_token(user["_id"], tokens.EmailTokenPurpose.SET_PASSWORD)
    background.add_task(send_email, notifications.set_password_email(user["email"], user["full_name"], raw))
    await audit.record("user", user["_id"], "create", actor["email"], label=user["email"])
    return to_out(user)


async def update_by_staff(actor: dict, user_id: str, data: UserUpdateByStaff) -> UserOut:
    target = await _get_or_404(user_id)
    fields = data.model_dump(mode="json", exclude_unset=True)
    if not fields:
        raise ValidationFailed("No hay datos para actualizar.")

    _require_staff_management(actor, target_role=target["role"])
    role_changed = "role" in fields and fields["role"] != target["role"]
    if role_changed:
        _require_staff_management(actor, target_role=Role.ADMIN.value)
        if target["_id"] == actor["_id"]:
            raise Forbidden("No puedes cambiar tu propio rol.")

    updated = await repository.update(target["_id"], fields)
    await audit.record("user", target["_id"], "update", actor["email"], label=target["email"],
                       changes=audit.diff(target, fields))
    if role_changed:
        await tokens.revoke_all_for_user(target["_id"])  # los permisos cambian: nueva sesión
    return to_out(updated)


async def set_status(actor: dict, user_id: str, is_active: bool) -> UserOut:
    target = await _get_or_404(user_id)
    if target["_id"] == actor["_id"]:
        raise Forbidden("No puedes suspender tu propia cuenta.")
    _require_staff_management(actor, target_role=target["role"])
    updated = await repository.update(target["_id"], {"is_active": is_active})
    if not is_active:
        await tokens.revoke_all_for_user(target["_id"])
    await audit.record("user", target["_id"], "activate" if is_active else "suspend", actor["email"],
                       label=target["email"])
    return to_out(updated)
