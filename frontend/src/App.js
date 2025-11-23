import React, { useState, useEffect } from 'react';
import { AppProvider } from './context/AppContext';
import { ToastProvider } from './context/ToastContext';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
    const [user, setUser] = useState(null);
    const [view, setView] = useState('login');

    // Лучше вынести в .env, но для хакатона сойдет
    const API_URL = 'http://localhost:8000';

    useEffect(() => {
        // При загрузке восстанавливаем сессию
        const storedUser = localStorage.getItem('user');
        const storedToken = localStorage.getItem('token');

        if (storedUser && storedToken) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                // Если JSON битый, чистим все
                handleLogout();
            }
        }
    }, []);

    const handleLoginSuccess = (token, userData) => {
        // 1. Сохраняем токен
        localStorage.setItem('token', token);

        // 2. Сохраняем юзера
        localStorage.setItem('user', JSON.stringify(userData));

        // 3. Обновляем стейт
        setUser(userData);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setView('login');
    };

    return (
        <AppProvider>
            <ToastProvider>
                <div className="app-container">
                    {!user ? (
                        view === 'login' ? (
                            <Login
                                apiUrl={API_URL}
                                onSuccess={handleLoginSuccess} // Передаем нашу функцию-обертку
                                onSwitchToRegister={() => setView('register')}
                            />
                        ) : (
                            <Register
                                apiUrl={API_URL}
                                onSuccess={() => setView('login')}
                                onSwitchToLogin={() => setView('login')}
                            />
                        )
                    ) : (
                        <Dashboard
                            user={user}
                            onLogout={handleLogout}
                            apiUrl={API_URL}
                        />
                    )}
                </div>
            </ToastProvider>
        </AppProvider>
    );
}

export default App;
