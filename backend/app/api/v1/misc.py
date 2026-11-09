"""Routers pequeños: folios, galería, ajustes del sitio, dashboard, notificaciones y auditoría."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from backend.app.api.deps import CurrentUser, require_permission
from backend.app.core.permissions import Permission
from backend.app.modules.audit import service as audit
from backend.app.modules.cms import service as cms
from backend.app.modules.dashboard import service as dashboard
from backend.app.modules.folios import service as folios
from backend.app.modules.notifications import service as notifications

# --- Folios ---
folios_router = APIRouter(prefix="/folios", tags=["folios"])
FolioReader = Annotated[dict, Depends(require_permission(Permission.FOLIOS_READ))]
FolioWriter = Annotated[dict, Depends(require_permission(Permission.FOLIOS_WRITE))]


@folios_router.get("/by-booking/{booking_id}", response_model=folios.FolioOut)
async def get_folio_by_booking(booking_id: str, _: FolioReader):
    return await folios.get_by_booking(booking_id)


@folios_router.post("/{folio_id}/charges", response_model=folios.FolioOut, status_code=status.HTTP_201_CREATED)
async def add_charge(folio_id: str, data: folios.ChargeIn, actor: FolioWriter):
    return await folios.add_charge(folio_id, data, actor["email"])


@folios_router.delete("/{folio_id}/charges/{charge_id}", response_model=folios.FolioOut)
async def remove_charge(folio_id: str, charge_id: str, actor: FolioWriter):
    return await folios.remove_charge(folio_id, charge_id, actor["email"])


# --- Galería ---
gallery_router = APIRouter(prefix="/gallery", tags=["gallery"])
GalleryWriter = Annotated[dict, Depends(require_permission(Permission.GALLERY_WRITE))]


@gallery_router.get("", response_model=list[cms.GalleryImageOut])
async def list_gallery(
    category: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=60, ge=1, le=200),
):
    return await cms.list_gallery(category, page, limit)


@gallery_router.post("", response_model=cms.GalleryImageOut, status_code=status.HTTP_201_CREATED)
async def upload_gallery_image(
    actor: GalleryWriter,
    file: UploadFile = File(...),
    category: str = Form("general", max_length=40),
    title: str = Form("", max_length=120),
):
    return await cms.upload_gallery_image(actor, file, category, title)


@gallery_router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gallery_image(image_id: str, actor: GalleryWriter):
    await cms.delete_gallery_image(actor, image_id)


# --- Ajustes del sitio ---
settings_router = APIRouter(prefix="/settings", tags=["settings"])
SettingsWriter = Annotated[dict, Depends(require_permission(Permission.SETTINGS_WRITE))]


@settings_router.get("", response_model=cms.SiteSettingsOut)
async def get_site_settings():
    return await cms.get_site_settings()


@settings_router.put("", response_model=cms.SiteSettingsOut)
async def update_site_settings(data: cms.SiteSettingsIn, actor: SettingsWriter):
    return await cms.update_site_settings(actor, data)


@settings_router.post("/logo", response_model=cms.SiteSettingsOut)
async def upload_logo(actor: SettingsWriter, file: UploadFile = File(...)):
    return await cms.update_logo(actor, file)


# --- Dashboard ---
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("", response_model=dashboard.DashboardOut)
async def get_dashboard(_: Annotated[dict, Depends(require_permission(Permission.DASHBOARD_READ))]):
    return await dashboard.get_dashboard()


# --- Notificaciones ---
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notifications_router.get("", response_model=list[notifications.NotificationOut])
async def my_notifications(user: CurrentUser):
    return await notifications.list_for_user(user["_id"])


@notifications_router.post("/read-all")
async def mark_all_read(user: CurrentUser) -> dict:
    return {"updated": await notifications.mark_all_read(user["_id"])}


# --- Auditoría ---
audit_router = APIRouter(prefix="/audit-logs", tags=["audit"])


@audit_router.get("", response_model=audit.AuditPage)
async def list_audit_logs(
    _: Annotated[dict, Depends(require_permission(Permission.AUDIT_READ))],
    entity: str | None = Query(default=None, max_length=40),
    entity_id: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    return await audit.list_logs(entity, entity_id, page, limit)
