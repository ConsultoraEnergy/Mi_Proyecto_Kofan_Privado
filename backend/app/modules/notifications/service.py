"""Notificaciones del panel (in-app) y plantillas de correo."""
from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel

from backend.app.core.settings import get_settings
from backend.app.core.time import utcnow
from backend.app.db.client import get_db
from backend.app.modules.notifications.email import Email


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str
    theme: str
    icon: str
    read: bool
    created_at: datetime


async def notify_user(user_id: ObjectId | str, title: str, message: str, theme: str = "primary",
                      icon: str = "bi-info-circle-fill") -> None:
    await get_db().notifications.insert_one({
        "user_id": ObjectId(str(user_id)),
        "title": title,
        "message": message,
        "theme": theme,
        "icon": icon,
        "read": False,
        "created_at": utcnow(),
    })


async def list_for_user(user_id: ObjectId, limit: int = 30) -> list[NotificationOut]:
    docs = await (
        get_db().notifications.find({"user_id": user_id}).sort("created_at", -1).limit(limit).to_list(limit)
    )
    return [
        NotificationOut(
            id=str(d["_id"]), title=d["title"], message=d["message"], theme=d.get("theme", "primary"),
            icon=d.get("icon", "bi-bell"), read=d.get("read", False), created_at=d["created_at"],
        )
        for d in docs
    ]


async def mark_all_read(user_id: ObjectId) -> int:
    result = await get_db().notifications.update_many({"user_id": user_id, "read": False}, {"$set": {"read": True}})
    return result.modified_count


# ---------------------------------------------------------------------------
# Plantillas de correo
# ---------------------------------------------------------------------------

def _link(path: str, token: str) -> str:
    return f"{get_settings().frontend_url}{path}?token={token}"


def verification_email(to: str, full_name: str, token: str) -> Email:
    hotel = get_settings().hotel_name
    link = _link("/auth/verify-email", token)
    return Email(
        to=to,
        subject=f"Confirma tu correo en {hotel}",
        text=(
            f"Hola {full_name},\n\nConfirma tu correo para activar tu cuenta en {hotel}:\n{link}\n\n"
            f"El enlace vence en {get_settings().email_verification_expire_hours} horas.\n"
            "Si no creaste esta cuenta, ignora este mensaje."
        ),
    )


def password_reset_email(to: str, full_name: str, token: str) -> Email:
    hotel = get_settings().hotel_name
    link = _link("/auth/reset-password", token)
    return Email(
        to=to,
        subject=f"Restablece tu contraseña de {hotel}",
        text=(
            f"Hola {full_name},\n\nPara crear una nueva contraseña entra a:\n{link}\n\n"
            f"El enlace vence en {get_settings().password_reset_expire_minutes} minutos y solo se puede usar una vez.\n"
            "Si no lo solicitaste, ignora este mensaje: tu contraseña no cambiará."
        ),
    )


def set_password_email(to: str, full_name: str, token: str) -> Email:
    hotel = get_settings().hotel_name
    link = _link("/auth/reset-password", token)
    return Email(
        to=to,
        subject=f"Activa tu cuenta de {hotel}",
        text=(
            f"Hola {full_name},\n\nEl equipo de {hotel} creó una cuenta para ti. "
            f"Define tu contraseña aquí:\n{link}\n\n"
            f"El enlace vence en {get_settings().set_password_expire_hours} horas."
        ),
    )
