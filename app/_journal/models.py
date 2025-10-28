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
    id: Any  # 可以是 int 或 str,因為飲食記錄使用 UUID 字串
    user_id: int
    systolic: Optional[int] = 0
    diastolic: Optional[int] = 0
    pulse: Optional[int] = 0
    weight: Optional[float] = 0.0
    body_fat: Optional[float] = 0.0
    bmi: Optional[float] = 0.0
    sugar: Optional[float] = 0.0  # 改為 float 以符合規格書
    exercise: Optional[int] = 0
    drug: Optional[int] = 0
    timeperiod: Optional[int] = 0
    description: Optional[str] = ""
    meal: Optional[int] = None
    tag: Optional[List[Dict[str, Any]]] = []
    image: Optional[List[str]] = []
    location: Optional[Dict[str, str]] = None
    reply: Optional[str] = ""
    recorded_at: str
    type: str  # blood_pressure, blood_sugar, weight, diet

    class Config:
        from_attributes = True


class DiaryListResponse(BaseResponse):
    """獲取日記列表回應"""
    diary: List[DiaryRecord] = Field(default=[], description="日記記錄列表")
