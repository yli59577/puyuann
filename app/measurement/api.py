# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import Optional
import sys
import os



# 使用相對導入
from . import models as measurement_models
from . import module as measurement_module

# 導入需要的類別
BloodPressureUpload = measurement_models.BloodPressureUpload
WeightUpload = measurement_models.WeightUpload
BloodSugarUpload = measurement_models.BloodSugarUpload
RecordUpload = measurement_models.RecordUpload
BaseResponse = measurement_models.BaseResponse
UploadResponse = measurement_models.UploadResponse
LastUploadResponse = measurement_models.LastUploadResponse
MeasurementModule = measurement_module.MeasurementModule

router = APIRouter()
security = HTTPBearer()

# ==================== 測量上傳 ====================

@router.post("/blood/pressure/", response_model=UploadResponse, summary="上傳血壓測量結果", tags=["測量上傳"])
def upload_blood_pressure(
    request: BloodPressureUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳血壓測量結果
    
    - **需要 Bearer Token**
    - **systolic**: 收縮壓 (mmHg), 範圍 50-250
    - **diastolic**: 舒張壓 (mmHg), 範圍 30-150
    - **pulse**: 脈搏 (次/分), 範圍 30-200, 可選
    - **measured_at**: 測量時間 (ISO 8601 格式)
    
    ### 範例請求
    ```json
    {
        "systolic": 120,
        "diastolic": 80,
        "pulse": 72,
        "measured_at": "2025-01-27T10:30:00Z"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MeasurementModule.parse_user_id_from_token(authorization)
    if not user_id:
        return UploadResponse(status="1", message="身份驗證失敗", data=None)
    
    # 2. 檢查用戶是否存在
    user = MeasurementModule.get_user(db, user_id)
    if not user:
        return UploadResponse(status="1", message="用戶不存在", data=None)
    
    # 3. 上傳血壓記錄
    record_id = MeasurementModule.upload_blood_pressure(
        db=db,
        user_id=user_id,
        systolic=request.systolic,
        diastolic=request.diastolic,
        pulse=request.pulse,
        measured_at=request.measured_at
    )
    
    if record_id:
        return UploadResponse(
            status="0", 
            message="上傳成功",
            data={"record_id": record_id}
        )
    else:
        return UploadResponse(status="1", message="上傳失敗", data=None)


@router.post("/weight", response_model=UploadResponse, summary="上傳體重測量結果", tags=["測量上傳"])
def upload_weight(
    request: WeightUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳體重測量結果
    
    - **需要 Bearer Token**
    - **weight**: 體重 (kg), 範圍 > 0
    - **bmi**: BMI, 範圍 10-50, 可選
    - **body_fat**: 體脂率 (%), 範圍 0-100, 可選
    - **measured_at**: 測量時間 (ISO 8601 格式)
    
    ### 範例請求
    ```json
    {
        "weight": 70.5,
        "bmi": 22.3,
        "body_fat": 18.5,
        "measured_at": "2025-01-27T10:30:00Z"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MeasurementModule.parse_user_id_from_token(authorization)
    if not user_id:
        return UploadResponse(status="1", message="身份驗證失敗", data=None)
    
    # 2. 檢查用戶是否存在
    user = MeasurementModule.get_user(db, user_id)
    if not user:
        return UploadResponse(status="1", message="用戶不存在", data=None)
    
    # 3. 上傳體重記錄
    record_id = MeasurementModule.upload_weight(
        db=db,
        user_id=user_id,
        weight=request.weight,
        bmi=request.bmi,
        body_fat=request.body_fat,
        measured_at=request.measured_at
    )
    
    if record_id:
        return UploadResponse(
            status="0", 
            message="上傳成功",
            data={"record_id": record_id}
        )
    else:
        return UploadResponse(status="1", message="上傳失敗", data=None)


@router.post("/blood/sugar", response_model=UploadResponse, summary="上傳血糖測量結果", tags=["測量上傳"])
def upload_blood_sugar(
    request: BloodSugarUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳血糖測量結果
    
    - **需要 Bearer Token**
    - **glucose**: 血糖值 (mg/dL), 範圍 20-600
    - **meal_time**: 測量時段 (0:早上, 1:中午, 2:晚上)
    - **measured_at**: 測量時間 (ISO 8601 格式)
    
    ### 範例請求
    ```json
    {
        "glucose": 95,
        "meal_time": 0,
        "measured_at": "2025-01-27T10:30:00Z"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MeasurementModule.parse_user_id_from_token(authorization)
    if not user_id:
        return UploadResponse(status="1", message="身份驗證失敗", data=None)
    
    # 2. 檢查用戶是否存在
    user = MeasurementModule.get_user(db, user_id)
    if not user:
        return UploadResponse(status="1", message="用戶不存在", data=None)
    
    # 3. 上傳血糖記錄
    record_id = MeasurementModule.upload_blood_sugar(
        db=db,
        user_id=user_id,
        glucose=request.glucose,
        meal_time=request.meal_time,
        measured_at=request.measured_at
    )
    
    if record_id:
        return UploadResponse(
            status="0", 
            message="上傳成功",
            data={"record_id": record_id}
        )
    else:
        return UploadResponse(status="1", message="上傳失敗", data=None)


@router.get("/last-upload", response_model=LastUploadResponse, summary="最後上傳時間", tags=["測量上傳"])
def get_last_upload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取最後上傳時間
    
    - **需要 Bearer Token**
    - **回傳**: 最後一次上傳測量記錄的時間
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MeasurementModule.parse_user_id_from_token(authorization)
    if not user_id:
        return LastUploadResponse(status="1", message="身份驗證失敗", last_upload_time=None)
    
    # 2. 檢查用戶是否存在
    user = MeasurementModule.get_user(db, user_id)
    if not user:
        return LastUploadResponse(status="1", message="用戶不存在", last_upload_time=None)
    
    # 3. 查詢最後上傳時間
    last_time = MeasurementModule.get_last_upload_time(db, user_id)
    
    if last_time:
        return LastUploadResponse(status="0", message="成功", last_upload_time=last_time)
    else:
        return LastUploadResponse(status="0", message="尚無上傳記錄", last_upload_time=None)


@router.post("/records", response_model=BaseResponse, summary="上傳一筆記錄", tags=["測量上傳"])
def upload_record(
    request: RecordUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳一筆記錄
    
    - **需要 Bearer Token**
    - **record_type**: 記錄類型 (0:血壓, 1:體重, 2:血糖)
    - **record_id**: 記錄 ID (必須 > 0)
    
    ### 範例請求
    ```json
    {
        "record_type": 0,
        "record_id": 123
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MeasurementModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 檢查用戶是否存在
    user = MeasurementModule.get_user(db, user_id)
    if not user:
        return BaseResponse(status="1", message="用戶不存在")
    
    # 3. 創建記錄
    success = MeasurementModule.create_measurement_record(
        db=db,
        user_id=user_id,
        record_type=request.record_type,
        record_id=request.record_id
    )
    
    if success:
        return BaseResponse(status="0", message="上傳成功")
    else:
        return BaseResponse(status="1", message="上傳失敗")
