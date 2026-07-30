import json
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, WebAppData
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import get_session
from bot.models import User, ContestEntry
from bot.keyboards import get_back_to_start_keyboard, get_start_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        if action == "contest":
            await process_contest(message, data)
        elif action == "booking":
            pass
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


async def process_contest(message: Message, data: dict):
    answer = data.get("answer", "").strip()
    
    if not answer:
        await message.answer(
            "❌ Введите ответ на загадку.",
            reply_markup=get_back_to_start_keyboard(),
        )
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
            await message.answer(
                "❌ Вы уже участвуете в конкурсе!",
                reply_markup=get_back_to_start_keyboard(),
            )
            return
        
        entry = ContestEntry(
            user_id=user.id,
            answer=answer,
        )
        session.add(entry)
        await session.commit()
    
    await message.answer(
        "✅ <b>Спасибо за участие!</b>\n\n"
        "Ваш ответ принят. Результаты конкурса объявим завтра. "
        "Удачи! 🍀",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML",
    )
    
    try:
        await message.bot.send_message(
            settings.admin_chat_id,
            f"🎁 <b>Новый участник конкурса</b>\n\n"
            f"👤 {message.from_user.first_name} "
            f"(@{message.from_user.username or 'нет username'})\n"
            f"💬 Ответ: {answer}",
            parse_mode="HTML",
        )
    except Exception:
        pass