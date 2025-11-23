import React, { useState, useEffect, useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import './Dashboard.css';
// Подключите глобальные стили кнопок, если они в App.css

// Импорт компонентов
import CourseList from './courses/CourseList';
import CourseForm from './courses/CourseForm';
import ScheduleList from './schedule/ScheduleList';
import ScheduleForm from './schedule/ScheduleForm';
import ScheduleCalendar from './schedule/ScheduleCalendar';
import ParticipantList from './participants/ParticipantList';
import ParticipantForm from './participants/ParticipantForm';

export default function Dashboard({ user, onLogout, apiUrl }) {
    // --- UI State ---
    const [activeTab, setActiveTab] = useState('calendar');

    // --- Courses State ---
    const [showCourseForm, setShowCourseForm] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    const [courseRefreshKey, setCourseRefreshKey] = useState(0);

    // --- Schedule State ---
    const [showScheduleForm, setShowScheduleForm] = useState(false);
    const [editingSchedule, setEditingSchedule] = useState(null);
    const [scheduleRefreshKey, setScheduleRefreshKey] = useState(0);

    // --- Participants State ---
    const [participants, setParticipants] = useState([]);
    const [showParticipantForm, setShowParticipantForm] = useState(false);
    const [editingParticipant, setEditingParticipant] = useState(null);

    // Хардкод курса для MVP (в реале можно брать из селекта или URL)
    const currentCourseId = "1";

    const { invalidateCoursesCache } = useAppContext();

    // ==========================
    // HANDLERS: PARTICIPANTS
    // ==========================
    const loadParticipants = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${apiUrl}/api/courses/${currentCourseId}/participants`, {
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
            if (response.ok) {
                const data = await response.json();
                setParticipants(data);
            }
        } catch (error) {
            console.error("Error loading participants:", error);
        }
    }, [apiUrl, currentCourseId]);

    useEffect(() => {
        if (activeTab === 'participants') {
            loadParticipants();
        }
    }, [activeTab, loadParticipants]);

    const handleEditParticipant = (user) => {
        setEditingParticipant(user);
        setShowParticipantForm(true);
    };

    const handleCancelParticipant = () => {
        setShowParticipantForm(false);
        setEditingParticipant(null);
    };

    const handleSaveParticipant = async (formData) => {
        try {
            const token = localStorage.getItem('token');
            const headers = {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            };

            if (editingParticipant) {
                // Update
                await fetch(`${apiUrl}/api/participants/${editingParticipant.id}`, {
                    method: 'PUT',
                    headers: headers,
                    body: JSON.stringify(formData)
                });
            } else {
                // Create
                await fetch(`${apiUrl}/api/courses/${currentCourseId}/participants`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(formData)
                });
            }
            // Close & Refresh
            setShowParticipantForm(false);
            setEditingParticipant(null);
            loadParticipants();
        } catch (error) {
            console.error("Error saving participant:", error);
            alert("Ошибка сохранения");
        }
    };

    // ==========================
    // HANDLERS: COURSES / SCHEDULE
    // ==========================

    const handleCreateCourse = () => {
        setEditingCourse(null);
        setShowCourseForm(true);
    };

    const handleEditCourse = (course) => {
        setEditingCourse(course);
        setShowCourseForm(true);
    };

    const handleCloseCourseForm = () => {
        setShowCourseForm(false);
        setEditingCourse(null);
    };

    const handleSaveCourse = () => {
        invalidateCoursesCache();
        setCourseRefreshKey(p => p + 1);
        handleCloseCourseForm();
    };

    // --- ИЗМЕНЕНО: Принимаем initialDate (строка YYYY-MM-DD) ---
    const handleCreateSchedule = (initialDate = null) => {
        if (initialDate) {
            // Если дата передана, создаем объект-заготовку с предустановленным временем
            // Ставим время по умолчанию, например 09:00
            const defaultTime = `${initialDate}T09:00:00`;
            setEditingSchedule({
                isNew: true, // Флаг что это новый объект
                date_time: defaultTime
            });
        } else {
            setEditingSchedule(null);
        }
        setShowScheduleForm(true);
    };

    const handleEditSchedule = (entry) => {
        setEditingSchedule(entry);
        setShowScheduleForm(true);
    };

    const handleCloseScheduleForm = () => {
        setShowScheduleForm(false);
        setEditingSchedule(null);
    };

    const handleSaveSchedule = () => {
        setScheduleRefreshKey(p => p + 1);
        handleCloseScheduleForm();
    };

    return (
        <div className="app-dashboard">
            {/* Навигационная панель (упрощенная) */}
            <nav className="dashboard-nav">
                <div className="nav-brand">Умное Расписание</div>
                <div className="nav-links">
                    <button
                        className={`nav-link ${activeTab === 'calendar' ? 'active' : ''}`}
                        onClick={() => setActiveTab('calendar')}
                    >
                        Календарь
                    </button>
                    <button
                        className={`nav-link ${activeTab === 'list' ? 'active' : ''}`}
                        onClick={() => setActiveTab('list')}
                    >
                        Список занятий
                    </button>
                    <button
                        className={`nav-link ${activeTab === 'courses' ? 'active' : ''}`}
                        onClick={() => setActiveTab('courses')}
                    >
                        Курсы
                    </button>
                    <button
                        className={`nav-link ${activeTab === 'participants' ? 'active' : ''}`}
                        onClick={() => setActiveTab('participants')}
                    >
                        Участники
                    </button>
                </div>
                <div className="user-menu">
                    <span>{user?.email}</span>
                    <button className="btn btn-secondary btn-sm" onClick={onLogout}>Выйти</button>
                </div>
            </nav>

            <main className="dashboard-content">
                {/* Вкладка: КАЛЕНДАРЬ */}
                {activeTab === 'calendar' && (
                    <ScheduleCalendar
                        key={scheduleRefreshKey}
                        apiUrl={apiUrl}
                        onEdit={handleEditSchedule}
                        onCreateNew={handleCreateSchedule} // Передаем функцию, которая принимает дату
                    />
                )}

                {/* Вкладка: СПИСОК ЗАНЯТИЙ */}
                {activeTab === 'list' && (
                    <ScheduleList
                        key={scheduleRefreshKey}
                        apiUrl={apiUrl}
                        onEdit={handleEditSchedule}
                        onCreateNew={() => handleCreateSchedule(null)}
                    />
                )}

                {/* Вкладка: КУРСЫ */}
                {activeTab === 'courses' && (
                    <CourseList
                        key={courseRefreshKey}
                        apiUrl={apiUrl}
                        onEdit={handleEditCourse}
                        onCreateNew={handleCreateCourse}
                    />
                )}

                {/* Вкладка: УЧАСТНИКИ */}
                {activeTab === 'participants' && (
                    <ParticipantList
                        participants={participants} // Можно переделать ParticipantList чтобы он принимал массив
                        apiUrl={apiUrl}
                        courseId={currentCourseId}
                        onEdit={handleEditParticipant}
                    />
                )}
            </main>

            {/* --- МОДАЛЬНЫЕ ОКНА --- */}

            {showCourseForm && (
                <CourseForm
                    apiUrl={apiUrl}
                    course={editingCourse}
                    onClose={handleCloseCourseForm}
                    onSave={handleSaveCourse}
                />
            )}

            {showScheduleForm && (
                <ScheduleForm
                    apiUrl={apiUrl}
                    entry={editingSchedule} // Здесь будет лежать объект с date_time если мы кликнули по календарю
                    onClose={handleCloseScheduleForm}
                    onSave={handleSaveSchedule}
                />
            )}

            {showParticipantForm && (
                <ParticipantForm
                    participant={editingParticipant}
                    onClose={handleCancelParticipant}
                    onSave={handleSaveParticipant}
                />
            )}
        </div>
    );
}
