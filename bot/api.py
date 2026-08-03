from aiohttp import web
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from bot.database import async_session_maker
from bot.models import Service, TimeSlot


async def get_services(request: web.Request) -> web.Response:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Service).where(Service.is_active == 1)
        )
        services = result.scalars().all()
        
        data = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "duration_minutes": s.duration_minutes,
                "price": s.price,
                "service_type": s.service_type.value,
            }
            for s in services
        ]
        return web.json_response({"services": data}, headers={'Access-Control-Allow-Origin': '*'})


async def get_available_dates(request: web.Request) -> web.Response:
    service_id = int(request.match_info["service_id"])
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id, Service.is_active == 1)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            return web.json_response({"error": "Service not found"}, status=404)
        
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dates = []
        
        for day_offset in range(30):
            current_date = base_date + timedelta(days=day_offset)
            
            result = await session.execute(
                select(TimeSlot).where(
                    and_(
                        TimeSlot.service_id == service_id,
                        TimeSlot.date == current_date,
                        TimeSlot.is_available == 1,
                        TimeSlot.current_bookings < TimeSlot.max_bookings,
                    )
                )
            )
            slots = result.scalars().all()
            
            if slots:
                dates.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "display": current_date.strftime("%d.%m.%Y"),
                    "weekday": current_date.strftime("%a"),
                    "has_slots": True,
                })
            else:
                dates.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "display": current_date.strftime("%d.%m.%Y"),
                    "weekday": current_date.strftime("%a"),
                    "has_slots": False,
                })
        
        return web.json_response({"dates": dates}, headers={'Access-Control-Allow-Origin': '*'})


async def get_available_slots(request: web.Request) -> web.Response:
    service_id = int(request.match_info["service_id"])
    date_str = request.match_info["date"]
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return web.json_response({"error": "Invalid date format"}, status=400)
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(TimeSlot).where(
                and_(
                    TimeSlot.service_id == service_id,
                    TimeSlot.date == target_date,
                    TimeSlot.is_available == 1,
                    TimeSlot.current_bookings < TimeSlot.max_bookings,
                )
            ).order_by(TimeSlot.start_time)
        )
        slots = result.scalars().all()
        
        # Deduplicate by start_time (keep first available)
        seen_times = set()
        unique_slots = []
        for s in slots:
            if s.start_time not in seen_times:
                seen_times.add(s.start_time)
                unique_slots.append(s)
        
        data = [
            {
                "id": s.id,
                "start_time": s.start_time,
                "end_time": s.end_time,
            }
            for s in unique_slots
        ]
        return web.json_response({"slots": data}, headers={'Access-Control-Allow-Origin': '*'})


async def get_service_info(request: web.Request) -> web.Response:
    service_id = int(request.match_info["service_id"])
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Service).where(Service.id == service_id, Service.is_active == 1)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            return web.json_response({"error": "Service not found"}, status=404)
        
        data = {
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "duration_minutes": service.duration_minutes,
            "price": service.price,
            "service_type": service.service_type.value,
        }
        return web.json_response(data, headers={'Access-Control-Allow-Origin': '*'})


def setup_routes(app: web.Application):
    app.router.add_get("/api/services", get_services)
    app.router.add_get("/api/services/{service_id}", get_service_info)
    app.router.add_get("/api/services/{service_id}/dates", get_available_dates)
    app.router.add_get("/api/services/{service_id}/dates/{date}/slots", get_available_slots)
    # CORS preflight
    app.router.add_options("/api/{path:.*}", lambda request: web.Response(headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }))


async def create_app() -> web.Application:
    app = web.Application()
    setup_routes(app)
    return app