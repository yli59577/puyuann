# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Union, Any
from datetime import datetime, date

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
    invite_code = Column(String, nullable=True)
    badge = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserDefaults(Base):
    """用戶預設值表"""
    __tablename__ = "user_defaults"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    sugar_delta_min = Column(Float, nullable=True)
    sugar_delta_max = Column(Float, nullable=True)
    sugar_morning_min = Column(Float, nullable=True)
    sugar_morning_max = Column(Float, nullable=True)
    sugar_evening_min = Column(Float, nullable=True)
    sugar_evening_max = Column(Float, nullable=True)
    sugar_before_min = Column(Float, nullable=True)
    sugar_before_max = Column(Float, nullable=True)
    sugar_after_min = Column(Float, nullable=True)
    sugar_after_max = Column(Float, nullable=True)
    systolic_min = Column(Integer, nullable=True)
    systolic_max = Column(Integer, nullable=True)
    diastolic_min = Column(Integer, nullable=True)
    diastolic_max = Column(Integer, nullable=True)
    pulse_min = Column(Integer, nullable=True)
    pulse_max = Column(Integer, nullable=True)
    weight_min = Column(Float, nullable=True)
    weight_max = Column(Float, nullable=True)
    bmi_min = Column(Float, nullable=True)
    bmi_max = Column(Float, nullable=True)
    body_fat_min = Column(Float, nullable=True)
    body_fat_max = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserSettings(Base):
    """用戶個人設定表"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    after_recording = Column(Boolean, default=False)
    no_recording_for_a_day = Column(Boolean, default=False)
    over_max_or_under_min = Column(Boolean, default=False)
    after_meal = Column(Boolean, default=False)
    unit_of_sugar = Column(Boolean, default=False)
    unit_of_weight = Column(Boolean, default=False)
    unit_of_height = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# ==================== Pydantic 資料驗證模型 ====================

class UserProfileData(BaseModel):
    """API 回應的用戶完整資料結構 - 根據規格書與前端需求調整"""
    id: int
    account: Optional[str] = ""
    email: Optional[EmailStr] = ""
    phone: Optional[str] = ""
    name: Optional[str] = ""
    gender: Optional[int] = 0
    birthday: Optional[str] = ""
    height: Optional[float] = 0.0
    weight: Optional[float] = 0.0
    verified: int = 0  # 改為 int 類型 (0 或 1)
    privacy_policy: int = 0  # 改為 int 類型 (0 或 1)
    must_change_password: int = 0  # 改為 int 類型 (0 或 1)
    fcm_id: Optional[str] = ""
    fb_id: Optional[str] = ""
    google_id: Optional[str] = ""
    apple_id: Optional[str] = ""
    login_times: int = 0
    address: Optional[str] = ""
    invite_code: Optional[str] = ""
    badge: int = 0
    # 根據前端需求保留，即使規格書不明確
    avatar: Optional[str] = ""
    # 根據前端需求保留，即使規格書不明確
    group: Optional[str] = ""
    # 根據前端需求保留
    unread_records: List[int] = []
    # 根據前端需求保留
    status: str = "0"
    # VIP 狀態對象
    vip: Optional[dict] = None
    # App 需要的時間戳欄位
    created_at: Optional[str] = ""
    updated_at: Optional[str] = ""
    # App 需要的預設值欄位
    default: Optional[dict] = None
    # App 需要的設定欄位
    setting: Optional[dict] = None

class UserProfileUpdate(BaseModel):
    """更新個人資料的請求"""
    name: Optional[str] = None
    gender: Optional[int] = None
    birthday: Optional[Any] = None  # 接受任何類型（字串、日期、空值）
    height: Optional[Any] = None  # 接受任何類型（字串、數字、空值）
    weight: Optional[Any] = None  # 接受任何類型（字串、數字、空值）
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    fcm_id: Optional[str] = None

class UserSettingsUpdate(BaseModel):
    """更新個人設定的請求"""
    after_recording: Optional[bool] = None
    no_recording_for_a_day: Optional[bool] = None
    notification_enabled: Optional[bool] = Field(None, alias="over_max_or_under_min")
    language: Optional[str] = None
    theme: Optional[str] = None

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: Optional[str] = Field(None, description="回應訊息")


class UserProfileResponse(BaseModel):
    """獲取個人資料的回應，包含在 'user' 鍵中"""
    status: str = "0"
    message: str = "成功"
    user: Optional[UserProfileData] = None