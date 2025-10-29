# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==================== Pydantic 請求模型 ====================

class MedicalInfoUpdate(BaseModel):
    """更新就醫資訊請求"""
    oad: int = Field(..., description="糖尿病口服藥 (0:否, 1:是)")
    insulin: int = Field(..., description="胰島素 (0:否, 1:是)")
    anti_hypertensives: int = Field(..., description="高血壓藥 (0:否, 1:是)")
    diabetes_type: int = Field(..., ge=0, le=4, description="糖尿病類型 (0:無, 1:糖尿病前期, 2:第一型, 3:第二型, 4:妊娠)")


class DrugUsedUpload(BaseModel):
    """上傳藥物資訊請求"""
    type: int = Field(..., description="使用藥物類型 (0:糖尿病藥物, 1:高血壓藥物)")
    name: str = Field(..., description="藥物名稱")
    recorded_at: str = Field(..., description="記錄時間 (格式: YYYY-MM-DD HH:MM:SS)")


class DrugUsedDeleteRequest(BaseModel):
    """刪除藥物資訊請求"""
    ids: List[int] = Field(..., description="藥物資訊 ID 列表", alias="ids[]")
    
    class Config:
        populate_by_name = True


# ==================== Pydantic 回應模型 ====================

class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="狀態碼 (0:成功, 1:失敗)")
    message: str = Field(..., description="訊息")


class MedicalInfo(BaseModel):
    """就醫資訊"""
    id: int
    user_id: int
    oad: int
    insulin: int
    anti_hypertensives: int
    diabetes_type: int
    updated_at: str
    created_at: str

    class Config:
        from_attributes = True


class MedicalInfoResponse(BaseResponse):
    """獲取就醫資訊回應"""
    medical_info: Optional[MedicalInfo] = Field(None, description="就醫資訊")


class DrugUsedRecord(BaseModel):
    """藥物資訊記錄"""
    id: int
    name: str
    type: int
    recorded_at: str
    updated_at: str
    created_at: str
    user_id: int

    class Config:
        from_attributes = True


class DrugUsedListResponse(BaseResponse):
    """獲取藥物資訊列表回應"""
    drug_useds: List[DrugUsedRecord] = Field(default=[], description="藥物資訊列表")
