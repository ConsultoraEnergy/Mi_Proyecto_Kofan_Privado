"""
Métricas del panel. La ocupación se DERIVA de las noches reservadas (6.5), no de una bandera manual.
Fase 3: cachear (Redis 60 s) o materializar.
"""
from datetime import date, datetime, timedelta

from pydantic import BaseModel

from backend.app.core.time import date_to_datetime, hotel_today, start_of_month_utc
from backend.app.db.client import get_db
from backend.app.modules.bookings.state_machine import BookingStatus
from backend.app.modules.folios import service as folios


class DashboardStats(BaseModel):
    month_revenue: float
    confirmed_bookings: int
    pending_verification: int
    in_house_guests: int
    arrivals_today: int
    departures_today: int
    occupancy_percent: int
    occupied_rooms: int
    sellable_rooms: int


class PopularRoom(BaseModel):
    room_id: str
    name: str
    bookings: int


class RecentActivity(BaseModel):
    booking_id: str
    code: str
    guest_name: str
    room_name: str
    status: BookingStatus
    total_amount: float
    at: datetime


class DashboardOut(BaseModel):
    today: date
    stats: DashboardStats
    popular_rooms: list[PopularRoom]
    recent_activity: list[RecentActivity]


async def get_dashboard() -> DashboardOut:
    db = get_db()
    today = hotel_today()
    today_dt = date_to_datetime(today)

    sellable_rooms = await db.rooms.count_documents({"is_active": True, "operational_status": {"$ne": "out_of_service"}})
    occupied_rooms = len(await db.room_nights.distinct("room_id", {"night": today_dt}))

    in_house = await (await db.bookings.aggregate([
        {"$match": {"status": BookingStatus.CHECKED_IN.value}},
        {"$group": {"_id": None, "n": {"$sum": {"$add": [1, {"$size": {"$ifNull": ["$companions", []]}}]}}}},
    ])).to_list(1)

    stats = DashboardStats(
        month_revenue=await folios.revenue_since(start_of_month_utc(today)),
        confirmed_bookings=await db.bookings.count_documents({"status": BookingStatus.CONFIRMED.value}),
        pending_verification=await db.bookings.count_documents({"status": BookingStatus.PENDING_VERIFICATION.value}),
        in_house_guests=in_house[0]["n"] if in_house else 0,
        arrivals_today=await db.bookings.count_documents({"status": BookingStatus.CONFIRMED.value, "check_in": today_dt}),
        departures_today=await db.bookings.count_documents({"status": BookingStatus.CHECKED_IN.value, "check_out": today_dt}),
        occupancy_percent=round(occupied_rooms * 100 / sellable_rooms) if sellable_rooms else 0,
        occupied_rooms=occupied_rooms,
        sellable_rooms=sellable_rooms,
    )

    since = date_to_datetime(today - timedelta(days=90))
    popular = await (await db.bookings.aggregate([
        {"$match": {"created_at": {"$gte": since}, "status": {"$ne": BookingStatus.CANCELLED.value}}},
        {"$group": {"_id": "$room_id", "name": {"$first": "$room.name"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": 3},
    ])).to_list(3)

    recent = await db.bookings.find({}).sort("updated_at", -1).limit(5).to_list(5)

    return DashboardOut(
        today=today,
        stats=stats,
        popular_rooms=[PopularRoom(room_id=str(p["_id"]), name=p["name"], bookings=p["n"]) for p in popular],
        recent_activity=[
            RecentActivity(
                booking_id=str(b["_id"]), code=b["code"], guest_name=b["guest"]["full_name"],
                room_name=b["room"]["name"], status=b["status"], total_amount=b["total_amount"],
                at=b.get("updated_at") or b["created_at"],
            )
            for b in recent
        ],
    )
