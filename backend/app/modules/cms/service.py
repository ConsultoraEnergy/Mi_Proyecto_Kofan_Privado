"""Contenido del sitio editable desde el panel: ajustes generales (marca, contacto, pago) y galería."""

import re
from datetime import datetime
from typing import Annotated

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.app.core.errors import NotFound, ValidationFailed
from backend.app.core.settings import get_settings
from backend.app.core.time import utcnow
from backend.app.db.client import get_db
from backend.app.db.utils import page_params, require_object_id
from backend.app.modules.audit import service as audit
from backend.app.modules.media import storage

SETTINGS_ID = "site"

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]
Time = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


class SiteSettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hotel_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
    tagline: Text = ""
    # Responsable del tratamiento de datos (Ley 1581): aparecen en la política de datos.
    legal_name: Text = ""
    tax_id: Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)] = ""
    contact_email: Text = ""
    phone: Text = ""
    whatsapp_number: Text = ""
    address: Text = ""
    city: Text = ""
    country: Text = "Colombia"
    check_in_time: Time = "15:00"
    check_out_time: Time = "11:00"
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] = "COP"
    tax_percentage: float = Field(default=0, ge=0, le=100)
    social_facebook: Text = ""
    social_instagram: Text = ""
    social_tiktok: Text = ""
    # Sin pasarela de pago: datos para que el huésped transfiera el anticipo.
    payment_instructions: LongText = ""
    about_description: LongText = ""
    mission: LongText = ""
    vision: LongText = ""


class SiteSettingsOut(SiteSettingsIn):
    model_config = ConfigDict(extra="ignore")
    logo_url: str = ""
    deposit_percent: int


def _defaults() -> dict:
    settings = get_settings()
    return {
        **SiteSettingsIn(hotel_name=settings.hotel_name, currency=settings.currency).model_dump(),
        "logo_url": "",
    }


async def get_site_settings() -> SiteSettingsOut:
    doc = await get_db().settings.find_one({"_id": SETTINGS_ID}) or {}
    return SiteSettingsOut(**{**_defaults(), **doc, "deposit_percent": get_settings().deposit_percent})


async def ensure_defaults() -> None:
    """Crea el documento de ajustes con valores iniciales si no existe (no pisa cambios)."""
    await get_db().settings.update_one(
        {"_id": SETTINGS_ID}, {"$setOnInsert": {**_defaults(), "created_at": utcnow()}}, upsert=True
    )


async def update_site_settings(actor: dict, data: SiteSettingsIn) -> SiteSettingsOut:
    before = await get_db().settings.find_one({"_id": SETTINGS_ID}) or {}
    fields = data.model_dump()
    await get_db().settings.update_one(
        {"_id": SETTINGS_ID}, {"$set": {**fields, "updated_at": utcnow(), "updated_by": actor["email"]}}, upsert=True
    )
    await audit.record("settings", SETTINGS_ID, "update", actor["email"], changes=audit.diff(before, fields))
    return await get_site_settings()


async def update_logo(actor: dict, file: UploadFile) -> SiteSettingsOut:
    url = await storage.save_public_image(file)
    before = await get_db().settings.find_one_and_update(
        {"_id": SETTINGS_ID},
        {"$set": {"logo_url": url, "updated_at": utcnow(), "updated_by": actor["email"]}},
        upsert=True,
    )
    if before and before.get("logo_url"):
        await storage.delete_public_file(before["logo_url"])
    return await get_site_settings()


# ---------------------------------------------------------------------------
# Galería
# ---------------------------------------------------------------------------


class GalleryImageOut(BaseModel):
    id: str
    url: str
    title: str
    category: str
    created_at: datetime


def _gallery_out(doc: dict) -> GalleryImageOut:
    return GalleryImageOut(
        id=str(doc["_id"]),
        url=doc["url"],
        title=doc.get("title", ""),
        category=doc.get("category", "general"),
        created_at=doc["created_at"],
    )


async def list_gallery(category: str | None, page: int, limit: int) -> list[GalleryImageOut]:
    skip, limit = page_params(page, limit, maximum=200)
    query = {"category": category.strip().lower()} if category and category != "all" else {}
    docs = await get_db().gallery.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [_gallery_out(d) for d in docs]


_CATEGORY_RE = re.compile(r"^[a-z0-9-]{2,40}$")


async def upload_gallery_image(actor: dict, file: UploadFile, category: str, title: str) -> GalleryImageOut:
    category = (category or "general").strip().lower()
    if not _CATEGORY_RE.match(category):
        raise ValidationFailed("Categoría no válida: usa letras minúsculas, números o guiones.")
    title = (title or "").strip()[:120]
    url = await storage.save_public_image(file)
    doc = {"url": url, "title": title, "category": category, "uploaded_by": actor["email"], "created_at": utcnow()}
    result = await get_db().gallery.insert_one(doc)
    return _gallery_out({**doc, "_id": result.inserted_id})


async def delete_gallery_image(actor: dict, image_id: str) -> None:
    doc = await get_db().gallery.find_one_and_delete({"_id": require_object_id(image_id, "Imagen")})
    if not doc:
        raise NotFound("Imagen no encontrada.")
    await storage.delete_public_file(doc["url"])
    await audit.record("gallery", doc["_id"], "delete", actor["email"], label=doc.get("title"))
