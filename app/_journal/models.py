# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==================== Pydantic 請求模型 ====================

class DietUpload(BaseModel):
    """上傳飲食日記請求"""
    description: str = Field(..., description="描述")
    meal: int = Field(..., ge=0, le=2, description="時段 (0:早餐, 1:午餐, 2:晚餐)")
    tag: List[str] = Field(default=[], description="標籤列表", alias="tag[]")
    image: int = Field(0, ge=0, description="照片數量")
    lat: Optional[float] = Field(None, description="緯度")
    lng: Optional[float] = Field(None, description="經度")
    recorded_at: str = Field(..., description="記錄時間")

    class Config:
        populate_by_name = True


class DeleteRecordsRequest(BaseModel):
    """刪除日記記錄請求"""
    deleteObject: Dict[str, List[int]] = Field(..., description="要刪除的記錄 ID")


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class DietUploadResponse(BaseResponse):
    """上傳飲食日記回應"""
    image_url: Optional[str] = Field(None, description="圖片網址")


class DiaryRecord(BaseModel):
    """日記記錄"""
    id: int = 0  # Swift 期望 Int，不能是 null
    user_id: int = 0
    systolic: int = 0
    diastolic: int = 0
    pulse: int = 0
    weight: float = 0.0
    body_fat: float = 0.0
    bmi: float = 0.0
    sugar: float = 0.0
    exercise: int = 0
    drug: int = 0
    timeperiod: int = 0
    description: str = ""
    meal: int = 0  # Swift 期望 Int，不能是 null
    tag: List[Dict[str, Any]] = []
    image: List[str] = []
    location: Dict[str, str] = {"lat": "0", "lng": "0"}  # Swift 期望 Dictionary，不能是 null
    reply: str = ""
    recorded_at: str = ""
    type: str = ""  # blood_pressure, blood_sugar, weight, diet

    class Config:
        from_attributes = True


class DiaryListResponse(BaseResponse):
    """獲取日記列表回應"""
    diary: List[DiaryRecord] = Field(default=[], description="日記記錄列表")
