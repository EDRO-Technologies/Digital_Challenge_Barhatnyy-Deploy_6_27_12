import os
from dotenv import load_dotenv
import telegram
import asyncio

# Загружаем .env
load_dotenv()


async def test_bot():
    print("=" * 50)
    print("ПРОВЕРКА TELEGRAM BOT TOKEN")
    print("=" * 50)

    # Читаем токен из .env
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    print(f"\n1. Токен из .env:")
    if token:
        print(f"   ✅ Найден: {token[:10]}...{token[-5:]}")
        print(f"   Длина: {len(token)} символов")
    else:
        print("   ❌ НЕ НАЙДЕН!")
        print("\n   Решение:")
        print("   1. Создай файл backend/.env")
        print("   2. Добавь строку: TELEGRAM_BOT_TOKEN=твой_токен")
        return

    # Проверяем формат токена
    print(f"\n2. Формат токена:")
    if ":" in token:
        parts = token.split(":")
        print(f"   ✅ Формат правильный (id:hash)")
        print(f"   Bot ID: {parts[0]}")
    else:
        print("   ❌ НЕВЕРНЫЙ ФОРМАТ! Должен быть: 123456789:ABCdef...")
        return

    # Проверяем подключение к Telegram API
    print(f"\n3. Проверка подключения к Telegram API:")
    try:
        bot = telegram.Bot(token=token)
        bot_info = await bot.get_me()

        print(f"   ✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")
        print(f"   Имя бота: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   Bot ID: {bot_info.id}")

        print(f"\n✅ ВСЁ РАБОТАЕТ!")
        print(f"\nТеперь найди бота в Telegram:")
        print(f"   👉 @{bot_info.username}")
        print(f"\nИ напиши ему /start")

    except telegram.error.InvalidToken:
        print("   ❌ НЕВЕРНЫЙ ТОКЕН!")
        print("\n   Решение:")
        print("   1. Открой Telegram, найди @BotFather")
        print("   2. Напиши /mybots")
        print("   3. Выбери своего бота → API Token")
        print("   4. Скопируй ВЕСЬ токен в .env")

    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        print("\n   Возможные причины:")
        print("   1. Нет интернета")
        print("   2. Telegram заблокирован")
        print("   3. Бот удалён в BotFather")


if __name__ == "__main__":
    asyncio.run(test_bot())
