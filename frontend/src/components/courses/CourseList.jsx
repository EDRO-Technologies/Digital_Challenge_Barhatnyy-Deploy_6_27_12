import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAppContext } from '../../context/AppContext';
import './Courses.css'; // Оставляем для специфичных стилей, если есть

export default function CourseList({ apiUrl, onEdit, onCreateNew }) {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [searchQuery, setSearchQuery] = useState('');

    const {
        coursesCache,
        setCoursesCache,
        coursesCacheTime,
        setCoursesCacheTime,
        isCacheValid,
        invalidateCoursesCache,
    } = useAppContext();

    const loadCourses = useCallback(async () => {
        // Если есть валидный кэш и нет поиска - используем его
        if (!searchQuery && coursesCache && isCacheValid(coursesCacheTime)) {
            setCourses(coursesCache);
            return;
        }

        setLoading(true);
        setError('');
        try {
            const token = localStorage.getItem('token');
            const params = searchQuery ? { name: searchQuery } : {};

            const response = await axios.get(`${apiUrl}/api/courses`, {
                headers: { Authorization: `Bearer ${token}` },
                params,
                timeout: 5000,
            });

            setCourses(response.data);

            // Кэшируем если нет поиска
            if (!searchQuery) {
                setCoursesCache(response.data);
                setCoursesCacheTime(Date.now());
            }
        } catch (err) {
            if (err.response?.status === 401) {
                setError('Сессия истекла');
                localStorage.removeItem('token');
            } else {
                setError('Ошибка загрузки курсов');
            }
            console.error('Ошибка:', err.message);
        } finally {
            setLoading(false);
        }
    }, [apiUrl, searchQuery, coursesCache, coursesCacheTime, isCacheValid, setCoursesCache, setCoursesCacheTime]);

    useEffect(() => {
        const debounceTimer = setTimeout(() => {
            loadCourses();
        }, searchQuery ? 300 : 0);
        return () => clearTimeout(debounceTimer);
    }, [loadCourses, searchQuery]);

    const handleDelete = async (id) => {
        if (!window.confirm('Удалить курс?')) return;
        try {
            const token = localStorage.getItem('token');
            await axios.delete(`${apiUrl}/api/courses/${id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setCourses(courses.filter(c => c.id !== id));
            invalidateCoursesCache();
        } catch (err) {
            alert('Ошибка при удалении');
        }
    };

    return (
        <div className="container">
            <div className="page-header">
                <h2 className="page-title">Курсы и дисциплины</h2>
                <button className="btn btn-primary" onClick={onCreateNew}>
                    + Новый курс
                </button>
            </div>

            <div className="search-bar">
                <input
                    type="text"
                    placeholder="Поиск курса..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input" // Стиль input уже глобальный, но класс можно оставить для ширины
                />
            </div>

            {error && <div className="error-text">{error}</div>}

            {loading && !courses.length ? (
                <div className="loading-spinner"></div>
            ) : (
                <div className="grid-container">
                    {courses.map(course => (
                        <div key={course.id} className="card">
                            <h3 className="card-title">{course.name}</h3>
                            {course.description && <p className="card-text">{course.description}</p>}

                            <div className="card-text">
                                {course.teacher && (
                                    <span className="teacher">👨‍🏫 {course.teacher}</span>
                                )}
                                {course.semester && (
                                    <span className="semester">📅 Семестр {course.semester}</span>
                                )}
                            </div>

                            <div className="card-footer">
                                <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => onEdit(course)}
                                >
                                    Редактировать
                                </button>
                                <button
                                    className="btn btn-danger btn-sm"
                                    onClick={() => handleDelete(course.id)}
                                >
                                    Удалить
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {!loading && courses.length === 0 && (
                <div className="empty-state">Нет курсов</div>
            )}
        </div>
    );
}
