import logging
import os
import sys
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime

# Добавляем путь для импорта database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота из .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./database.db")


def get_db_connection():
    """Получить подключение к базе данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение и показывает Chat ID
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Создаём интерактивные кнопки
    keyboard = [
        [InlineKeyboardButton("📋 Узнать мой Chat ID", callback_data='show_chat_id')],
        [InlineKeyboardButton("📅 Моё расписание", callback_data='my_schedule')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = f"""
👋 <b>Привет, {user.first_name}!</b>

Я бот системы <b>"Умное расписание СурГУ"</b>

🆔 <b>Твой Chat ID:</b> <code>{chat_id}</code>

📝 <b>Что я умею:</b>
• Показывать твой Chat ID для регистрации
• Отправлять уведомления о новых занятиях
• Сообщать об изменениях в расписании
• Показывать твоё расписание

<b>Для начала работы:</b>
1. Скопируй свой Chat ID (нажми на него)
2. Зарегистрируйся на сайте
3. Добавь Chat ID в профиль
4. Получай уведомления автоматически!
"""

    await update.message.reply_text(
        welcome_message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    logger.info(f"✅ Пользователь {user.first_name} ({user.username}) ID={chat_id} запустил бота")


async def my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /my_id
    Показывает Chat ID пользователя
    """
    chat_id = update.effective_chat.id
    user = update.effective_user

    message = f"""
🆔 <b>Твой Telegram Chat ID</b>

<code>{chat_id}</code>

<i>Нажми на число выше, чтобы скопировать</i>

📝 <b>Как использовать:</b>
1. Скопируй этот Chat ID
2. Зайди на сайт расписания
3. Добавь Chat ID в профиль участника
4. Готово! Уведомления будут приходить сюда

💡 <b>Совет:</b> Сохрани этот Chat ID — он не меняется и понадобится при регистрации на других курсах.
"""

    keyboard = [
        [InlineKeyboardButton("✅ Я добавил Chat ID", callback_data='confirm_registered')],
        [InlineKeyboardButton("❓ Где добавить Chat ID?", callback_data='where_add_id')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    logger.info(f"📋 Показан Chat ID для пользователя {user.first_name}: {chat_id}")


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /schedule
    Показывает расписание пользователя
    """
    chat_id = update.effective_chat.id
    user = update.effective_user

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ищем пользователя по telegram_id
        cursor.execute("""
            SELECT id, full_name, email FROM users 
            WHERE telegram_id = ?
        """, (str(chat_id),))

        user_data = cursor.fetchone()

        if not user_data:
            # Пользователь не зарегистрирован
            keyboard = [
                [InlineKeyboardButton("📋 Узнать мой Chat ID", callback_data='show_chat_id')],
                [InlineKeyboardButton("❓ Как зарегистрироваться?", callback_data='how_to_register')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "⚠️ <b>Ты ещё не зарегистрирован в системе</b>\n\n"
                "Чтобы получать расписание:\n"
                "1. Узнай свой Chat ID (кнопка ниже)\n"
                "2. Зарегистрируйся на сайте\n"
                "3. Добавь Chat ID в профиль\n"
                "4. Возвращайся сюда за расписанием!",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            conn.close()
            return

        user_id = user_data['id']
        user_name = user_data['full_name']

        # Получаем ближайшие занятия пользователя
        cursor.execute("""
            SELECT cs.id, cs.title, cs.date_time, cs.location, cs.instructor, cs.status, c.name as course_name
            FROM class_slots cs
            LEFT JOIN courses c ON cs.course_id = c.id
            INNER JOIN participants p ON p.class_slot_id = cs.id
            WHERE p.user_id = ?
            AND datetime(cs.date_time) >= datetime('now')
            ORDER BY cs.date_time
            LIMIT 10
        """, (user_id,))

        slots = cursor.fetchall()
        conn.close()

        if not slots:
            await update.message.reply_text(
                f"📅 <b>Привет, {user_name}!</b>\n\n"
                "У тебя пока нет предстоящих занятий.\n\n"
                "Как только появятся новые занятия, ты получишь уведомление! 🔔",
                parse_mode='HTML'
            )
            return

        # Формируем сообщение с расписанием
        schedule_text = f"📅 <b>Твоё расписание, {user_name}</b>\n\n"
        schedule_text += f"Найдено занятий: <b>{len(slots)}</b>\n\n"

        status_emoji = {
            "scheduled": "📅",
            "in_progress": "▶️",
            "completed": "✅",
            "cancelled": "❌"
        }

        for idx, slot in enumerate(slots, 1):
            status = slot['status'] or 'scheduled'
            emoji = status_emoji.get(status, '📌')

            schedule_text += f"<b>{idx}. {slot['title'] or 'Занятие'}</b> {emoji}\n"
            if slot['course_name']:
                schedule_text += f"   📚 Курс: {slot['course_name']}\n"
            schedule_text += f"   ⏰ {slot['date_time']}\n"
            if slot['location']:
                schedule_text += f"   📍 {slot['location']}\n"
            if slot['instructor']:
                schedule_text += f"   👨‍🏫 {slot['instructor']}\n"
            schedule_text += "\n"

        # Отправляем большое сообщение частями если нужно
        if len(schedule_text) > 4000:
            # Разбиваем на части
            parts = [schedule_text[i:i + 4000] for i in range(0, len(schedule_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(schedule_text, parse_mode='HTML')

        logger.info(f"📅 Показано расписание для {user_name} (ID={user_id}): {len(slots)} занятий")

    except Exception as e:
        logger.error(f"❌ Ошибка получения расписания: {e}")
        await update.message.reply_text(
            "⚠️ Произошла ошибка при загрузке расписания.\n"
            "Попробуй позже или обратись к администратору.",
            parse_mode='HTML'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help
    Показывает справку по использованию бота
    """
    help_text = """
📚 <b>Справка по боту "Умное расписание СурГУ"</b>

<b>📋 Доступные команды:</b>

/start - Начать работу с ботом
/my_id - Узнать свой Chat ID
/schedule - Показать моё расписание
/help - Показать эту справку

<b>🔔 Уведомления:</b>

Бот автоматически присылает уведомления:
• 🆕 При добавлении новых занятий
• 🔄 При изменении статуса занятий
• ❌ При отмене занятий

<b>🎯 Как начать получать уведомления:</b>

1. Используй команду /my_id
2. Скопируй свой Chat ID
3. Зайди на сайт расписания
4. Добавь Chat ID в профиль участника
5. Готово! Уведомления будут приходить автоматически

<b>💡 Полезная информация:</b>

• Chat ID — это твой уникальный номер в Telegram
• Он не меняется и всегда остаётся одинаковым
• Без Chat ID бот не сможет отправлять тебе уведомления
• Можно использовать один Chat ID для разных курсов

<b>❓ Возникли проблемы?</b>

Обратись к администратору системы или в техподдержку.
"""

    keyboard = [
        [InlineKeyboardButton("📋 Мой Chat ID", callback_data='show_chat_id')],
        [InlineKeyboardButton("📅 Расписание", callback_data='my_schedule')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатий на inline-кнопки
    """
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    callback_data = query.data

    if callback_data == 'show_chat_id':
        await query.message.reply_text(
            f"🆔 <b>Твой Chat ID:</b> <code>{chat_id}</code>\n\n"
            f"<i>Нажми на число, чтобы скопировать</i>",
            parse_mode='HTML'
        )

    elif callback_data == 'my_schedule':
        # Вызываем функцию расписания
        await schedule_command(Update(update.update_id, message=query.message), context)

    elif callback_data == 'help':
        await help_command(Update(update.update_id, message=query.message), context)

    elif callback_data == 'confirm_registered':
        await query.message.reply_text(
            "✅ Отлично! Теперь ты будешь получать уведомления о занятиях.\n\n"
            "Используй команду /schedule, чтобы посмотреть своё расписание.",
            parse_mode='HTML'
        )

    elif callback_data == 'where_add_id':
        await query.message.reply_text(
            "📝 <b>Где добавить Chat ID:</b>\n\n"
            "1. Зайди на сайт расписания\n"
            "2. Открой раздел <b>\"Участники\"</b>\n"
            "3. Создай или отредактируй свой профиль\n"
            "4. Найди поле <b>\"Telegram Chat ID\"</b>\n"
            "5. Вставь туда скопированный Chat ID\n"
            "6. Сохрани изменения\n\n"
            "Готово! 🎉",
            parse_mode='HTML'
        )

    elif callback_data == 'how_to_register':
        await query.message.reply_text(
            "📝 <b>Как зарегистрироваться:</b>\n\n"
            "1. Зайди на сайт системы расписания\n"
            "2. Зарегистрируйся или войди в аккаунт\n"
            "3. Добавь свой Chat ID в профиль\n"
            "4. Запиши на курсы\n\n"
            "После этого бот будет присылать уведомления!",
            parse_mode='HTML'
        )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик неизвестных команд
    """
    await update.message.reply_text(
        "❓ Неизвестная команда.\n\n"
        "Используй /help для списка доступных команд.",
        parse_mode='HTML'
    )


def main():
    """
    Главная функция для запуска бота
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        print("\n❌ ОШИБКА: Telegram Bot Token не настроен")
        print("Добавь TELEGRAM_BOT_TOKEN в файл .env\n")
        return

    logger.info("🤖 Инициализация Telegram бота...")
    print("\n" + "=" * 50)
    print("🤖 TELEGRAM БОТ - Умное расписание СурГУ")
    print("=" * 50)
    print(f"\n✅ Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")
    print(f"📂 База данных: {DATABASE_PATH}\n")

    # Создаём приложение бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("my_id", my_id_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик inline-кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запускаем бота
    logger.info("✅ Бот запущен и ожидает команды")
    print("✅ Бот успешно запущен!")
    print("\n📱 Команды бота:")
    print("   /start - Приветствие и инструкции")
    print("   /my_id - Показать Chat ID")
    print("   /schedule - Показать расписание")
    print("   /help - Справка")
    print("\n🔔 Бот автоматически отправляет уведомления о занятиях")
    print("\n⏹  Нажми Ctrl+C для остановки\n")
    print("=" * 50 + "\n")

    # Запускаем polling (бот будет слушать входящие сообщения)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен пользователем")
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"❌ Критическая ошибка: {e}")
