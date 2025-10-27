# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== SQLAlchemy 資料庫模型 ====================

class UserProfile(Base):
    """用戶個人資料表"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    fcm_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    birthday = Column(String, nullable=True)
    gender = Column(Integer, nullable=True)  # 0: 女, 1: 男
    address = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserDefaults(Base):
    """用戶預設值表"""
    __tablename__ = "user_defaults"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    sugar_morning_max = Column(Integer, default=0)
    sugar_morning_min = Column(Integer, default=0)
    sugar_afternoon_max = Column(Integer, default=0)
    sugar_afternoon_min = Column(Integer, default=0)
    sugar_evening_max = Column(Integer, default=0)
    sugar_evening_min = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserSettings(Base):
    """用戶設定表"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    after_recording = Column(Boolean, default=False)
    no_recording_for_a_day = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=True)
    language = Column(String, default="zh-TW")
    theme = Column(String, default="light")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ==================== Pydantic 請求模型 ====================

class UserProfileUpdate(BaseModel):
    """更新用戶個人資料請求"""
    fcm_id: Optional[str] = Field(None, description="Firebase Cloud Messaging ID")
    name: Optional[str] = Field(None, description="姓名")
    birthday: Optional[str] = Field(None, description="生日 (YYYY-MM-DD)")
    gender: Optional[int] = Field(None, ge=0, le=1, description="性別 (0:女, 1:男)")
    address: Optional[str] = Field(None, description="地址")
    weight: Optional[float] = Field(None, gt=0, description="體重 (kg)")
    height: Optional[float] = Field(None, gt=0, description="身高 (cm)")
    phone: Optional[str] = Field(None, description="電話")
    avatar: Optional[str] = Field(None, description="頭像 URL")


class UserDefaultsUpdate(BaseModel):
    """更新用戶預設值請求"""
    sugar_morning_max: Optional[int] = Field(None, description="早上血糖最大值")
    sugar_morning_min: Optional[int] = Field(None, description="早上血糖最小值")
    sugar_afternoon_max: Optional[int] = Field(None, description="下午血糖最大值")
    sugar_afternoon_min: Optional[int] = Field(None, description="下午血糖最小值")
    sugar_evening_max: Optional[int] = Field(None, description="晚上血糖最大值")
    sugar_evening_min: Optional[int] = Field(None, description="晚上血糖最小值")


class UserSettingsUpdate(BaseModel):
    """更新用戶設定請求"""
    after_recording: Optional[bool] = Field(None, description="記錄後通知")
    no_recording_for_a_day: Optional[bool] = Field(None, description="一天未記錄通知")
    notification_enabled: Optional[bool] = Field(None, description="啟用通知")
    language: Optional[str] = Field(None, description="語言")
    theme: Optional[str] = Field(None, description="主題")


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class UserProfileResponse(BaseResponse):
    """用戶資料回應"""
    data: Optional[dict] = Field(None, description="用戶資料")