# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone, timedelta

# 定義台灣時區 UTC+8
TAIWAN_TZ = timezone(timedelta(hours=8))

def get_taiwan_time():
    """取得台灣時間 (UTC+8)，去除時區資訊儲存到資料庫"""
    return datetime.now(TAIWAN_TZ).replace(tzinfo=None)


# ==================== SQLAlchemy 資料庫模型 ====================

class User(Base):
    """用戶資料表 - 對應 UserAuth"""
    __tablename__ = "UserAuth"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=False)
    code = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    privacy_policy = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    login_token = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    token_expire_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_taiwan_time)
    updated_at = Column(DateTime, default=get_taiwan_time, onupdate=get_taiwan_time)


class VerificationCodeDB(Base):
    """驗證碼資料表"""
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, index=True, nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=get_taiwan_time)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)


# ==================== Pydantic 請求模型 ====================

class UserRegister(BaseModel):
    """用戶註冊請求"""
    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., min_length=6, description="密碼（至少6位）")


class UserLogin(BaseModel):
    """用戶登入請求"""
    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., description="密碼")


class PasswordReset(BaseModel):
    """重設密碼請求（需要舊密碼）"""
    oldPassword: str = Field(..., description="舊密碼")
    newPassword: str = Field(..., min_length=6, description="新密碼（至少6位）")


class PasswordForgot(BaseModel):
    """忘記密碼請求（符合規格書）"""
    email: EmailStr = Field(..., description="電子郵件")


class VerificationSend(BaseModel):
    """發送驗證碼請求"""
    email: EmailStr = Field(..., description="電子郵件")


class VerificationCheck(BaseModel):
    """檢查驗證碼請求"""
    email: EmailStr = Field(..., description="電子郵件")
    code: str = Field(..., description="驗證碼")


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應格式"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class RegisterResponse(BaseResponse):
    """註冊成功回應"""
    user_id: Optional[int] = Field(None, description="用戶 ID")


class TokenResponse(BaseModel):
    """登入成功回應（符合規格書）"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    token: Optional[str] = Field(None, description="JWT Token")
    message: Optional[str] = Field(None, description="訊息（僅失敗時返回）")


class VerificationSendResponse(BaseModel):
    """發送驗證碼成功回應（符合規格書欄位順序）"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    code: Optional[str] = Field(None, description="六位數驗證碼")
    message: str = Field(..., description="訊息")
