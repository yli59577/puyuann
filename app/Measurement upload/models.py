# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== SQLAlchemy 資料庫模型 ====================

class BloodPressureRecord(Base):
    """血壓測量記錄表"""
    __tablename__ = "blood_pressure_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    systolic = Column(Integer, nullable=False, comment="收縮壓")
    diastolic = Column(Integer, nullable=False, comment="舒張壓")
    pulse = Column(Integer, nullable=True, comment="脈搏")
    measured_at = Column(DateTime, nullable=False, comment="測量時間")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WeightRecord(Base):
    """體重測量記錄表"""
    __tablename__ = "weight_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    weight = Column(Float, nullable=False, comment="體重 (kg)")
    bmi = Column(Float, nullable=True, comment="BMI")
    body_fat = Column(Float, nullable=True, comment="體脂率 (%)")
    measured_at = Column(DateTime, nullable=False, comment="測量時間")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BloodSugarRecord(Base):
    """血糖測量記錄表"""
    __tablename__ = "blood_sugar_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    glucose = Column(Integer, nullable=False, comment="血糖值 (mg/dL)")
    meal_time = Column(Integer, nullable=False, comment="測量時段 (0:早上, 1:中午, 2:晚上)")
    measured_at = Column(DateTime, nullable=False, comment="測量時間")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class MeasurementRecord(Base):
    """通用測量記錄表 (用於記錄上傳)"""
    __tablename__ = "measurement_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    record_type = Column(Integer, nullable=False, comment="記錄類型 (0:血壓, 1:體重, 2:血糖)")
    record_id = Column(Integer, nullable=False, comment="對應記錄的 ID")
    uploaded_at = Column(DateTime, default=func.now(), comment="上傳時間")


# ==================== Pydantic 請求模型 ====================

class BloodPressureUpload(BaseModel):
    """上傳血壓測量結果"""
    systolic: int = Field(..., ge=50, le=250, description="收縮壓 (mmHg)")
    diastolic: int = Field(..., ge=30, le=150, description="舒張壓 (mmHg)")
    pulse: Optional[int] = Field(None, ge=30, le=200, description="脈搏 (次/分)")
    measured_at: str = Field(..., description="測量時間 (ISO 8601 格式)")


class WeightUpload(BaseModel):
    """上傳體重測量結果"""
    weight: float = Field(..., gt=0, le=500, description="體重 (kg)")
    bmi: Optional[float] = Field(None, ge=10, le=50, description="BMI")
    body_fat: Optional[float] = Field(None, ge=0, le=100, description="體脂率 (%)")
    measured_at: str = Field(..., description="測量時間 (ISO 8601 格式)")


class BloodSugarUpload(BaseModel):
    """上傳血糖測量結果"""
    glucose: int = Field(..., ge=20, le=600, description="血糖值 (mg/dL)")
    meal_time: int = Field(..., ge=0, le=2, description="測量時段 (0:早上, 1:中午, 2:晚上)")
    measured_at: str = Field(..., description="測量時間 (ISO 8601 格式)")


class RecordUpload(BaseModel):
    """上傳記錄"""
    record_type: int = Field(..., ge=0, le=2, description="記錄類型 (0:血壓, 1:體重, 2:血糖)")
    record_id: int = Field(..., gt=0, description="記錄 ID")


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class UploadResponse(BaseResponse):
    """上傳回應"""
    data: Optional[dict] = Field(None, description="回傳數據")


class LastUploadResponse(BaseResponse):
    """最後上傳時間回應"""
    last_upload_time: Optional[str] = Field(None, description="最後上傳時間")
