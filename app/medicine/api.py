# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app._user.module import UserModule

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

@router.get("/medical", summary="獲取就醫資訊", tags=["就醫、藥物資訊"])
def get_medical_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的就醫資訊
    """
    authorization = f"Bearer {credentials.credentials}"
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        # 返回預設物件而非 None，避免 Swift 解析失敗
        return {
            "status": "1", 
            "message": "authentication failed", 
            "medical_info": {
                "id": 0,
                "user_id": 0,
                "oad": 0,
                "insulin": 0,
                "anti_hypertensives": 0,
                "diabetes_type": 0,
                "created_at": "",
                "updated_at": ""
            }
        }
    
    medical_info = MedicineModule.get_medical_info(user_id=user_id)
    
    if medical_info:
        return {
            "status": "0", 
            "message": "ok", 
            "medical_info": {
                "id": medical_info.id,
                "user_id": medical_info.user_id,
                "oad": medical_info.oad,
                "insulin": medical_info.insulin,
                "anti_hypertensives": medical_info.anti_hypertensives,
                "diabetes_type": medical_info.diabetes_type,
                "created_at": medical_info.created_at,
                "updated_at": medical_info.updated_at
            }
        }
    else:
        # 返回預設物件而非 None，避免 Swift 解析失敗
        return {
            "status": "0", 
            "message": "ok", 
            "medical_info": {
                "id": 0,
                "user_id": user_id,
                "oad": 0,
                "insulin": 0,
                "anti_hypertensives": 0,
                "diabetes_type": 0,
                "created_at": "",
                "updated_at": ""
            }
        }


@router.patch("/medical", response_model=BaseResponse, summary="更新就醫資訊", tags=["就醫、藥物資訊"])
def update_medical_info(
    request: MedicalInfoUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    更新用戶的就醫資訊
    """
    authorization = f"Bearer {credentials.credentials}"
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="authentication failed")
    
    success = MedicineModule.update_medical_info(
        user_id=user_id,
        oad=request.oad,
        insulin=request.insulin,
        anti_hypertensives=request.anti_hypertensives,
        diabetes_type=request.diabetes_type
    )
    
    if success:
        return BaseResponse(status="0", message="success")
    else:
        return BaseResponse(status="1", message="failed")


@router.get("/drug-used", response_model=DrugUsedListResponse, summary="獲取所有藥物資訊", tags=["就醫、藥物資訊"])
def get_drug_used_list(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的所有藥物資訊
    """
    authorization = f"Bearer {credentials.credentials}"
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return DrugUsedListResponse(status="1", message="authentication failed", drug_useds=[])
    
    drug_useds = MedicineModule.get_drug_used_list(user_id=user_id)
    
    if drug_useds is not None:
        return DrugUsedListResponse(status="0", message="ok", drug_useds=drug_useds)
    else:
        return DrugUsedListResponse(status="1", message="failed", drug_useds=[])


@router.post("/drug-used", response_model=BaseResponse, summary="上傳藥物資訊", tags=["就醫、藥物資訊"])
def upload_drug_used(
    request: DrugUsedUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳藥物資訊
    """
    authorization = f"Bearer {credentials.credentials}"
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="authentication failed")
    
    success = MedicineModule.upload_drug_used(
        user_id=user_id,
        drug_type=request.type,
        name=request.name,
        recorded_at=request.recorded_at
    )
    
    if success:
        return BaseResponse(status="0", message="success")
    else:
        return BaseResponse(status="1", message="failed")


@router.delete("/drug-used", response_model=BaseResponse, summary="刪除藥物資訊", tags=["就醫、藥物資訊"])
def delete_drug_used(
    request: DrugUsedDeleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    刪除藥物資訊
    """
    authorization = f"Bearer {credentials.credentials}"
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="authentication failed")
    
    success = MedicineModule.delete_drug_used_records(
        user_id=user_id,
        ids=request.ids
    )
    
    if success:
        return BaseResponse(status="0", message="ok")
    else:
        return BaseResponse(status="1", message="failed")
