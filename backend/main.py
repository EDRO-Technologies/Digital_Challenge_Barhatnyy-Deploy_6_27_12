from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Query, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import uvicorn
import secrets
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import traceback

# Загружаем .env
load_dotenv()
print("=" * 60)
print("🚀 СИСТЕМА УМНОГО РАСПИСАНИЯ СУРГУ")
print("=" * 60)
print(f"📧 SMTP: {os.getenv('SMTP_USER', 'Не настроен')}")
print(f"🤖 Telegram Bot: {'✅ Настроен' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Не настроен'}")
print(f"📂 База данных: {os.getenv('DATABASE_PATH', './database.db')}")
print("=" * 60 + "\n")

# ========== ИМПОРТЫ ==========
from models import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ClassSlotCreate, ClassSlotUpdate
from auth import create_user, get_user_by_email, get_user_by_id, verify_password, create_access_token, decode_token, \
    set_auth_cookie, hash_password
from database import init_db, get_db
from courses_api import get_courses, create_course, get_course, update_course, delete_course, CourseCreate, \
    CourseUpdate, CourseResponse
from slots_api import create_class_slot, get_class_slot, update_class_slot, delete_class_slot
from participants_api import get_participants, create_participant, get_participant, delete_participant
from schedule_api import upload_schedule

# Импорт уведомлений с проверкой
try:
    from notifications import notify_slot_created, notify_slot_status_changed

    NOTIFICATIONS_ENABLED = True
    print("✅ Модуль уведомлений загружен успешно\n")
except Exception as e:
    print(f"⚠️  Модуль уведомлений не загружен: {e}\n")
    NOTIFICATIONS_ENABLED = False


    # Заглушки если модуль не загрузился
    async def notify_slot_created(*args, **kwargs):
        return {"success_count": 0, "failed_count": 0}


    async def notify_slot_status_changed(*args, **kwargs):
        return {"success_count": 0, "failed_count": 0}

# ========== ПРИЛОЖЕНИЕ ==========
app = FastAPI(title="Умное расписание СурГУ", version="3.0.0")

# CORS - РАЗРЕШАЕМ ВСЁ ДЛЯ РАЗРАБОТКИ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    print("✅ СЕРВЕР ЗАПУЩЕН: http://0.0.0.0:8000")
    print("📖 API Документация: http://0.0.0.0:8000/docs\n")


# ========== AUTH DEPENDENCY ==========
async def get_current_user(authorization: Optional[str] = Header(None), access_token: Optional[str] = Cookie(None)):
    """Получение текущего пользователя из токена"""
    token = access_token.replace("Bearer ", "") if access_token and access_token.startswith(
        "Bearer ") else access_token or (authorization.split()[1] if authorization and " " in authorization else None)
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = get_user_by_id(payload.get("user_id"))
    if not user:
        raise HTTPException(401, "User not found")
    return user


# ========== AUTH ENDPOINTS ==========
@app.post("/api/auth/register", response_model=TokenResponse, tags=["auth"])
async def register(data: RegisterRequest, response: Response):
    """Регистрация нового пользователя"""
    if get_user_by_email(data.email):
        raise HTTPException(400, "Email exists")
    user_id = create_user(data.email, data.password, data.full_name)
    token = create_access_token({"user_id": user_id})
    set_auth_cookie(response, token)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": data.email, "full_name": data.full_name}
    }


@app.post("/api/auth/login", response_model=TokenResponse, tags=["auth"])
async def login(data: LoginRequest, response: Response):
    """Вход пользователя"""
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"user_id": user["id"]})
    set_auth_cookie(response, token)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
    }


@app.get("/api/auth/me", response_model=UserResponse, tags=["auth"])
async def get_me(u=Depends(get_current_user)):
    """Получение данных текущего пользователя"""
    return {"id": u["id"], "email": u["email"], "full_name": u["full_name"]}


@app.post("/api/auth/logout", tags=["auth"])
async def logout(response: Response):
    """Выход пользователя"""
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ========== РАСПИСАНИЕ ==========
@app.get("/api/schedule", response_model=List[dict], tags=["schedule"])
async def get_schedule_list(
        date: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
):
    """Получение расписания с фильтрами"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT id, title, date_time, location, instructor, status
            FROM class_slots
            WHERE 1=1
        """
        params = []

        if date_from and date_to:
            query += " AND date(date_time) >= ? AND date(date_time) <= ?"
            params.extend([date_from, date_to])
        elif date:
            query += " AND date(date_time) = ?"
            params.append(date)

        real_limit = 2000 if (date_from or date_to) else limit
        query += " ORDER BY date_time DESC LIMIT ? OFFSET ?"
        params.extend([real_limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": r[0],
                "title": r[1] or "Без названия",
                "date_time": str(r[2]),
                "room": r[3],
                "teacher": r[4],
                "status": r[5]
            }
            for r in rows
        ]


@app.post("/api/schedule/upload", tags=["schedule"])
async def upload_schedule_ep(file: UploadFile = File(...), u=Depends(get_current_user)):
    """Загрузка расписания из Excel"""
    return await upload_schedule(file)


@app.post("/api/schedule", response_model=dict, tags=["schedule"])
async def create_slot_ep(data: ClassSlotCreate, u=Depends(get_current_user)):
    """
    Создание занятия с автоматической отправкой Telegram уведомлений участникам курса
    """
    print("\n" + "=" * 60)
    print("📝 СОЗДАНИЕ НОВОГО СЛОТА")
    print("=" * 60)
    print(f"   Курс ID: {data.course_id}")
    print(f"   Название: {data.title}")
    print(f"   Время: {data.date_time}")
    print(f"   Место: {data.location}")

    try:
        # Создаём слот
        slot = await create_class_slot(data)
        print(f"✅ Слот создан: ID={slot['id']}")

        # Получаем участников курса с telegram_chat_id
        with get_db() as conn:
            cursor = conn.cursor()

            # Получаем информацию о курсе
            cursor.execute("SELECT name FROM courses WHERE id = ?", (data.course_id,))
            course = cursor.fetchone()
            course_name = course[0] if course else "Неизвестный курс"
            print(f"📚 Курс: {course_name}")

            # Получаем всех участников курса с Telegram ID
            cursor.execute("""
                SELECT DISTINCT u.id, u.full_name, u.telegram_id
                FROM users u
                WHERE u.telegram_id IS NOT NULL
                AND u.id IN (
                    SELECT DISTINCT p.user_id 
                    FROM participants p
                    INNER JOIN class_slots cs ON p.class_slot_id = cs.id
                    WHERE cs.course_id = ?
                )
            """, (data.course_id,))

            participants_raw = cursor.fetchall()

            participants = [
                {"id": row[0], "telegram_chat_id": row[2]}
                for row in participants_raw
            ]

            print(f"👥 Найдено участников с Telegram: {len(participants)}")
            for row in participants_raw:
                print(f"      - {row[1]} (chat_id: {row[2]})")

            # Формируем данные для уведомления
            slot_data = {
                "course_name": course_name,
                "start_time": data.date_time,
                "end_time": data.date_time,
                "location": data.location or "Не указано",
                "status": "scheduled"
            }

            notification_result = {"success_count": 0, "failed_count": 0}

            if participants and NOTIFICATIONS_ENABLED:
                try:
                    print(f"\n📤 Отправка Telegram уведомлений о новом занятии...")
                    notification_result = await notify_slot_created(participants, slot_data)  # АСИНХРОННЫЙ ВЫЗОВ
                    print(f"✅ Уведомления отправлены:")
                    print(f"   ✓ Успешно: {notification_result['success_count']}")
                    if notification_result['failed_count'] > 0:
                        print(f"   ✗ Ошибок: {notification_result['failed_count']}")
                        if notification_result.get('failed_chat_ids'):
                            print(f"   Не удалось отправить на: {notification_result['failed_chat_ids']}")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомлений: {e}")
                    traceback.print_exc()
            elif not NOTIFICATIONS_ENABLED:
                print("⚠️  Уведомления отключены (модуль не загружен)")
            else:
                print(f"⚠️  Нет участников с Telegram для курса ID={data.course_id}")

            slot["notifications_sent"] = notification_result['success_count']
            slot["notifications_failed"] = notification_result['failed_count']

        print("=" * 60 + "\n")
        return slot

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        traceback.print_exc()
        print("=" * 60 + "\n")
        raise


@app.get("/api/schedule/{slot_id}", response_model=dict, tags=["schedule"])
async def get_slot_ep(slot_id: int):
    """Получение занятия по ID"""
    return await get_class_slot(slot_id)


@app.put("/api/schedule/{slot_id}", response_model=dict, tags=["schedule"])
async def update_slot_ep(slot_id: int, data: ClassSlotUpdate, u=Depends(get_current_user)):
    """
    Обновление занятия с автоматической отправкой Telegram уведомлений при изменении статуса
    """

    # Получаем текущий статус до обновления
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, course_id, title, date_time, location 
            FROM class_slots 
            WHERE id = ?
        """, (slot_id,))

        current_slot = cursor.fetchone()

        if not current_slot:
            raise HTTPException(status_code=404, detail="Занятие не найдено")

        old_status = current_slot[0]
        course_id = current_slot[1]
        title = current_slot[2]
        date_time = current_slot[3]
        location = current_slot[4]

    # Обновляем слот
    updated_slot = await update_class_slot(slot_id, data)

    # Проверяем, изменился ли статус
    new_status = data.status if data.status else old_status

    if new_status != old_status:
        print("\n" + "=" * 60)
        print("🔄 ИЗМЕНЕНИЕ СТАТУСА СЛОТА")
        print("=" * 60)
        print(f"   Слот ID: {slot_id}")
        print(f"   Название: {title}")
        print(f"   Старый статус: {old_status}")
        print(f"   Новый статус: {new_status}")

        try:
            # Получаем информацию о курсе и участниках
            with get_db() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM courses WHERE id = ?", (course_id,))
                course = cursor.fetchone()
                course_name = course[0] if course else "Неизвестный курс"
                print(f"📚 Курс: {course_name}")

                # Получаем участников ЭТОГО слота с Telegram ID
                cursor.execute("""
                    SELECT u.id, u.full_name, u.telegram_id
                    FROM users u
                    INNER JOIN participants p ON u.id = p.user_id
                    WHERE p.class_slot_id = ?
                    AND u.telegram_id IS NOT NULL
                """, (slot_id,))

                participants_raw = cursor.fetchall()

                participants = [
                    {"id": row[0], "telegram_chat_id": row[2]}
                    for row in participants_raw
                ]

                print(f"👥 Найдено участников с Telegram: {len(participants)}")
                for row in participants_raw:
                    print(f"      - {row[1]} (chat_id: {row[2]})")

            # Формируем данные для уведомления
            slot_data = {
                "course_name": course_name,
                "start_time": date_time,
                "end_time": date_time,
                "location": location or "Не указано",
                "status": new_status
            }

            # Отправляем уведомления
            notification_result = {"success_count": 0, "failed_count": 0}

            if participants and NOTIFICATIONS_ENABLED:
                try:
                    print(f"\n📤 Отправка Telegram уведомлений об изменении статуса...")
                    notification_result = await notify_slot_status_changed(participants, slot_data,
                                                                           old_status)  # АСИНХРОННЫЙ ВЫЗОВ
                    print(f"✅ Уведомления отправлены:")
                    print(f"   ✓ Успешно: {notification_result['success_count']}")
                    if notification_result['failed_count'] > 0:
                        print(f"   ✗ Ошибок: {notification_result['failed_count']}")
                        if notification_result.get('failed_chat_ids'):
                            print(f"   Не удалось отправить на: {notification_result['failed_chat_ids']}")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомлений: {e}")
                    traceback.print_exc()
            elif not NOTIFICATIONS_ENABLED:
                print("⚠️  Уведомления отключены (модуль не загружен)")
            else:
                print("⚠️  Нет участников с Telegram для этого занятия")

            # Добавляем информацию об уведомлениях в ответ
            updated_slot["status_changed"] = True
            updated_slot["old_status"] = old_status
            updated_slot["notifications_sent"] = notification_result['success_count']
            updated_slot["notifications_failed"] = notification_result['failed_count']

            print("=" * 60 + "\n")

        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
            print("=" * 60 + "\n")
    else:
        print(f"ℹ️  Статус слота ID={slot_id} не изменился ({new_status})")

    return updated_slot


@app.patch("/api/schedule/{slot_id}/status", tags=["schedule"])
async def change_slot_status(slot_id: int, status: str, u=Depends(get_current_user)):
    """Быстрое изменение статуса занятия"""
    data = ClassSlotUpdate(status=status)
    return await update_slot_ep(slot_id, data, u)


@app.delete("/api/schedule/{slot_id}", tags=["schedule"])
async def delete_slot_ep(slot_id: int, u=Depends(get_current_user)):
    """Удаление занятия"""
    return await delete_class_slot(slot_id)


# ========== КУРСЫ ==========
@app.get("/api/courses", response_model=List[CourseResponse], tags=["courses"])
async def get_courses_ep(name: Optional[str] = None, limit: int = 100, offset: int = 0):
    """Получение списка курсов"""
    return await get_courses(name, None, None, limit, offset)


@app.post("/api/courses", response_model=CourseResponse, tags=["courses"])
async def create_course_ep(data: CourseCreate, u=Depends(get_current_user)):
    """Создание курса"""
    return await create_course(data)


@app.get("/api/courses/{course_id}", response_model=CourseResponse, tags=["courses"])
async def get_course_ep(course_id: int):
    """Получение курса по ID"""
    return await get_course(course_id)


@app.put("/api/courses/{course_id}", response_model=CourseResponse, tags=["courses"])
async def update_course_ep(course_id: int, data: CourseUpdate, u=Depends(get_current_user)):
    """Обновление курса"""
    return await update_course(course_id, data)


@app.delete("/api/courses/{course_id}", tags=["courses"])
async def delete_course_ep(course_id: int, u=Depends(get_current_user)):
    """Удаление курса"""
    return await delete_course(course_id)


# ========== УЧАСТНИКИ КУРСОВ ==========

@app.get("/api/courses/{course_id}/participants", tags=["participants"])
async def get_course_participants(course_id: int):
    """Получение участников курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM courses WHERE id = ?", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Курс не найден")

        cursor.execute("""
            SELECT id, email, full_name, telegram_id
            FROM users
            WHERE id > 1
            ORDER BY full_name
        """)

        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "telegram": row[3]
            }
            for row in rows
        ]


@app.post("/api/courses/{course_id}/participants", tags=["participants"])
async def add_course_participant(course_id: int, data: dict, u=Depends(get_current_user)):
    """
    Добавление участника к курсу с автоматической регистрацией на все занятия
    Поддерживает Telegram Chat ID для уведомлений
    """
    print("\n" + "=" * 60)
    print(f"🔵 ДОБАВЛЕНИЕ УЧАСТНИКА К КУРСУ {course_id}")
    print("=" * 60)
    print(f"   Данные: {data}")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM courses WHERE id = ?", (course_id,))
            course = cursor.fetchone()
            if not course:
                raise HTTPException(status_code=404, detail="Курс не найден")

            course_name = course[1]
            print(f"📚 Курс: {course_name}")

            email = data.get("email")
            if not email:
                raise HTTPException(status_code=400, detail="Email обязателен")

            print(f"📧 Email: {email}")

            # Получаем telegram_id из любого поля
            telegram_id = data.get("telegram") or data.get("chatId")
            if telegram_id:
                print(f"🤖 Telegram Chat ID: {telegram_id}")

            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            existing = cursor.fetchone()

            if existing:
                user_id = existing[0]
                print(f"✅ Пользователь найден: ID={user_id}")

                # Обновляем telegram_id если передан
                if telegram_id:
                    cursor.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id))
                    print(f"✅ Обновлён telegram_id: {telegram_id}")
            else:
                name = data.get("name") or email.split("@")[0]
                password = secrets.token_urlsafe(12)
                password_hash = hash_password(password)

                cursor.execute("""
                    INSERT INTO users (email, password_hash, full_name, telegram_id)
                    VALUES (?, ?, ?, ?)
                """, (email, password_hash, name, telegram_id))

                user_id = cursor.lastrowid
                print(f"✅ Создан новый пользователь: ID={user_id}")
                if telegram_id:
                    print(f"✅ С telegram_id: {telegram_id}")

            # Получаем все слоты курса
            cursor.execute("SELECT id, title FROM class_slots WHERE course_id = ?", (course_id,))
            slots = cursor.fetchall()

            print(f"📋 Найдено слотов курса: {len(slots)}")

            if not slots:
                print(f"⚠️  У курса нет занятий, но пользователь создан/найден")
                print("=" * 60 + "\n")
                return {
                    "message": "Участник добавлен к курсу. Занятий пока нет.",
                    "course_id": course_id,
                    "user_id": user_id,
                    "slots_added": 0,
                    "telegram_id": telegram_id
                }

            added_count = 0
            now = datetime.now().isoformat()

            for slot in slots:
                slot_id = slot[0]
                slot_title = slot[1]
                try:
                    cursor.execute("""
                        INSERT INTO participants (class_slot_id, user_id, status, registered_at)
                        VALUES (?, ?, 'registered', ?)
                    """, (slot_id, user_id, now))
                    added_count += 1
                    print(f"   ✓ Добавлен к слоту #{slot_id}: {slot_title}")
                except sqlite3.IntegrityError:
                    print(f"   - Уже зарегистрирован на слот #{slot_id}")

            print(f"\n✅ ИТОГО: добавлен к {added_count} занятиям")
            if telegram_id:
                print(f"🔔 Будет получать уведомления в Telegram (chat_id: {telegram_id})")
            print("=" * 60 + "\n")

            return {
                "message": f"Участник добавлен к {added_count} занятиям курса",
                "course_id": course_id,
                "user_id": user_id,
                "slots_added": added_count,
                "telegram_id": telegram_id,
                "course_name": course_name
            }

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        traceback.print_exc()
        print("=" * 60 + "\n")
        raise


@app.delete("/api/courses/{course_id}/participants/{user_id}", tags=["participants"])
async def remove_course_participant(course_id: int, user_id: int, u=Depends(get_current_user)):
    """Удаление участника из курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM courses WHERE id = ?", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Курс не найден")

        cursor.execute("""
            DELETE FROM participants
            WHERE user_id = ?
            AND class_slot_id IN (SELECT id FROM class_slots WHERE course_id = ?)
        """, (user_id, course_id))

        deleted_count = cursor.rowcount

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Участник не найден в этом курсе")

        return {
            "message": f"Участник удалён с {deleted_count} занятий курса",
            "course_id": course_id,
            "user_id": user_id,
            "slots_removed": deleted_count
        }


# ========== TELEGRAM ПОДПИСКА ==========

@app.post("/api/notifications/subscribe-telegram", tags=["notifications"])
async def subscribe_telegram(telegram_id: str, u=Depends(get_current_user)):
    """Подписка на Telegram уведомления"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, u["id"]))
    print(f"✅ Пользователь ID={u['id']} подписался на Telegram: {telegram_id}")
    return {"message": "Telegram подписка активирована", "telegram_id": telegram_id}


# ========== HEALTH CHECK ==========

@app.get("/api/health", tags=["system"])
async def health_check():
    """Проверка работоспособности системы"""
    return {
        "status": "healthy",
        "telegram": "enabled" if NOTIFICATIONS_ENABLED else "disabled",
        "database": "connected",
        "version": "3.0.0"
    }


# ========== ЗАПУСК ==========

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
