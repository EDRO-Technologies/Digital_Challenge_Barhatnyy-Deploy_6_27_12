from fastapi import HTTPException
from database import get_db
from models import CourseCreate, CourseUpdate, CourseResponse
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


async def get_courses(
        name: Optional[str] = None,
        instructor: Optional[str] = None,
        semester: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
) -> List[dict]:
    """Получение списка курсов с фильтрацией"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT id, name, description, instructor, start_date, end_date FROM courses WHERE 1=1"
        params = []

        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")

        if instructor:
            query += " AND instructor LIKE ?"
            params.append(f"%{instructor}%")

        query += " ORDER BY name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "instructor": row[3],
                "start_date": row[4],
                "end_date": row[5]
            }
            for row in rows
        ]


async def create_course(data: CourseCreate) -> dict:
    """Создание нового курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO courses (name, description, instructor, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data.name, data.description, data.instructor, data.start_date, data.end_date)
        )

        course_id = cursor.lastrowid

        logger.info(f"✅ Создан курс ID={course_id}: {data.name}")

        return {
            "id": course_id,
            "name": data.name,
            "description": data.description,
            "instructor": data.instructor,
            "start_date": data.start_date,
            "end_date": data.end_date
        }


async def get_course(course_id: int) -> dict:
    """Получение курса по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, instructor, start_date, end_date FROM courses WHERE id = ?",
            (course_id,)
        )

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Курс с ID {course_id} не найден")

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "instructor": row[3],
            "start_date": row[4],
            "end_date": row[5]
        }


async def update_course(course_id: int, data: CourseUpdate) -> dict:
    """Обновление курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование курса
        cursor.execute("SELECT id FROM courses WHERE id = ?", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Курс с ID {course_id} не найден")

        # Формируем список полей для обновления
        updates = []
        params = []

        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)

        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)

        if data.instructor is not None:
            updates.append("instructor = ?")
            params.append(data.instructor)

        if data.start_date is not None:
            updates.append("start_date = ?")
            params.append(data.start_date)

        if data.end_date is not None:
            updates.append("end_date = ?")
            params.append(data.end_date)

        if not updates:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")

        # Выполняем обновление
        params.append(course_id)
        query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        logger.info(f"✅ Обновлён курс ID={course_id}")

        # Возвращаем обновлённый курс
        return await get_course(course_id)


async def delete_course(course_id: int) -> dict:
    """Удаление курса"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Проверяем существование курса
        cursor.execute("SELECT id FROM courses WHERE id = ?", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Курс с ID {course_id} не найден")

        # Удаляем курс (каскадно удалятся все связанные занятия и участники)
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))

        logger.info(f"🗑️  Удалён курс ID={course_id}")

        return {"message": f"Курс {course_id} успешно удалён"}
