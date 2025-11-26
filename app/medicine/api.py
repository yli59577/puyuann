# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db

# 導入模型和模組
from .models import (
    MedicalInfoUpdate,
    DrugUsedUpload,
    DrugUsedDeleteRequest,
    BaseResponse,
    MedicalInfoResponse,
    DrugUsedListResponse
)
from .module import MedicineModule

router = APIRouter()
security = HTTPBearer()

# ==================== 就醫、藥物資訊 ====================

@router.get("/medical", response_model=MedicalInfoResponse, summary="獲取就醫資訊", tags=["就醫、藥物資訊"])
def get_medical_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的就醫資訊
    
    - **需要 Bearer Token**
    
    ### 回傳內容
    - **medical_info**: 就醫資訊物件
      - oad: 糖尿病口服藥 (0:否, 1:是)
      - insulin: 胰島素 (0:否, 1:是)
      - anti_hypertensives: 高血壓藥 (0:否, 1:是)
      - diabetes_type: 糖尿病類型 (0:無, 1:糖尿病前期, 2:第一型, 3:第二型, 4:妊娠)
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MedicineModule.parse_user_id_from_token(authorization)
    if not user_id:
        return MedicalInfoResponse(status="1", message="身份驗證失敗", medical_info=None)
    
    # 2. 查詢就醫資訊
    medical_info = MedicineModule.get_medical_info(user_id=user_id)
    
    if medical_info:
        return MedicalInfoResponse(status="0", message="ok", medical_info=medical_info)
    else:
        return MedicalInfoResponse(status="1", message="失敗", medical_info=None)


@router.patch("/medical", response_model=BaseResponse, summary="更新就醫資訊", tags=["就醫、藥物資訊"])
def update_medical_info(
    request: MedicalInfoUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    更新用戶的就醫資訊
    
    - **需要 Bearer Token**
    - **oad**: 糖尿病口服藥 (0:否, 1:是)
    - **insulin**: 胰島素 (0:否, 1:是)
    - **anti_hypertensives**: 高血壓藥 (0:否, 1:是)
    - **diabetes_type**: 糖尿病類型 (0:無, 1:糖尿病前期, 2:第一型, 3:第二型, 4:妊娠)
    
    ### 範例請求
    ```json
    {
        "oad": 1,
        "insulin": 0,
        "anti_hypertensives": 1,
        "diabetes_type": 1
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MedicineModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 更新就醫資訊
    success = MedicineModule.update_medical_info(
        user_id=user_id,
        oad=request.oad,
        insulin=request.insulin,
        anti_hypertensives=request.anti_hypertensives,
        diabetes_type=request.diabetes_type
    )
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.get("/drug-used", response_model=DrugUsedListResponse, summary="獲取所有藥物資訊", tags=["就醫、藥物資訊"])
def get_drug_used_list(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的所有藥物資訊
    
    - **需要 Bearer Token**
    
    ### 回傳內容
    - **drug_useds**: 藥物資訊列表
      - id: 記錄 ID
      - name: 藥物名稱
      - type: 藥物類型 (0:糖尿病藥物, 1:高血壓藥物)
      - recorded_at: 記錄時間
      - created_at: 建立時間
      - updated_at: 更新時間
      - user_id: 用戶 ID
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MedicineModule.parse_user_id_from_token(authorization)
    if not user_id:
        return DrugUsedListResponse(status="1", message="身份驗證失敗", drug_useds=[])
    
    # 2. 查詢藥物資訊
    drug_useds = MedicineModule.get_drug_used_list(user_id=user_id)
    
    if drug_useds is not None:
        return DrugUsedListResponse(status="0", message="ok", drug_useds=drug_useds)
    else:
        return DrugUsedListResponse(status="1", message="失敗", drug_useds=[])


@router.post("/drug-used", response_model=BaseResponse, summary="上傳藥物資訊", tags=["就醫、藥物資訊"])
def upload_drug_used(
    request: DrugUsedUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳藥物資訊
    
    - **需要 Bearer Token**
    - **type**: 使用藥物類型 (0:糖尿病藥物, 1:高血壓藥物)
    - **name**: 藥物名稱
    - **recorded_at**: 記錄時間 (格式: YYYY-MM-DD HH:MM:SS)
    
    ### 範例請求
    ```json
    {
        "type": 1,
        "name": "F-medical",
        "recorded_at": "2017-11-21 21:32:17"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MedicineModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 上傳藥物資訊
    success = MedicineModule.upload_drug_used(
        user_id=user_id,
        drug_type=request.type,
        name=request.name,
        recorded_at=request.recorded_at
    )
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.delete("/drug-used", response_model=BaseResponse, summary="刪除藥物資訊", tags=["就醫、藥物資訊"])
def delete_drug_used(
    request: DrugUsedDeleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    刪除藥物資訊
    
    - **需要 Bearer Token**
    - **ids[]**: 要刪除的藥物資訊記錄 ID 列表
    
    ### 範例請求
    ```json
    {
        "ids[]": [52]
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = MedicineModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 刪除藥物資訊
    success = MedicineModule.delete_drug_used_records(
        user_id=user_id,
        ids=request.ids
    )
    
    if success:
        return BaseResponse(status="0", message="ok")
    else:
        return BaseResponse(status="1", message="失敗")
