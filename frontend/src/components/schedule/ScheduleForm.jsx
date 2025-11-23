// Убрал useCallback из импорта
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import './Schedule.css';

export default function ScheduleForm({ apiUrl, entry, onClose, onSave }) {
    // ... весь остальной код остается тем же ...
    const [formData, setFormData] = useState({
        course_id: '',
        title: '',
        description: '',
        date_time: '',
        location: '',
        instructor: '',
        max_participants: '',
        direction: '',
        status: 'planned'
    });

    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    // --- Загрузка курсов ---
    useEffect(() => {
        const loadCourses = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`${apiUrl}/api/courses`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setCourses(response.data);
            } catch (err) {
                console.error("Ошибка загрузки курсов:", err);
            }
        };
        loadCourses();
    }, [apiUrl]);

    // ... (дальше код без изменений, см. предыдущий ответ) ...

    // --- Формируем список преподавателей ---
    const teachersList = useMemo(() => {
        const teachersFromCourses = courses
            .map(c => c.teacher)
            .filter(t => t && t.trim() !== '');

        const mockTeachers = [
            'Иванов И.И.',
            'Петров П.П.',
            'Сидорова А.А.',
            'Смирнов В.В.',
            'Кузнецова Е.Н.'
        ];

        return [...new Set([...teachersFromCourses, ...mockTeachers])].sort();
    }, [courses]);

    // ... (остальная часть файла идентична) ...
    useEffect(() => {
        if (entry) {
            let formattedDate = '';

            if (entry.date_time) {
                formattedDate = entry.date_time.includes('T')
                    ? entry.date_time.slice(0, 16)
                    : `${entry.date_time}T09:00`;
            }

            let defaultInstructor = entry.instructor || '';

            setFormData({
                course_id: entry.course_id ? String(entry.course_id) : '',
                title: entry.title || '',
                description: entry.description || '',
                date_time: formattedDate,
                location: entry.location || '',
                instructor: defaultInstructor,
                max_participants: entry.max_participants ? String(entry.max_participants) : '',
                direction: entry.direction || '',
                status: entry.status || 'planned'
            });
        }
    }, [entry]);

    const handleCourseChange = (e) => {
        const selectedId = e.target.value;
        const selectedCourse = courses.find(c => String(c.id) === selectedId);

        setFormData(prev => ({
            ...prev,
            course_id: selectedId,
            instructor: (!prev.instructor && selectedCourse?.teacher) ? selectedCourse.teacher : prev.instructor
        }));
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.course_id) newErrors.course_id = "Выберите курс";
        if (!formData.title.trim()) newErrors.title = "Название обязательно";
        if (!formData.date_time) newErrors.date_time = "Дата обязательно";
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validate()) return;

        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
            const finalDateTime = formData.date_time.length === 16 ? `${formData.date_time}:00` : formData.date_time;

            const payload = {
                course_id: parseInt(formData.course_id),
                title: formData.title,
                date_time: finalDateTime,
                description: formData.description || null,
                location: formData.location || null,
                instructor: formData.instructor || null,
                max_participants: formData.max_participants ? parseInt(formData.max_participants) : null,
                direction: formData.direction || null,
                status: formData.status
            };

            if (entry && entry.id && !entry.isNew) {
                await axios.put(`${apiUrl}/api/schedule/${entry.id}`, payload, { headers });
            } else {
                await axios.post(`${apiUrl}/api/schedule`, payload, { headers });
            }
            onSave();
        } catch (err) {
            alert("Ошибка сохранения: " + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h2 className="modal-title">{entry && entry.id && !entry.isNew ? 'Редактировать' : 'Новое занятие'}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Курс *</label>
                        <select
                            name="course_id"
                            value={formData.course_id}
                            onChange={handleCourseChange}
                            className={errors.course_id ? 'input-error' : ''}
                        >
                            <option value="">Выберите курс...</option>
                            {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                        </select>
                        {errors.course_id && <span className="error-text">{errors.course_id}</span>}
                    </div>

                    <div className="form-group">
                        <label>Тема занятия *</label>
                        <input type="text" name="title" value={formData.title} onChange={handleChange} className={errors.title ? 'input-error' : ''} />
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Дата и время *</label>
                            <input type="datetime-local" name="date_time" value={formData.date_time} onChange={handleChange} className={errors.date_time ? 'input-error' : ''} />
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Статус</label>
                            <select name="status" value={formData.status} onChange={handleChange}>
                                <option value="planned">Запланировано</option>
                                <option value="confirmed">Подтверждено</option>
                                <option value="moved">Перенесено</option>
                                <option value="cancelled">Отменено</option>
                                <option value="finished">Завершено</option>
                            </select>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                        <div className="form-group" style={{flex:1}}>
                            <label>Место / Ауд.</label>
                            <input type="text" name="location" value={formData.location} onChange={handleChange} placeholder="Ауд. 101" />
                        </div>
                        <div className="form-group" style={{flex:1}}>
                            <label>Преподаватель</label>
                            <select name="instructor" value={formData.instructor} onChange={handleChange}>
                                <option value="">Не выбран</option>
                                {teachersList.map((t, idx) => (
                                    <option key={idx} value={t}>{t}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '12px' }}>
                        <div className="form-group" style={{flex:1}}>
                            <label>Направление</label>
                            <input type="text" name="direction" value={formData.direction} onChange={handleChange} placeholder="Frontend" />
                        </div>
                        <div className="form-group" style={{ width: '100px' }}>
                            <label>Мест</label>
                            <input type="number" name="max_participants" value={formData.max_participants} onChange={handleChange} placeholder="30" />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Описание</label>
                        <textarea name="description" value={formData.description} onChange={handleChange} rows="2" />
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>Отмена</button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Сохранение...' : 'Сохранить'}</button>
                    </div>
                </form>
            </div>
        </div>
    );
}
