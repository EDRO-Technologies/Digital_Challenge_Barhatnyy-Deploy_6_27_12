import openpyxl
from typing import List, Dict
import re

# Сопоставление дней недели
DAY_MAPPING = {
    'ПН': 1, 'пн': 1,
    'ВТ': 2, 'вт': 2,
    'СР': 3, 'ср': 3,
    'ЧТ': 4, 'чт': 4,
    'ПТ': 5, 'пт': 5,
    'СБ': 6, 'сб': 6,
    'ВС': 7, 'вс': 7
}

# Приблизительное время пар (для наглядности)
PAIR_TIMES = {
    1: "08:30-10:00",
    2: "10:10-11:40",
    3: "11:50-13:20",
    4: "13:40-15:10",
    5: "15:20-16:50",
    6: "17:00-18:30",
    7: "18:40-20:10",
    8: "20:20-21:50"
}


def parse_excel_schedule(file_path: str) -> List[Dict]:
    """
    Парсинг реального Excel файла с расписанием СурГУ
    Возвращает список занятий
    """
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active

    schedule_entries = []
    current_course = None  # переименовано из current_group
    current_day = None

    # Паттерны для извлечения данных
    course_pattern = re.compile(r'(\d{3}-\d{2}м?)')  # 606-51, 603-51м и т.д.

    for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        # Пропускаем пустые строки
        if not row or not any(row):
            continue

        first_cell = str(row[0] or '').strip()

        # Ищем название курса
        course_match = course_pattern.search(first_cell)
        if course_match or ('курс' in first_cell.lower()):
            current_course = first_cell
            continue

        # Ищем день недели
        if first_cell in DAY_MAPPING:
            current_day = DAY_MAPPING[first_cell]
            continue

        # Обрабатываем строку с предметом
        if current_course and current_day and len(row) >= 4:
            try:
                pair_num = int(row[0]) if row[0] and str(row[0]).isdigit() else None
                subject = str(row[1] or '').strip()
                teacher = str(row[2] or '').strip()
                room = str(row[3] or '').strip()

                if not subject or subject == '-':
                    continue

                time_slot = PAIR_TIMES.get(pair_num, "00:00-00:00")

                schedule_entries.append({
                    'course_name': current_course,  # переименовано из group_name
                    'day_of_week': current_day,
                    'time_slot': time_slot,
                    'subject': subject,
                    'teacher': teacher if teacher else None,
                    'room': room if room else None
                })

            except Exception as e:
                print(f"⚠️  Ошибка в строке {row_idx}: {e}")
                continue

    return schedule_entries
