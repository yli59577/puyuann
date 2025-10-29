# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==================== Pydantic 請求模型 ====================

class A1cUpload(BaseModel):
    """上傳糖化血色素請求"""
    a1c: str = Field(..., description="糖化血色素")
    recorded_at: str = Field(..., description="記錄時間 (格式: YYYY-MM-DD HH:MM:SS)")


class A1cDeleteRequest(BaseModel):
    """刪除糖化血色素請求"""
    ids: List[int] = Field(..., description="糖化血色素 ID 列表", alias="ids[]")
    
    class Config:
        populate_by_name = True


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class A1cRecord(BaseModel):
    """糖化血色素記錄"""
    id: int
    a1c: str
    recorded_at: str
    updated_at: str
    created_at: str
    user_id: int

    class Config:
        from_attributes = True


class A1cListResponse(BaseResponse):
    """獲取糖化血色素列表回應"""
    a1cs: List[A1cRecord] = Field(default=[], description="糖化血色素記錄列表")
