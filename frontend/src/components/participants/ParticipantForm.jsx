import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function ParticipantForm({ participant, onClose, onSave }) {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        telegram: '',
        chatId: '',
        course_id: ''
    });
    const [errors, setErrors] = useState({});
    const [courses, setCourses] = useState([]);
    const [loadingCourses, setLoadingCourses] = useState(true);

    useEffect(() => {
        fetchCourses();

        if (participant) {
            setFormData({
                name: participant.name || '',
                email: participant.email || '',
                telegram: participant.telegram || '',
                chatId: participant.telegram || '',
                course_id: participant.course_id || ''
            });
        }
    }, [participant]);

    const fetchCourses = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/courses');
            setCourses(response.data);
            console.log('✅ Загружено курсов:', response.data.length);
        } catch (error) {
            console.error('❌ Ошибка загрузки курсов:', error);
        } finally {
            setLoadingCourses(false);
        }
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.name.trim()) newErrors.name = "Имя обязательно";
        if (!formData.email.trim()) newErrors.email = "Email обязателен";

        if (formData.chatId && !formData.chatId.match(/^-?\d+$/)) {
            newErrors.chatId = "Chat ID должен быть числом";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!validate()) return;

        // Формируем данные для отправки
        const dataToSend = {
            name: formData.name,
            email: formData.email,
            telegram: formData.chatId || formData.telegram,
            chatId: formData.chatId,
            course_id: formData.course_id ? parseInt(formData.course_id) : null
        };

        console.log('📋 Отправка данных формы:', dataToSend);
        onSave(dataToSend);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h2 className="modal-title">
                    {participant ? 'Редактировать' : 'Новый участник'}
                </h2>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>ФИО Студента *</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            className={errors.name ? 'input-error' : ''}
                            placeholder="Иванов Иван Иванович"
                        />
                        {errors.name && <span className="error-text">{errors.name}</span>}
                    </div>

                    <div className="form-group">
                        <label>Email *</label>
                        <input
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({...formData, email: e.target.value})}
                            className={errors.email ? 'input-error' : ''}
                            placeholder="student@example.com"
                        />
                        {errors.email && <span className="error-text">{errors.email}</span>}
                    </div>

                    <div className="form-group">
                        <label>Telegram</label>
                        <div style={{ position: 'relative' }}>
                            <span style={{ position: 'absolute', left: '12px', top: '12px', color: '#b3b6be' }}>@</span>
                            <input
                                type="text"
                                value={formData.telegram.replace('@', '')}
                                onChange={(e) => setFormData({...formData, telegram: '@' + e.target.value.replace('@', '')})}
                                style={{ paddingLeft: '28px' }}
                                placeholder="username"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>🤖 Telegram Chat ID</label>
                        <input
                            type="text"
                            value={formData.chatId}
                            onChange={(e) => setFormData({...formData, chatId: e.target.value})}
                            className={errors.chatId ? 'input-error' : ''}
                            placeholder="123456789"
                        />
                        {errors.chatId && <span className="error-text">{errors.chatId}</span>}
                        <small style={{ display: 'block', marginTop: '5px', color: '#666', fontSize: '12px' }}>
                            Узнать Chat ID: напишите @userinfobot в Telegram или нашему боту /my_id
                        </small>
                    </div>

                    <div className="form-group">
                        <label>📚 Курс {formData.course_id && '(выбран)'}</label>
                        <select
                            value={formData.course_id}
                            onChange={(e) => setFormData({...formData, course_id: e.target.value})}
                            disabled={loadingCourses}
                            style={{
                                backgroundColor: formData.course_id ? '#e3f2fd' : 'white',
                                borderColor: formData.course_id ? '#2196F3' : '#ddd'
                            }}
                        >
                            <option value="">Без курса (можно добавить позже)</option>
                            {courses.map(course => (
                                <option key={course.id} value={course.id}>
                                    {course.name}
                                    {course.instructor && ` — ${course.instructor}`}
                                </option>
                            ))}
                        </select>
                        {loadingCourses && (
                            <small style={{ display: 'block', marginTop: '5px', color: '#666', fontSize: '12px' }}>
                                ⏳ Загрузка курсов...
                            </small>
                        )}
                        {formData.course_id && (
                            <small style={{ display: 'block', marginTop: '5px', color: '#1976d2', fontSize: '12px', fontWeight: '500' }}>
                                ✅ Участник будет добавлен на все занятия этого курса и получит Telegram уведомления
                            </small>
                        )}
                    </div>

                    <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={onClose}>
                            Отмена
                        </button>
                        <button type="submit" className="btn btn-primary">
                            {formData.course_id ? '💾 Сохранить и добавить к курсу' : '💾 Сохранить'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
