import React, { createContext, useContext, useState, useCallback } from 'react';

const AppContext = createContext();

// Константа вне компонента (не изменяется)
const CACHE_TIMEOUT = 5 * 60 * 1000; // 5 минут

export function AppProvider({ children }) {
    // Кэш для курсов
    const [coursesCache, setCoursesCache] = useState(null);
    const [coursesCacheTime, setCoursesCacheTime] = useState(null);

    // Кэш для расписания
    const [scheduleCache, setScheduleCache] = useState({});
    const [scheduleCacheTime, setScheduleCacheTime] = useState({});

    const invalidateCoursesCache = useCallback(() => {
        setCoursesCache(null);
        setCoursesCacheTime(null);
    }, []);

    const invalidateScheduleCache = useCallback((dateKey) => {
        setScheduleCache(prev => {
            const newCache = { ...prev };
            delete newCache[dateKey];
            return newCache;
        });
        setScheduleCacheTime(prev => {
            const newTime = { ...prev };
            delete newTime[dateKey];
            return newTime;
        });
    }, []);

    const isCacheValid = useCallback((cacheTime) => {
        if (!cacheTime) return false;
        return Date.now() - cacheTime < CACHE_TIMEOUT;
    }, []); // CACHE_TIMEOUT теперь константа вне компонента

    return (
        <AppContext.Provider
            value={{
                coursesCache,
                setCoursesCache,
                coursesCacheTime,
                setCoursesCacheTime,
                scheduleCache,
                setScheduleCache,
                scheduleCacheTime,
                setScheduleCacheTime,
                invalidateCoursesCache,
                invalidateScheduleCache,
                isCacheValid,
                CACHE_TIMEOUT,
            }}
        >
            {children}
        </AppContext.Provider>
    );
}

export function useAppContext() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext должен быть использован внутри AppProvider');
    }
    return context;
}
