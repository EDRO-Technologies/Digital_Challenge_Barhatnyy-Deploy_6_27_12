import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useAppContext } from '../../context/AppContext';
import './Courses.css';

export default function CourseForm({ apiUrl, course, onClose, onSave }) {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        teacher: '',
        semester: '',
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const { invalidateCoursesCache } = useAppContext();

    // --- Список преподавателей (Mock) ---
    // В будущем заменить на загрузку с API
    const teachersList = useMemo(() => {
        return [
            'Иванов И.И.',
            'Петров П.П.',
            'Сидорова А.А.',
            'Смирнов В.В.',
            'Кузнецова Е.Н.',
            'Васильев А.Б.',
            'Попова М.С.'
        ].sort();
    }, []);

    useEffect(() => {
        if (course) {
            setFormData({
                name: course.name || '',
                description: course.description || '',
                teacher: course.teacher || '',
                semester: course.semester ? String(course.semester) : '',
            });
        }
    }, [course]);

    const validate = () => {
        const newErrors = {};
        if (!formData.name.trim()) {
            newErrors.name = 'Название обязательно';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validate()) return;

        setLoading(true);
        setErrors({});

        try {
            const token = localStorage.getItem('token');

            const payload = {
                name: formData.name.trim(),
                description: formData.description.trim() || null,
                teacher: formData.teacher.trim() || null,
                semester: formData.semester ? parseInt(formData.semester, 10) : null,
            };

            // Удаляем пустые поля
            const cleanPayload = Object.fromEntries(
                Object.entries(payload).filter(([_, value]) => value !== null && value !== '')
            );

            const config = {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                timeout: 5000,
            };

            if (course) {
                await axios.put(`${apiUrl}/api/courses/${course.id}`, cleanPayload, config);
            } else {
                await axios.post(`${apiUrl}/api/courses`, cleanPayload, config);
            }

            invalidateCoursesCache();
            if (onSave) onSave();
            onClose();
        } catch (err) {
            let message = 'Ошибка соединения с сервером';
            if (err.response?.data?.detail) {
                message = typeof err.response.data.detail === 'string'
                    ? err.response.data.detail
                    : 'Ошибка при сохранении курса';
            }
            setErrors({ submit: message });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        if (errors[name]) {
            setErrors(prev => {
                const newErrors = { ...prev };
                delete newErrors[name];
                return newErrors;
            });
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h2 className="modal-title">
                    {course ? 'Редактировать курс' : 'Новый курс'}
                </h2>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Название курса *</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            className={errors.name ? 'input-error' : ''}
                            placeholder="Например: Высшая математика"
                        />
                        {errors.name && <span className="error-text">{errors.name}</span>}
                    </div>

                    {/* --- ИЗМЕНЕНО: Select вместо Input --- */}
                    <div className="form-group">
                        <label>Преподаватель</label>
                        <select
                            name="teacher"
                            value={formData.teacher}
                            onChange={handleChange}
                        >
                            <option value="">Выберите преподавателя...</option>
                            {teachersList.map((t, idx) => (
                                <option key={idx} value={t}>{t}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Семестр</label>
                        <input
                            type="number"
                            name="semester"
                            value={formData.semester}
                            onChange={handleChange}
                            placeholder="1-8"
                            min="1"
                            max="12"
                        />
                    </div>

                    <div className="form-group">
                        <label>Описание</label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            rows="3"
                            placeholder="Краткое описание дисциплины..."
                        />
                    </div>

                    {errors.submit && (
                        <div className="form-group error-text" style={{textAlign: 'center'}}>
                            {errors.submit}
                        </div>
                    )}

                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Отмена
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? 'Сохранение...' : 'Сохранить'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
