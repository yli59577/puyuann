from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.core.database import Base

# 定義台灣時區 UTC+8
TAIWAN_TZ = timezone(timedelta(hours=8))

def get_taiwan_time():
    """取得台灣時間 (UTC+8)，去除時區資訊儲存到資料庫"""
    return datetime.now(TAIWAN_TZ).replace(tzinfo=None)

Base = declarative_base()

# --- SQLAlchemy 資料庫模型 ---

class User(Base):
    """用戶資料表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class VerificationCodeDB(Base):
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=get_taiwan_time)
    is_used = Column(Boolean, default=False)  # 確保初始值為 False

class UserDefaults(Base):
    __tablename__ = "user_defaults"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sugar_morning_max = Column(Integer, default=0)
    sugar_morning_min = Column(Integer, default=0)
    sugar_evening_max = Column(Integer, default=0)
    sugar_evening_min = Column(Integer, default=0)
    sugar_before_max = Column(Integer, default=0)
    sugar_before_min = Column(Integer, default=0)
    sugar_after_max = Column(Integer, default=0)
    sugar_after_min = Column(Integer, default=0)
    systolic_max = Column(Integer, default=0)
    systolic_min = Column(Integer, default=0)
    diastolic_max = Column(Integer, default=0)
    diastolic_min = Column(Integer, default=0)
    pulse_max = Column(Integer, default=0)
    pulse_min = Column(Integer, default=0)
    weight_max = Column(Integer, default=0)
    weight_min = Column(Integer, default=0)
    bmi_max = Column(Float, default=0.0)
    bmi_min = Column(Float, default=0.0)
    body_fat_max = Column(Float, default=0.0)
    body_fat_min = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    after_recording = Column(Boolean, default=False)
    no_recording_for_a_day = Column(Boolean, default=False)
    over_max_or_under_min = Column(Boolean, default=False)
    after_meal = Column(Boolean, default=False)
    unit_of_sugar = Column(Boolean, default=False)
    unit_of_weight = Column(Boolean, default=False)
    unit_of_height = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    fcm_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    birthday = Column(String, nullable=True)
    gender = Column(Boolean, nullable=True)
    address = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# --- Pydantic API 模型 ---

class BaseResponse(BaseModel):
    """基本回應格式"""
    status: str
    message: str

class UserCreate(BaseModel):
    """用戶註冊請求"""
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """用戶登入請求"""
    email: EmailStr
    password: str

class VerificationBase(BaseModel):
    """發送驗證碼請求"""
    email: EmailStr

class VerificationCode(VerificationBase):
    """檢查驗證碼請求"""
    code: str

class VerificationSendResponse(BaseResponse):
    """發送驗證碼成功回應"""
    code: str

class TokenResponse(BaseModel):
    """登入成功回應"""
    status: str
    token: str

class PasswordReset(BaseModel):
    """重設密碼請求"""
    oldPassword: str
    newPassword: str

class PasswordForgot(BaseModel):
    """忘記密碼請求"""
    email: EmailStr

class VerificationCodeResponse(BaseModel):
    """驗證碼詳細回應"""
    id: int
    email: str
    code: str
    created_at: str
    is_used: bool
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """用戶資訊回應"""
    id: int
    email: str
    is_active: bool
    
    class Config:
        from_attributes = True