from fastapi import HTTPException
from database import get_db
from models import ClassSlotCreate, ClassSlotUpdate, ClassSlotResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def create_class_slot(data: ClassSlotCreate) -> dict:
    """Создание нового слота (занятия)"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование курса
        cursor.execute("SELECT id FROM courses WHERE id = ?", (data.course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Курс с ID {data.course_id} не найден")

        # Создаём слот
        cursor.execute("""
            INSERT INTO class_slots (course_id, title, date_time, location, instructor, max_participants, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.course_id,
            data.title,
            data.date_time,
            data.location,
            data.instructor,
            data.max_participants,
            data.status
        ))

        slot_id = cursor.lastrowid

        logger.info(f"✅ Создан слот ID={slot_id}: {data.title}")

        return {
            "id": slot_id,
            "course_id": data.course_id,
            "title": data.title,
            "date_time": data.date_time,
            "location": data.location,
            "instructor": data.instructor,
            "max_participants": data.max_participants,
            "status": data.status
        }


async def get_class_slot(slot_id: int) -> dict:
    """Получение слота по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, course_id, title, date_time, location, instructor, max_participants, status
            FROM class_slots
            WHERE id = ?
        """, (slot_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Слот с ID {slot_id} не найден")

        return {
            "id": row[0],
            "course_id": row[1],
            "title": row[2],
            "date_time": row[3],
            "location": row[4],
            "instructor": row[5],
            "max_participants": row[6],
            "status": row[7]
        }


async def update_class_slot(slot_id: int, data: ClassSlotUpdate) -> dict:
    """Обновление слота"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование слота
        cursor.execute("SELECT id FROM class_slots WHERE id = ?", (slot_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Слот с ID {slot_id} не найден")

        # Формируем список полей для обновления
        updates = []
        params = []

        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)

        if data.date_time is not None:
            updates.append("date_time = ?")
            params.append(data.date_time)

        if data.location is not None:
            updates.append("location = ?")
            params.append(data.location)

        if data.instructor is not None:
            updates.append("instructor = ?")
            params.append(data.instructor)

        if data.max_participants is not None:
            updates.append("max_participants = ?")
            params.append(data.max_participants)

        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)

        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        # Выполняем обновление
        params.append(slot_id)
        query = f"UPDATE class_slots SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        logger.info(f"✅ Обновлён слот ID={slot_id}")

        # Возвращаем обновлённый слот
        return await get_class_slot(slot_id)


async def delete_class_slot(slot_id: int) -> dict:
    """Удаление слота"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование слота
        cursor.execute("SELECT id FROM class_slots WHERE id = ?", (slot_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Слот с ID {slot_id} не найден")

        # Удаляем слот (каскадно удалятся все связанные участники)
        cursor.execute("DELETE FROM class_slots WHERE id = ?", (slot_id,))

        logger.info(f"🗑️  Удалён слот ID={slot_id}")

        return {"message": f"Слот {slot_id} успешно удалён"}


async def update_class_slot_status(slot_id: int, new_status: str) -> dict:
    """Обновление статуса слота"""
    valid_statuses = ["scheduled", "in_progress", "completed", "cancelled"]

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый статус. Допустимые значения: {', '.join(valid_statuses)}"
        )

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM class_slots WHERE id = ?", (slot_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Слот с ID {slot_id} не найден")

        cursor.execute("UPDATE class_slots SET status = ? WHERE id = ?", (new_status, slot_id))

        logger.info(f"✅ Статус слота ID={slot_id} изменён на {new_status}")

        return await get_class_slot(slot_id)
