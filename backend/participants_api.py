from fastapi import HTTPException
from database import get_db
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def create_participant(data: dict):
    """
    Создание участника с поддержкой telegram Chat ID
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем, существует ли пользователь с таким email
        cursor.execute("SELECT id FROM users WHERE email = ?", (data.get('email'),))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user[0]

            # Обновляем telegram_id если он предоставлен
            if data.get('telegram'):
                cursor.execute("""
                    UPDATE users SET telegram_id = ? WHERE id = ?
                """, (data.get('telegram'), user_id))
                logger.info(f"✅ Обновлён telegram_id для пользователя ID={user_id}")
        else:
            # Создаём нового пользователя
            from auth import hash_password
            import secrets

            temp_password = secrets.token_urlsafe(12)
            password_hash = hash_password(temp_password)

            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, telegram_id)
                VALUES (?, ?, ?, ?)
            """, (
                data.get('email'),
                password_hash,
                data.get('name'),
                data.get('telegram')
            ))

            user_id = cursor.lastrowid
            logger.info(f"✅ Создан новый пользователь ID={user_id} с telegram_id={data.get('telegram')}")

        # Добавляем участника к слоту если указан
        if data.get('class_slot_id'):
            try:
                cursor.execute("""
                    INSERT INTO participants (class_slot_id, user_id, status)
                    VALUES (?, ?, ?)
                """, (data.get('class_slot_id'), user_id, data.get('status', 'registered')))

                logger.info(f"✅ Участник добавлен к слоту ID={data.get('class_slot_id')}")
            except Exception as e:
                logger.warning(f"⚠️  Участник уже зарегистрирован на этот слот: {e}")

        # Добавляем участника ко всем слотам курса если указан course_id
        if data.get('course_id'):
            cursor.execute("""
                SELECT id FROM class_slots WHERE course_id = ?
            """, (data.get('course_id'),))

            slots = cursor.fetchall()
            added_count = 0

            for slot in slots:
                try:
                    cursor.execute("""
                        INSERT INTO participants (class_slot_id, user_id, status)
                        VALUES (?, ?, ?)
                    """, (slot[0], user_id, data.get('status', 'registered')))
                    added_count += 1
                except:
                    pass  # Уже зарегистрирован

            logger.info(f"✅ Участник добавлен к {added_count} слотам курса ID={data.get('course_id')}")

        return {
            "id": user_id,
            "name": data.get('name'),
            "email": data.get('email'),
            "telegram": data.get('telegram'),
            "status": "created"
        }


async def get_participants(
        email: Optional[str] = None,
        course_id: Optional[int] = None,
        slot_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
):
    """
    Получение списка участников с фильтрацией
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT u.id, u.email, u.full_name, u.telegram_id
            FROM users u
        """

        conditions = []
        params = []

        if course_id or slot_id:
            query += " INNER JOIN participants p ON u.id = p.user_id"

            if slot_id:
                query += " WHERE p.class_slot_id = ?"
                params.append(slot_id)
            elif course_id:
                query += """
                    INNER JOIN class_slots cs ON p.class_slot_id = cs.id
                    WHERE cs.course_id = ?
                """
                params.append(course_id)

        if email:
            conditions.append("u.email LIKE ?")
            params.append(f"%{email}%")

        if conditions:
            if 'WHERE' in query:
                query += " AND " + " AND ".join(conditions)
            else:
                query += " WHERE " + " AND ".join(conditions)

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
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


async def get_participant(participant_id: int):
    """Получение участника по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, telegram_id
            FROM users WHERE id = ?
        """, (participant_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Участник не найден")

        return {
            "id": row[0],
            "email": row[1],
            "name": row[2],
            "telegram": row[3]
        }


async def delete_participant(participant_id: int):
    """Удаление участника"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (participant_id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Участник не найден")

        return {"message": "Участник удалён"}
