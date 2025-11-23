import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import './Schedule.css';

const getMonthName = (date) => {
    return date.toLocaleString('ru-RU', { month: 'long', year: 'numeric' });
};

const isSameDay = (d1, d2) => {
    return d1.getFullYear() === d2.getFullYear() &&
        d1.getMonth() === d2.getMonth() &&
        d1.getDate() === d2.getDate();
};

// --- ИСПРАВЛЕНИЕ: Функция для получения строки даты без сдвига UTC ---
const getLocalDateString = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

export default function ScheduleCalendar({ apiUrl, onEdit, onCreateNew }) {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);

    const calendarDays = useMemo(() => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        const firstDayOfMonth = new Date(year, month, 1);
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        let startDayOfWeek = firstDayOfMonth.getDay() - 1;
        if (startDayOfWeek === -1) startDayOfWeek = 6;

        const daysArray = [];

        const prevMonthLastDay = new Date(year, month, 0).getDate();
        for (let i = startDayOfWeek - 1; i >= 0; i--) {
            daysArray.push({
                date: new Date(year, month - 1, prevMonthLastDay - i),
                isCurrentMonth: false
            });
        }

        for (let i = 1; i <= daysInMonth; i++) {
            daysArray.push({
                date: new Date(year, month, i),
                isCurrentMonth: true
            });
        }

        const remainingCells = 42 - daysArray.length;
        for (let i = 1; i <= remainingCells; i++) {
            daysArray.push({
                date: new Date(year, month + 1, i),
                isCurrentMonth: false
            });
        }

        return daysArray;
    }, [currentDate]);

    useEffect(() => {
        const fetchSchedule = async () => {
            setLoading(true);
            try {
                // Используем безопасную функцию
                const startStr = getLocalDateString(calendarDays[0].date);
                const endStr = getLocalDateString(calendarDays[calendarDays.length - 1].date);

                const token = localStorage.getItem('token');
                const response = await axios.get(`${apiUrl}/api/schedule`, {
                    headers: { Authorization: `Bearer ${token}` },
                    params: { date_from: startStr, date_to: endStr }
                });
                setEvents(response.data);
            } catch (error) {
                console.error("Ошибка загрузки расписания:", error);
            } finally {
                setLoading(false);
            }
        };

        if (calendarDays.length > 0) {
            fetchSchedule();
        }
    }, [apiUrl, currentDate, calendarDays]);

    const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    const goToday = () => setCurrentDate(new Date());

    return (
        <div className="container">
            <div className="calendar-header-controls">
                <div className="month-title">
                    {getMonthName(currentDate)}
                </div>
                <div className="nav-buttons">
                    <button className="btn btn-secondary btn-sm" onClick={prevMonth}>&lt;</button>
                    <button className="btn btn-secondary btn-sm" onClick={goToday}>Сегодня</button>
                    <button className="btn btn-secondary btn-sm" onClick={nextMonth}>&gt;</button>
                </div>
            </div>

            <div className="calendar-grid-header">
                {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(d => (
                    <div key={d} className="weekday-label">{d}</div>
                ))}
            </div>

            <div className="calendar-grid">
                {calendarDays.map((dayObj, index) => {
                    const isToday = isSameDay(dayObj.date, new Date());
                    // ИСПОЛЬЗУЕМ БЕЗОПАСНУЮ СТРОКУ
                    const dayDateStr = getLocalDateString(dayObj.date);

                    const dayEvents = events.filter(e => {
                        // Сравниваем строки (предполагаем, что с бэка тоже приходит YYYY-MM-DD часть в начале)
                        return e.date_time.startsWith(dayDateStr);
                    }).sort((a, b) => a.date_time.localeCompare(b.date_time));

                    return (
                        <div
                            key={index}
                            className={`calendar-cell ${!dayObj.isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                            onClick={() => onCreateNew(dayDateStr)}
                        >
                            <div className="cell-header">
                                <span className="day-number">{dayObj.date.getDate()}</span>
                                {isToday && <span className="today-marker">•</span>}
                            </div>

                            <div className="events-list">
                                {dayEvents.map(event => (
                                    <div
                                        key={event.id}
                                        className="event-chip"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onEdit(event);
                                        }}
                                        title={`${event.date_time.slice(11,16)} - ${event.title}`}
                                    >
                                        <span className="event-time">{event.date_time.slice(11,16)}</span>
                                        <span className="event-title">{event.title}</span>
                                    </div>
                                ))}
                            </div>

                            <button className="add-btn-overlay">+</button>
                        </div>
                    );
                })}
            </div>

            {loading && <div className="loading-overlay">Обновление...</div>}
        </div>
    );
}
