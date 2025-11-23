import logging
from typing import List, Dict
import os
from dotenv import load_dotenv
import asyncio
import telegram
from telegram.error import TelegramError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_bot_instance = None


def get_telegram_bot():
    """Получает экземпляр Telegram бота (singleton)"""
    global _bot_instance
    if _bot_instance is None:
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")
        _bot_instance = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        logger.info("Telegram Bot инициализирован")
    return _bot_instance


async def send_telegram_message_async(chat_id: str, message: str) -> bool:
    """Асинхронная отправка сообщения в Telegram"""
    try:
        bot = get_telegram_bot()
        await bot.send_message(
            chat_id=int(chat_id),
            text=message,
            parse_mode='HTML'
        )
        logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
        return True
    except TelegramError as e:
        logger.error(f"❌ Telegram ошибка для чата {chat_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False


def format_slot_telegram_message(slot_data: dict, notification_type: str = "new") -> str:
    """Формирует текстовое сообщение для Telegram"""
    headers = {
        "new": "🆕 <b>Новое занятие добавлено!</b>",
        "status_changed": "🔄 <b>Изменение статуса занятия</b>",
        "reminder": "⏰ <b>Напоминание о занятии</b>"
    }
    header = headers.get(notification_type, "📌 <b>Уведомление о занятии</b>")

    status_emoji = {
        "scheduled": "📅",
        "in_progress": "▶️",
        "completed": "✅",
        "cancelled": "❌"
    }

    status = slot_data.get('status', 'scheduled')
    status_text = f"{status_emoji.get(status, '📌')} {status}"

    message = f"""{header}

📚 <b>Курс:</b> {slot_data.get('course_name', 'Не указан')}
⏰ <b>Начало:</b> {slot_data.get('start_time', 'Не указано')}
⏱ <b>Конец:</b> {slot_data.get('end_time', 'Не указано')}
📍 <b>Место:</b> {slot_data.get('location', 'Не указано')}
🏷 <b>Статус:</b> {status_text}
"""

    if notification_type == "status_changed" and slot_data.get('old_status'):
        old_status = slot_data['old_status']
        message += f"\n🔀 <b>Предыдущий статус:</b> {status_emoji.get(old_status, '📌')} {old_status}"

    return message


async def notify_participants_telegram_async(
        participants: List[dict],
        slot_data: dict,
        notification_type: str = "new"
) -> Dict[str, any]:
    """
    АСИНХРОННАЯ отправка уведомлений в Telegram
    Работает в существующем event loop FastAPI
    """
    logger.info(f"📤 Отправка уведомлений ({notification_type}) для {len(participants)} участников")
    message = format_slot_telegram_message(slot_data, notification_type)

    success_count = 0
    failed_count = 0
    failed_chat_ids = []

    # Создаём список задач для параллельной отправки
    tasks = []
    chat_ids = []

    for participant in participants:
        chat_id = participant.get('telegram_chat_id')
        if not chat_id:
            logger.warning(f"⚠️ Участник без telegram_chat_id: {participant.get('id')}")
            continue

        logger.info(f"📨 Добавление в очередь для ID={participant.get('id')} (chat_id={chat_id})")
        tasks.append(send_telegram_message_async(str(chat_id), message))
        chat_ids.append(chat_id)

    # Отправляем все сообщения параллельно
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Ошибка для chat_id {chat_ids[i]}: {result}")
                failed_count += 1
                failed_chat_ids.append(chat_ids[i])
            elif result:
                success_count += 1
            else:
                failed_count += 1
                failed_chat_ids.append(chat_ids[i])

    logger.info(f"✅ Уведомления отправлены. Успешно: {success_count}, Ошибки: {failed_count}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_chat_ids": failed_chat_ids
    }


# СИНХРОННЫЕ ОБЁРТКИ для обратной совместимости
def notify_participants_telegram(participants: List[dict], slot_data: dict, notification_type: str = "new") -> Dict[
    str, any]:
    """
    Синхронная обёртка - НЕ ИСПОЛЬЗОВАТЬ в FastAPI!
    Оставлена только для обратной совместимости
    """
    logger.warning("⚠️ Используется синхронная обёртка! Используйте notify_participants_telegram_async")
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(notify_participants_telegram_async(participants, slot_data, notification_type))
    except RuntimeError:
        # Если event loop уже запущен, создаём задачу
        return asyncio.create_task(notify_participants_telegram_async(participants, slot_data, notification_type))


async def notify_slot_created(participants: List[dict], slot_data: dict) -> Dict[str, any]:
    """Асинхронное уведомление о создании нового слота"""
    return await notify_participants_telegram_async(participants, slot_data, notification_type="new")


async def notify_slot_status_changed(participants: List[dict], slot_data: dict, old_status: str) -> Dict[str, any]:
    """Асинхронное уведомление об изменении статуса слота"""
    slot_data['old_status'] = old_status
    return await notify_participants_telegram_async(participants, slot_data, notification_type="status_changed")


# Для обратной совместимости
def notify_users(participants: List[dict], slot_data: dict, notification_type: str = "new") -> Dict[str, any]:
    """Устаревшая функция - используйте notify_slot_created или notify_slot_status_changed"""
    return notify_participants_telegram(participants, slot_data, notification_type)
