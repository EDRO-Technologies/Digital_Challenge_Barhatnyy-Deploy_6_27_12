from datetime import datetime, timedelta, timezone
import jwt
import hashlib
from database import get_db
from fastapi import Response

# Настройки безопасности
SECRET_KEY = "your-secret-key-change-in-production-12345"  # Измени в продакшене!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней


def hash_password(password: str) -> str:
    """
    Хеширование пароля с использованием SHA-256
    Простой и надёжный способ без зависимостей
    """
    # Используем SHA-256 с солью
    salt = "hackaton-salt-2024"  # В продакшене генерируй случайную соль для каждого пользователя
    password_with_salt = password + salt
    return hashlib.sha256(password_with_salt.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return hash_password(plain_password) == hashed_password


def create_access_token(data: dict) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def set_auth_cookie(response: Response, token: str):
    """Установка cookie с токеном"""
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )


def create_user(email: str, password: str, full_name: str) -> int:
    """Создание нового пользователя"""
    with get_db() as conn:
        cursor = conn.cursor()
        password_hash = hash_password(password)

        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
            (email, password_hash, full_name)
        )
        return cursor.lastrowid


def get_user_by_email(email: str):
    """Получение пользователя по email"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, full_name FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            return {
                "id": user[0],
                "email": user[1],
                "password_hash": user[2],
                "full_name": user[3]
            }
        return None


def get_user_by_id(user_id: int):
    """Получение пользователя по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            return {
                "id": user[0],
                "email": user[1],
                "full_name": user[2]
            }
        return None
