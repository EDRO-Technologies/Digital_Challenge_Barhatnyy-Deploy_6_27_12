import React, { useState, useMemo } from 'react';
import './Participants.css'; // Убедитесь, что этот файл пустой или содержит только специфику

// Компонент аватара с инициалами
const UserAvatar = ({ name }) => {
    const getInitials = (n) => {
        return n ? n.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() : '??';
    };

    // Генерация цвета на основе имени
    const getColor = (n) => {
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
        let hash = 0;
        for (let i = 0; i < n.length; i++) {
            hash = n.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
    };

    return (
        <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: getColor(name || ''),
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            fontWeight: '600',
            marginRight: '12px'
        }}>
            {getInitials(name)}
        </div>
    );
};

export default function ParticipantList({ participants, apiUrl, courseId, onEdit }) {
    const [searchQuery, setSearchQuery] = useState('');

    // Фильтрация на клиенте (так быстрее для списков < 1000 человек)
    const filteredParticipants = useMemo(() => {
        if (!participants) return [];
        return participants.filter(p =>
            p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            p.email.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }, [participants, searchQuery]);

    const handleDelete = async (id) => {
        if(!window.confirm('Удалить участника?')) return;
        // Логика удаления должна быть передана из Dashboard или вызвана здесь
        // Для простоты пока алерт, так как пропс onDelete не передан, но можно добавить
        try {
            const token = localStorage.getItem('token');
            await fetch(`${apiUrl}/api/participants/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            // Тут нужен коллбек на обновление списка, например onRefresh()
            alert('Участник удален (обновите страницу)');
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="container">
            <div className="page-header">
                <div>
                    <h2 className="page-title">Участники</h2>
                    <div style={{ fontSize: '14px', color: '#b3b6be', marginTop: '4px' }}>
                        Всего: {participants?.length || 0} чел.
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '12px', flex: 1, justifyContent: 'flex-end', maxWidth: '500px' }}>
                    <input
                        type="text"
                        placeholder="Поиск по имени или email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="search-input"
                        style={{ width: '100%' }}
                    />
                    <button
                        className="btn btn-primary"
                        onClick={() => onEdit(null)} // null означает создание нового
                    >
                        + Добавить
                    </button>
                </div>
            </div>

            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.02)' }}>
                        <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 600 }}>ИМЯ</th>
                        <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 600 }}>КОНТАКТЫ</th>
                        <th style={{ padding: '16px 24px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 600, textAlign: 'right' }}>ДЕЙСТВИЯ</th>
                    </tr>
                    </thead>
                    <tbody>
                    {filteredParticipants.length > 0 ? (
                        filteredParticipants.map(user => (
                            <tr
                                key={user.id}
                                style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }}
                                className="table-row-hover" // можно добавить ховер эффект в CSS
                            >
                                <td style={{ padding: '16px 24px', display: 'flex', alignItems: 'center' }}>
                                    <UserAvatar name={user.name} />
                                    <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>{user.name}</span>
                                </td>
                                <td style={{ padding: '16px 24px' }}>
                                    <div style={{ fontSize: '14px', color: 'var(--text-main)' }}>{user.email}</div>
                                    {user.telegram && (
                                        <div style={{ fontSize: '13px', color: '#3b82f6', marginTop: '2px' }}>
                                            {user.telegram}
                                        </div>
                                    )}
                                </td>
                                <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        style={{ marginRight: '8px' }}
                                        onClick={() => onEdit(user)}
                                    >
                                        ✏️
                                    </button>
                                    <button
                                        className="btn btn-danger btn-sm"
                                        onClick={() => handleDelete(user.id)}
                                    >
                                        🗑️
                                    </button>
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="3" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                {searchQuery ? 'Ничего не найдено' : 'Список пуст'}
                            </td>
                        </tr>
                    )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
