import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './Schedule.css';

export default function ScheduleList({ apiUrl, onEdit, onCreateNew, refreshTrigger }) {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterDate, setFilterDate] = useState('');

    const loadSchedule = useCallback(async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const params = {};
            if (filterDate) params.date_from = filterDate;

            const response = await axios.get(`${apiUrl}/api/schedule`, {
                headers: { Authorization: `Bearer ${token}` },
                params,
            });

            const sortedData = response.data.sort((a, b) =>
                new Date(a.date_time) - new Date(b.date_time)
            );
            setEntries(sortedData);
        } catch (err) {
            console.error('Ошибка загрузки расписания');
        } finally {
            setLoading(false);
        }
    }, [apiUrl, filterDate]);

    // ВАЖНО: Добавляем refreshTrigger в зависимости
    useEffect(() => {
        loadSchedule();
    }, [loadSchedule, refreshTrigger]); // <-- Теперь перезапросит при изменении refreshTrigger

    const handleDelete = async (id) => {
        if (!window.confirm('Удалить занятие?')) return;
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${apiUrl}/api/schedule/${id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setEntries(entries.filter(e => e.id !== id));
        } catch (err) {
            alert('Ошибка при удалении');
        }
    };

    const formatDateTime = (isoString) => {
        if (!isoString) return '';
        const date = new Date(isoString);
        return date.toLocaleString('ru-RU', {
            day: 'numeric',
            month: 'long',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusBadge = (status) => {
        const badges = {
            planned: { text: 'Запланировано', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' },
            confirmed: { text: 'Подтверждено', color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)' },
            moved: { text: 'Перенесено', color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)' },
            cancelled: { text: 'Отменено', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },
            finished: { text: 'Завершено', color: '#b3b6be', bg: 'rgba(255, 255, 255, 0.05)' },
        };

        const badge = badges[status] || badges.planned;

        return (
            <span style={{
                color: badge.color,
                background: badge.bg,
                border: `1px solid ${badge.color}`,
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '600',
                whiteSpace: 'nowrap'
            }}>
        {badge.text}
      </span>
        );
    };

    return (
        <div className="container">
            <div className="page-header">
                <h2 className="page-title">Список занятий</h2>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <input
                        type="date"
                        value={filterDate}
                        onChange={(e) => setFilterDate(e.target.value)}
                        style={{ width: 'auto' }}
                    />
                    <button className="btn btn-primary" onClick={onCreateNew}>
                        + Занятие
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="loading-spinner"></div>
            ) : (
                <div className="schedule-list">
                    {entries.length === 0 ? (
                        <div className="empty-state">Нет занятий</div>
                    ) : (
                        entries.map(entry => (
                            <div key={entry.id} className="schedule-row card" style={{ opacity: entry.status === 'cancelled' ? 0.7 : 1 }}>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: '13px', color: '#3b82f6', fontWeight: 600, marginBottom: '4px' }}>
                                        {formatDateTime(entry.date_time)}
                                    </div>
                                    <h4 className="card-title" style={{
                                        fontSize: '18px',
                                        marginBottom: '8px',
                                        textDecoration: entry.status === 'cancelled' ? 'line-through' : 'none'
                                    }}>
                                        {entry.title}
                                    </h4>

                                    <div className="card-text" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                                        {entry.instructor && <span>👨‍🏫 {entry.instructor}</span>}
                                        {entry.location && <span>📍 {entry.location}</span>}
                                        {entry.direction && <span>🏷️ {entry.direction}</span>}
                                    </div>

                                    {entry.description && (
                                        <div className="card-text" style={{ marginTop: '8px', fontStyle: 'italic', color: '#b3b6be' }}>
                                            {entry.description}
                                        </div>
                                    )}
                                </div>

                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '12px' }}>
                                    {getStatusBadge(entry.status)}
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button className="btn btn-secondary btn-sm" onClick={() => onEdit(entry)}>✏️</button>
                                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(entry.id)}>🗑️</button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
