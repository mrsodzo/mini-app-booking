from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models import Service, TimeSlot, ServiceType, Admin
from bot.config import settings
from datetime import datetime, timedelta
import json


SERVICES = [
    {
        "name": "Стрижка мужская",
        "description": "Классическая мужская стрижка с укладкой",
        "duration_minutes": 30,
        "price": 1500,
        "service_type": ServiceType.HAIRCUT,
    },
    {
        "name": "Стрижка бороды",
        "description": "Формирование и стрижка бороды",
        "duration_minutes": 20,
        "price": 800,
        "service_type": ServiceType.BEARD,
    },
    {
        "name": "Окрашивание волос",
        "description": "Полное окрашивание волос профессиональными красками",
        "duration_minutes": 90,
        "price": 4500,
        "service_type": ServiceType.COLORING,
    },
    {
        "name": "Укладка волос",
        "description": "Укладка волос феном/прибором",
        "duration_minutes": 30,
        "price": 1000,
        "service_type": ServiceType.STYLING,
    },
    {
        "name": "Комплекс: стрижка + борода",
        "description": "Мужская стрижка и формирование бороды",
        "duration_minutes": 45,
        "price": 2000,
        "service_type": ServiceType.HAIRCUT,
    },
]


TIME_SLOTS = [
    "10:00",
    "12:00",
    "14:00",
    "16:00",
    "18:00",
]


async def init_default_data(session: AsyncSession):
    # Check if services already exist
    result = await session.execute(text("SELECT COUNT(*) FROM services"))
    if result.scalar() > 0:
        return
    
    for service_data in SERVICES:
        service = Service(**service_data)
        session.add(service)
    
    await session.flush()
    
    services = await session.execute(
        text("SELECT id FROM services WHERE is_active = 1")
    )
    service_ids = [row[0] for row in services.fetchall()]
    
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create slots for 30 days to cover any date user might select
    for service_id in service_ids:
        for day_offset in range(30):
            current_date = base_date + timedelta(days=day_offset)
            for time_str in TIME_SLOTS:
                hour, minute = map(int, time_str.split(":"))
                start_time = current_date.replace(hour=hour, minute=minute)
                end_time = start_time + timedelta(minutes=30)
                
                time_slot = TimeSlot(
                    service_id=service_id,
                    date=current_date,
                    start_time=time_str,
                    end_time=end_time.strftime("%H:%M"),
                    is_available=1,
                    max_bookings=1,
                    current_bookings=0,
                )
                session.add(time_slot)
    
    await session.commit()


async def ensure_admin(session: AsyncSession):
    """Ensure admin exists"""
    if not settings.admin_chat_id:
        return
    result = await session.execute(
        text("SELECT id FROM admins WHERE telegram_id = :tid"),
        {"tid": settings.admin_chat_id}
    )
    if not result.scalar_one_or_none():
        admin = Admin(
            telegram_id=settings.admin_chat_id,
            username="admin",
            is_superadmin=1,
        )
        session.add(admin)
        await session.commit()


async def ensure_time_slots(session: AsyncSession):
    """Ensure time slots exist for the next 30 days"""
    services = await session.execute(
        text("SELECT id FROM services WHERE is_active = 1")
    )
    service_ids = [row[0] for row in services.fetchall()]
    
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for service_id in service_ids:
        for day_offset in range(30):
            current_date = base_date + timedelta(days=day_offset)
            for time_str in TIME_SLOTS:
                existing = await session.execute(
                    text("SELECT id FROM time_slots WHERE service_id = :sid AND date = :dt AND start_time = :st"),
                    {"sid": service_id, "dt": current_date, "st": time_str}
                )
                if existing.scalar_one_or_none():
                    continue
                    
                hour, minute = map(int, time_str.split(":"))
                start_time = current_date.replace(hour=hour, minute=minute)
                end_time = start_time + timedelta(minutes=30)
                
                time_slot = TimeSlot(
                    service_id=service_id,
                    date=current_date,
                    start_time=time_str,
                    end_time=end_time.strftime("%H:%M"),
                    is_available=1,
                    max_bookings=1,
                    current_bookings=0,
                )
                session.add(time_slot)
    
    await session.commit()