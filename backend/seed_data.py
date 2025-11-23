"""
Скрипт для заполнения базы данных тестовыми данными
Создаёт пользователей, курсы, занятия и участников
"""

import sqlite3
from auth import hash_password
from database import DATABASE_PATH
from datetime import datetime, timedelta


def seed_database():
    """Заполняет БД тестовыми данными"""
    print("\n" + "=" * 60)
    print("🌱 ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ ТЕСТОВЫМИ ДАННЫМИ")
    print("=" * 60 + "\n")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # ========== 1. СОЗДАЁМ АДМИНИСТРАТОРА ==========
        print("👤 Создание администратора...")
        password_hash = hash_password("admin123")
        cursor.execute("""
            INSERT OR IGNORE INTO users (email, password_hash, full_name, telegram_id)
            VALUES (?, ?, ?, ?)
        """, ("admin@surgu.ru", password_hash, "Администратор Системы", None))

        admin_id = cursor.lastrowid if cursor.lastrowid > 0 else 1
        print(f"✅ Админ создан:")
        print(f"   📧 Email: admin@surgu.ru")
        print(f"   🔑 Пароль: admin123")
        print(f"   🆔 ID: {admin_id}\n")

        # ========== 2. СОЗДАЁМ СТУДЕНТОВ ==========
        print("👨‍🎓 Создание студентов...")
        students = [
            ("ivanov@surgu.ru", "Иванов Иван Иванович", "123456789"),
            ("petrov@surgu.ru", "Петров Пётр Петрович", "987654321"),
            ("sidorova@surgu.ru", "Сидорова Анна Сергеевна", "555444333"),
            ("kozlov@surgu.ru", "Козлов Михаил Андреевич", None),
            ("vasileva@surgu.ru", "Васильева Елена Дмитриевна", None)
        ]

        student_ids = []
        for email, name, telegram_id in students:
            password_hash = hash_password("student123")
            cursor.execute("""
                INSERT OR IGNORE INTO users (email, password_hash, full_name, telegram_id)
                VALUES (?, ?, ?, ?)
            """, (email, password_hash, name, telegram_id))

            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            user_id = cursor.fetchone()[0]
            student_ids.append(user_id)

        print(f"✅ Создано {len(students)} студентов:")
        for idx, (email, name, telegram_id) in enumerate(students):
            telegram_status = f"📱 {telegram_id}" if telegram_id else "❌ без Telegram"
            print(f"   {idx + 1}. {name} ({email}) {telegram_status}")
        print(f"   🔑 Пароль для всех: student123\n")

        # ========== 3. СОЗДАЁМ КУРСЫ ==========
        print("📚 Создание курсов...")
        courses = [
            ("Основы программирования", "Введение в Python, алгоритмы и структуры данных", "Иванова М.А.", "2025-09-01",
             "2025-12-31"),
            ("Базы данных", "SQL, NoSQL, проектирование БД", "Петров С.И.", "2025-09-01", "2025-12-31"),
            ("Web-разработка", "HTML, CSS, JavaScript, React, FastAPI", "Сидорова Е.В.", "2025-09-01", "2025-12-31"),
            ("Математический анализ", "Пределы, производные, интегралы", "Козлов А.П.", "2025-09-01", "2025-12-31")
        ]

        course_ids = []
        for name, desc, instructor, start, end in courses:
            cursor.execute("""
                INSERT INTO courses (name, description, instructor, start_date, end_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, desc, instructor, start, end))
            course_ids.append(cursor.lastrowid)

        print(f"✅ Создано {len(courses)} курсов:")
        for idx, (name, _, instructor, _, _) in enumerate(courses):
            print(f"   {idx + 1}. {name} (👨‍🏫 {instructor})")
        print()

        # ========== 4. СОЗДАЁМ ЗАНЯТИЯ ==========
        print("📅 Создание занятий...")

        # Базовая дата для занятий
        base_date = datetime(2025, 11, 25, 10, 0, 0)

        # Занятия для первого курса (Основы программирования)
        slots_course_1 = [
            ("Лекция 1: Введение в Python", base_date, "Аудитория 301", "Иванова М.А.", 30, "scheduled"),
            ("Практика 1: Переменные и типы данных", base_date + timedelta(days=2, hours=4), "Компьютерный класс 205",
             "Иванова М.А.", 15, "scheduled"),
            ("Лекция 2: Условия и циклы", base_date + timedelta(days=7), "Аудитория 301", "Иванова М.А.", 30,
             "scheduled"),
            ("Практика 2: Решение задач", base_date + timedelta(days=9, hours=4), "Компьютерный класс 205",
             "Иванова М.А.", 15, "scheduled"),
            ("Лекция 3: Функции", base_date + timedelta(days=14), "Аудитория 301", "Иванова М.А.", 30, "scheduled"),
        ]

        # Занятия для второго курса (Базы данных)
        slots_course_2 = [
            ("Лекция 1: Основы реляционных БД", base_date + timedelta(days=1), "Аудитория 205", "Петров С.И.", 25,
             "scheduled"),
            ("Практика 1: SQL запросы", base_date + timedelta(days=3, hours=4), "Компьютерный класс 310", "Петров С.И.",
             12, "scheduled"),
            ("Лекция 2: NoSQL базы данных", base_date + timedelta(days=8), "Аудитория 205", "Петров С.И.", 25,
             "scheduled"),
        ]

        # Занятия для третьего курса (Web-разработка)
        slots_course_3 = [
            ("Лекция 1: HTML и CSS", base_date + timedelta(days=1, hours=2), "Аудитория 410", "Сидорова Е.В.", 20,
             "scheduled"),
            ("Практика 1: Создание веб-страницы", base_date + timedelta(days=4, hours=4), "Компьютерный класс 205",
             "Сидорова Е.В.", 15, "scheduled"),
        ]

        all_slots = [
            (course_ids[0], slots_course_1),
            (course_ids[1], slots_course_2),
            (course_ids[2], slots_course_3)
        ]

        slot_ids_by_course = {}
        total_slots = 0

        for course_id, slots in all_slots:
            slot_ids = []
            for title, date_time, location, instructor, max_part, status in slots:
                cursor.execute("""
                    INSERT INTO class_slots (course_id, title, date_time, location, instructor, max_participants, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (course_id, title, date_time.strftime("%Y-%m-%d %H:%M:%S"), location, instructor, max_part,
                      status))
                slot_ids.append(cursor.lastrowid)
                total_slots += 1
            slot_ids_by_course[course_id] = slot_ids

        print(f"✅ Создано {total_slots} занятий:")
        for idx, (course_id, slots) in enumerate(all_slots):
            print(f"   Курс {idx + 1} ({courses[idx][0]}): {len(slots)} занятий")
        print()

        # ========== 5. ЗАПИСЫВАЕМ СТУДЕНТОВ НА КУРСЫ ==========
        print("📝 Регистрация студентов на занятия...")

        # Первые 3 студента на первый курс (с Telegram)
        for student_id in student_ids[:3]:
            for slot_id in slot_ids_by_course[course_ids[0]]:
                cursor.execute("""
                    INSERT OR IGNORE INTO participants (class_slot_id, user_id, status)
                    VALUES (?, ?, 'registered')
                """, (slot_id, student_id))

        # Студенты 2-4 на второй курс
        for student_id in student_ids[1:4]:
            for slot_id in slot_ids_by_course[course_ids[1]]:
                cursor.execute("""
                    INSERT OR IGNORE INTO participants (class_slot_id, user_id, status)
                    VALUES (?, ?, 'registered')
                """, (slot_id, student_id))

        # Студенты 3-5 на третий курс
        for student_id in student_ids[2:5]:
            for slot_id in slot_ids_by_course[course_ids[2]]:
                cursor.execute("""
                    INSERT OR IGNORE INTO participants (class_slot_id, user_id, status)
                    VALUES (?, ?, 'registered')
                """, (slot_id, student_id))

        print(f"✅ Регистрация завершена:")
        print(f"   Курс 1 (Основы программирования): 3 студента")
        print(f"   Курс 2 (Базы данных): 3 студента")
        print(f"   Курс 3 (Web-разработка): 3 студента")
        print()

        conn.commit()

        # ========== ИТОГОВАЯ СТАТИСТИКА ==========
        print("=" * 60)
        print("🎉 БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
        print("=" * 60)
        print("\n📊 Итоговая статистика:")
        print(f"   👤 Пользователей: {len(students) + 1} (1 админ + {len(students)} студентов)")
        print(f"   📚 Курсов: {len(courses)}")
        print(f"   📅 Занятий: {total_slots}")

        cursor.execute("SELECT COUNT(*) FROM participants")
        participants_count = cursor.fetchone()[0]
        print(f"   📝 Записей на занятия: {participants_count}")

        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
        telegram_users = cursor.fetchone()[0]
        print(f"   📱 Пользователей с Telegram: {telegram_users}")

        print("\n🔑 Учётные данные для входа:")
        print("   Админ: admin@surgu.ru / admin123")
        print("   Студенты: *@surgu.ru / student123")

        print("\n📱 Студенты с Telegram ID (получат уведомления):")
        for idx, (email, name, telegram_id) in enumerate(students[:3]):
            print(f"   {idx + 1}. {name}: {telegram_id}")

        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ОШИБКА: {e}\n")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_database()
