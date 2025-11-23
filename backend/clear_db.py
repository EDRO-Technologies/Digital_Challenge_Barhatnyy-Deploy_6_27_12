"""
Скрипт для очистки и пересоздания базы данных
ВНИМАНИЕ: Удаляет ВСЕ данные без возможности восстановления!
"""

import os
import sqlite3
from database import DATABASE_PATH, init_db
from datetime import datetime


def backup_database():
    """Создаёт резервную копию БД перед очисткой"""
    if os.path.exists(DATABASE_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{DATABASE_PATH}.backup_{timestamp}"

        try:
            import shutil
            shutil.copy2(DATABASE_PATH, backup_path)
            print(f"✅ Резервная копия создана: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️  Не удалось создать резервную копию: {e}")
            return None
    return None


def clear_all_data():
    """Удаляет все данные из всех таблиц, но сохраняет структуру"""
    print("\n" + "=" * 60)
    print("🗑️  ОЧИСТКА ВСЕХ ДАННЫХ ИЗ БАЗЫ")
    print("=" * 60 + "\n")

    if not os.path.exists(DATABASE_PATH):
        print("❌ База данных не найдена!")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()

        print("📋 Найденные таблицы:")
        for table in tables:
            print(f"   - {table[0]}")
        print()

        # Отключаем проверку внешних ключей для удаления
        cursor.execute("PRAGMA foreign_keys = OFF")

        # Удаляем данные из каждой таблицы
        deleted_counts = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            deleted_counts[table_name] = count

            cursor.execute(f"DELETE FROM {table_name}")
            print(f"🗑️  Таблица '{table_name}': удалено {count} записей")

        # Сбрасываем автоинкремент
        cursor.execute("DELETE FROM sqlite_sequence")

        # Включаем обратно проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ ВСЕ ДАННЫЕ УСПЕШНО УДАЛЕНЫ!")
        print("=" * 60)
        print("\n📊 Удалено записей:")
        total = 0
        for table_name, count in deleted_counts.items():
            print(f"   {table_name}: {count}")
            total += count
        print(f"\n   ВСЕГО: {total} записей")
        print("\n💡 Структура таблиц сохранена, можно заполнить заново.")
        print("   Запустите: python seed_data.py")
        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ОШИБКА: {e}\n")
        raise
    finally:
        conn.close()


def reset_database():
    """Полностью удаляет и пересоздаёт базу данных"""
    print("\n" + "=" * 60)
    print("🔄 ПОЛНОЕ ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60 + "\n")

    # Создаём резервную копию
    backup_path = backup_database()

    if os.path.exists(DATABASE_PATH):
        print(f"🗑️  Удаление старой базы данных...")
        os.remove(DATABASE_PATH)
        print(f"✅ База данных удалена: {DATABASE_PATH}")
    else:
        print("ℹ️  База данных не существует")

    # Создаём новую базу
    print("\n🔨 Создание новой базы данных...")
    init_db()

    print("\n" + "=" * 60)
    print("✅ БАЗА ДАННЫХ УСПЕШНО ПЕРЕСОЗДАНА!")
    print("=" * 60)
    print(f"\n📂 Путь: {os.path.abspath(DATABASE_PATH)}")
    if backup_path:
        print(f"💾 Резервная копия: {backup_path}")
    print("\n💡 Заполните базу тестовыми данными:")
    print("   python seed_data.py")
    print("\n" + "=" * 60 + "\n")


def show_database_info():
    """Показывает информацию о текущем состоянии БД"""
    print("\n" + "=" * 60)
    print("📊 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ")
    print("=" * 60 + "\n")

    if not os.path.exists(DATABASE_PATH):
        print("❌ База данных не найдена!")
        print(f"   Путь: {os.path.abspath(DATABASE_PATH)}")
        print("\n💡 Создайте базу командой: python -c 'from database import init_db; init_db()'")
        print("=" * 60 + "\n")
        return

    file_size = os.path.getsize(DATABASE_PATH)
    print(f"📂 Путь: {os.path.abspath(DATABASE_PATH)}")
    print(f"💾 Размер: {file_size / 1024:.2f} KB")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()

        print(f"\n📋 Таблицы ({len(tables)}):")
        total_records = 0

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            print(f"\n   📌 {table_name}: {count} записей")
            print(f"      Колонки: {', '.join([col[1] for col in columns])}")

        print(f"\n📊 Всего записей в БД: {total_records}")

        # Специфичная статистика
        cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id IS NOT NULL")
        telegram_users = cursor.fetchone()[0]
        print(f"\n👥 Пользователи:")
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"   Всего: {cursor.fetchone()[0]}")
        print(f"   С Telegram: {telegram_users}")

        cursor.execute("SELECT COUNT(*) FROM courses")
        print(f"\n📚 Курсов: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM class_slots")
        print(f"📅 Занятий: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM participants")
        print(f"📝 Записей на занятия: {cursor.fetchone()[0]}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        conn.close()

    print("\n" + "=" * 60 + "\n")


def main():
    """Главное меню скрипта"""
    print("\n" + "=" * 60)
    print("🛠️  УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ")
    print("=" * 60)
    print("\nВыберите действие:")
    print("  1. 📊 Показать информацию о БД")
    print("  2. 🗑️  Очистить все данные (сохранить структуру)")
    print("  3. 🔄 Полностью пересоздать БД")
    print("  4. 🌱 Заполнить тестовыми данными")
    print("  5. 🚪 Выход")
    print("=" * 60)

    choice = input("\nВведите номер (1-5): ").strip()

    if choice == "1":
        show_database_info()

    elif choice == "2":
        print("\n⚠️  ВНИМАНИЕ: Все данные будут удалены!")
        confirm = input("Продолжить? (yes/no): ").strip().lower()
        if confirm in ["yes", "y", "да"]:
            backup_database()
            clear_all_data()
        else:
            print("❌ Операция отменена")

    elif choice == "3":
        print("\n⚠️  ВНИМАНИЕ: База данных будет полностью удалена и пересоздана!")
        confirm = input("Продолжить? (yes/no): ").strip().lower()
        if confirm in ["yes", "y", "да"]:
            reset_database()
        else:
            print("❌ Операция отменена")

    elif choice == "4":
        print("\n🌱 Запуск заполнения базы данных...")
        from seed_data import seed_database
        seed_database()

    elif choice == "5":
        print("\n👋 До свидания!")

    else:
        print("\n❌ Неверный выбор!")


if __name__ == "__main__":
    main()
