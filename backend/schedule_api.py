from fastapi import UploadFile, File, HTTPException
from typing import List
from pydantic import BaseModel
from database import get_db
from parser import parse_excel_schedule
import os
import tempfile


# Модели данных
class ScheduleEntry(BaseModel):
    id: int
    course_name: str = None  # переименовано из group_name
    day_of_week: int
    time_slot: str
    subject: str
    teacher: str = None
    room: str = None


# Вспомогательные функции для работы с БД
def get_or_create_course(course_name: str) -> int:
    """Получить ID курса или создать новый"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование
        cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
        result = cursor.fetchone()

        if result:
            return result[0]

        # Создаём новый
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (course_name,))
        return cursor.lastrowid


def save_schedule_entries(entries: List[dict]):
    """Сохранение записей расписания в БД"""
    with get_db() as conn:
        cursor = conn.cursor()

        for entry in entries:
            course_id = get_or_create_course(entry['course_name'])

            # Добавляем в schedule
            cursor.execute("""
                INSERT INTO schedule (course_id, day_of_week, time_slot, subject, teacher, room)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                course_id,
                entry['day_of_week'],
                entry['time_slot'],
                entry['subject'],
                entry.get('teacher'),
                entry.get('room')
            ))


async def upload_schedule(file: UploadFile = File(...)):
    """Загрузка расписания из Excel файла"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx or .xls)")

    # Сохраняем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Парсим расписание
        entries = parse_excel_schedule(temp_path)

        # Сохраняем в БД
        save_schedule_entries(entries)

        return {
            "message": "Schedule uploaded successfully",
            "entries_count": len(entries)
        }
    finally:
        os.unlink(temp_path)


async def get_schedule_by_course(course_name: str):
    """Получение расписания для курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Ищем course_id
        cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
        course = cursor.fetchone()

        if not course:
            return []

        course_id = course[0]

        # Получаем расписание
        cursor.execute("""
            SELECT id, day_of_week, time_slot, subject, teacher, room
            FROM schedule
            WHERE course_id = ?
            ORDER BY day_of_week, time_slot
        """, (course_id,))

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "course_name": course_name,
                "day_of_week": row[1],
                "time_slot": row[2],
                "subject": row[3],
                "teacher": row[4],
                "room": row[5]
            }
            for row in rows
        ]


async def get_all_courses():
    """Получение списка всех курсов"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM courses ORDER BY name")

        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
