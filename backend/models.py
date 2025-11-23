from pydantic import BaseModel, EmailStr
from typing import Optional

# ========== AUTH MODELS ==========

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    telegram_id: Optional[str] = None

# ========== PARTICIPANT MODELS ==========

class ParticipantCreate(BaseModel):
    name: str
    email: EmailStr
    telegram: Optional[str] = None
    class_slot_id: Optional[int] = None
    course_id: Optional[int] = None
    status: str = "active"

class ParticipantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    telegram: Optional[str] = None
    status: Optional[str] = None

class ParticipantResponse(BaseModel):
    id: int
    name: str
    email: str
    telegram: Optional[str] = None
    status: str

# ========== COURSE MODELS ==========

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instructor: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    instructor: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# ========== SLOT MODELS ==========

class ClassSlotCreate(BaseModel):
    course_id: int
    title: str
    date_time: str
    location: Optional[str] = None
    instructor: Optional[str] = None
    max_participants: Optional[int] = None
    status: str = "scheduled"

class ClassSlotUpdate(BaseModel):
    title: Optional[str] = None
    date_time: Optional[str] = None
    location: Optional[str] = None
    instructor: Optional[str] = None
    max_participants: Optional[int] = None
    status: Optional[str] = None

class ClassSlotResponse(BaseModel):
    id: int
    course_id: int
    title: str
    date_time: str
    location: Optional[str] = None
    instructor: Optional[str] = None
    max_participants: Optional[int] = None
    status: str
