import json
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, WebAppData, InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import get_session
from bot.models import User, Booking, Service, TimeSlot, ContestEntry
from bot.keyboards.reply import get_back_to_start_keyboard, get_start_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def send_webapp_error(message: Message, error: str):
    """Send error response back to WebApp via answer_web_app_query"""
    try:
        webapp_response = {
            "ok": False,
            "error": error,
        }
        
        result = InlineQueryResultArticle(
            id="error_" + str(message.message_id),
            title="Ошибка",
            input_message_content=InputTextMessageContent(
                message_text=json.dumps(webapp_response),
            ),
        )
        await message.bot.answer_web_app_query(message.web_app_data.query_id, result)
    except Exception as e:
        logger.error(f"Failed to send webapp error: {e}")
    
    # Also send a visible message to user
    await message.answer(
        f"❌ {error}",
        reply_markup=get_back_to_start_keyboard(),
    )


async def process_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        if action == "booking":
            await process_booking(message, data)
        elif action == "contest":
            await process_contest(message, data)
        else:
            await message.answer(
                "❌ Неизвестное действие.",
                reply_markup=get_back_to_start_keyboard(),
            )
    except json.JSONDecodeError:
        await message.answer(
            "❌ Ошибка обработки данных.",
            reply_markup=get_back_to_start_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error processing webapp data: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_back_to_start_keyboard(),
        )


async def process_booking(message: Message, data: dict):
    service_id = data.get("service_id")
    time_slot_id = data.get("time_slot_id")
    client_name = data.get("client_name")
    client_phone = data.get("client_phone")
    notes = data.get("notes", "")
    
    if not all([service_id, time_slot_id, client_name, client_phone]):
        await send_webapp_error(message, "Не все данные заполнены.")
        return
    
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                phone=client_phone,
            )
            session.add(user)
            await session.flush()
        else:
            user.phone = client_phone
        
        result = await session.execute(
            select(Service).where(Service.id == service_id)
        )
        service = result.scalar_one_or_none()
        
        if not service:
            await send_webapp_error(message, "Услуга не найдена.")
            return
        
        result = await session.execute(
            select(TimeSlot).where(TimeSlot.id == time_slot_id)
        )
        time_slot = result.scalar_one_or_none()
        
        if not time_slot or time_slot.current_bookings >= time_slot.max_bookings:
            await send_webapp_error(message, "Это время уже занято. Выберите другое.")
            return
        
        time_slot.current_bookings += 1
        
        booking = Booking(
            user_id=user.id,
            service_id=service_id,
            time_slot_id=time_slot_id,
            client_name=client_name,
            client_phone=client_phone,
            notes=notes,
            status="new",
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        
        # Send response back to WebApp
        webapp_response = {
            "ok": True,
            "booking_id": booking.id,
            "service_name": service.name,
            "date": time_slot.date.strftime('%d.%m.%Y'),
            "time": time_slot.start_time,
            "client_name": client_name,
            "client_phone": client_phone,
            "price": service.price,
        }
        
        result = InlineQueryResultArticle(
            id=str(booking.id),
            title="Запись подтверждена",
            input_message_content=InputTextMessageContent(
                message_text=json.dumps(webapp_response),
            ),
        )
        await message.bot.answer_web_app_query(message.web_app_data.query_id, result)
        
        user_msg = (
            f"✅ <b>Вы успешно записались!</b>\n\n"
            f"📋 <b>Детали записи:</b>\n"
            f"💇‍♀️ Услуга: {service.name}\n"
            f"📅 Дата: {time_slot.date.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {time_slot.start_time}\n"
            f"👤 Имя: {client_name}\n"
            f"📱 Телефон: {client_phone}\n"
            f"💰 Цена: {service.price}₽\n\n"
            f"📝 Номер заказа: <b>#{booking.id}</b>\n"
            f"Мы свяжемся с вами для подтверждения."
        )
        
        await message.answer(user_msg, reply_markup=get_start_keyboard(), parse_mode="HTML")
        
        try:
            admin_msg = (
                f"🆕 <b>Новая запись #{booking.id}</b>\n\n"
                f"💇‍♀️ Услуга: {service.name}\n"
                f"📅 {time_slot.date.strftime('%d.%m.%Y')} в {time_slot.start_time}\n"
                f"👤 {client_name}\n"
                f"📱 {client_phone}\n"
                f"💰 {service.price}₽\n"
                f"👤 User: @{user.username or user.first_name}"
            )
            await message.bot.send_message(
                settings.admin_chat_id,
                admin_msg,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")


async def process_contest(message: Message, data: dict):
    answer = data.get("answer")
    
    if not answer:
        await send_webapp_error(message, "Ответ не указан.")
        return
    
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            session.add(user)
            await session.flush()
        
        result = await session.execute(
            select(ContestEntry).where(ContestEntry.user_id == user.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await send_webapp_error(message, "Вы уже участвовали в конкурсе!")
            return
        
        entry = ContestEntry(
            user_id=user.id,
            answer=answer,
        )
        session.add(entry)
        await session.commit()
        
        # Send response back to WebApp
        webapp_response = {
            "ok": True,
            "message": "Спасибо за участие!",
        }
        
        result = InlineQueryResultArticle(
            id="contest_" + str(user.id),
            title="Участие принято",
            input_message_content=InputTextMessageContent(
                message_text=json.dumps(webapp_response),
            ),
        )
        await message.bot.answer_web_app_query(message.web_app_data.query_id, result)
        
        await message.answer(
            "🎁 <b>Спасибо за участие!</b>\n\n"
            "Ваш ответ принят. Результаты конкурса объявят завтра.\n"
            "Удачи! 🍀",
            reply_markup=get_start_keyboard(),
            parse_mode="HTML",
        )
        
        try:
            admin_msg = (
                f"🎁 <b>Новый участник конкурса</b>\n\n"
                f"👤 @{user.username or user.first_name}\n"
                f"💬 Ответ: {answer}"
            )
            await message.bot.send_message(
                settings.admin_chat_id,
                admin_msg,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")


router.message.register(process_webapp_data, F.web_app_data)