from fastapi import APIRouter

from backend.app.api.v1 import auth, bookings, misc, rooms, users

api_router = APIRouter(prefix="/api/v1")

for router in (
    auth.router,
    users.router,
    rooms.router,
    bookings.router,
    misc.folios_router,
    misc.gallery_router,
    misc.settings_router,
    misc.dashboard_router,
    misc.notifications_router,
    misc.audit_router,
):
    api_router.include_router(router)
