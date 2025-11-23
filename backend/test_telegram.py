import sys
import os
import asyncio

# Добавляем путь к родительской директории для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifications import send_telegram_message, format_slot_telegram_message
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


async def test_telegram_bot():
    """
    Тестирует подключение к Telegram Bot и отправку тестового сообщения
    """
    print("=== Тест Telegram Bot для уведомлений о слотах ===\n")

    # Проверяем наличие необходимых переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен в .env файле")
        print("\nУбедитесь, что в .env файле есть:")
        print("TELEGRAM_BOT_TOKEN=your-bot-token-here")
        return

    # Запрашиваем тестовый chat_id
    print("Для теста нужен Telegram Chat ID.")
    print("Узнать свой Chat ID можно написав @userinfobot в Telegram\n")

    test_chat_id = input("Введите ваш Telegram Chat ID: ").strip()

    if not test_chat_id or not test_chat_id.isdigit():
        print("❌ Некорректный Chat ID")
        return

    # Формируем тестовые данные для слота (новое занятие)
    test_slot_new = {
        "course_name": "Основы программирования",
        "start_time": "2025-11-23 10:00:00",
        "end_time": "2025-11-23 12:00:00",
        "location": "Аудитория 301",
        "status": "scheduled"
    }

    # Тест 1: Уведомление о новом занятии
    print(f"\n📤 Тест 1: Отправка уведомления о НОВОМ занятии...")
    message_new = format_slot_telegram_message(test_slot_new, notification_type="new")
    success = await send_telegram_message(test_chat_id, message_new)

    if success:
        print("✅ Уведомление о новом занятии успешно отправлено!")
    else:
        print("❌ Ошибка отправки уведомления о новом занятии")
        return

    # Задержка между сообщениями
    await asyncio.sleep(2)

    # Формируем тестовые данные для слота (изменение статуса)
    test_slot_changed = {
        "course_name": "Основы программирования",
        "start_time": "2025-11-23 10:00:00",
        "end_time": "2025-11-23 12:00:00",
        "location": "Аудитория 301",
        "status": "cancelled",
        "old_status": "scheduled"
    }

    # Тест 2: Уведомление об изменении статуса
    print(f"\n📤 Тест 2: Отправка уведомления об ИЗМЕНЕНИИ статуса...")
    message_changed = format_slot_telegram_message(test_slot_changed, notification_type="status_changed")
    success = await send_telegram_message(test_chat_id, message_changed)

    if success:
        print("✅ Уведомление об изменении статуса успешно отправлено!")
    else:
        print("❌ Ошибка отправки уведомления об изменении статуса")
        return

    print("\n✅ Все тесты пройдены успешно!")
    print(f"📱 Проверьте Telegram чат с ID: {test_chat_id}")


if __name__ == "__main__":
    # Запускаем асинхронный тест
    asyncio.run(test_telegram_bot())
