# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db

# 導入模型和模組
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import (
    A1cUpload,
    A1cDeleteRequest,
    BaseResponse,
    A1cListResponse,
    A1cRecord
)
from module import A1cModule

router = APIRouter()
security = HTTPBearer()

# ==================== 糖化血色素 ====================

@router.post("/api/user/a1c", response_model=BaseResponse, summary="上傳糖化血色素", tags=["糖化血色素"])
def upload_a1c(
    request: A1cUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳糖化血色素記錄
    
    - **需要 Bearer Token**
    - **a1c**: 糖化血色素值
    - **recorded_at**: 記錄時間 (格式: YYYY-MM-DD HH:MM:SS)
    
    ### 範例請求
    ```json
    {
        "a1c": "5",
        "recorded_at": "2023-11-12 11:11:11"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = A1cModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 上傳糖化血色素記錄
    success = A1cModule.upload_a1c(
        user_id=user_id,
        a1c=request.a1c,
        recorded_at=request.recorded_at
    )
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.get("/api/user/a1c", response_model=A1cListResponse, summary="獲取糖化血色素", tags=["糖化血色素"])
def get_a1c_list(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的所有糖化血色素記錄
    
    - **需要 Bearer Token**
    
    ### 回傳內容
    - **a1cs**: 糖化血色素記錄列表
      - id: 記錄 ID
      - a1c: 糖化血色素值
      - recorded_at: 記錄時間
      - created_at: 建立時間
      - updated_at: 更新時間
      - user_id: 用戶 ID
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = A1cModule.parse_user_id_from_token(authorization)
    if not user_id:
        return A1cListResponse(status="1", message="身份驗證失敗", a1cs=[])
    
    # 2. 查詢糖化血色素記錄
    a1cs = A1cModule.get_a1c_list(user_id=user_id)
    
    if a1cs is not None:
        return A1cListResponse(status="0", message="ok", a1cs=a1cs)
    else:
        return A1cListResponse(status="1", message="失敗", a1cs=[])


@router.delete("/api/user/a1c", response_model=BaseResponse, summary="刪除糖化血色素", tags=["糖化血色素"])
def delete_a1c(
    request: A1cDeleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    刪除糖化血色素記錄
    
    - **需要 Bearer Token**
    - **ids[]**: 要刪除的糖化血色素記錄 ID 列表
    
    ### 範例請求
    ```json
    {
        "ids[]": [52]
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = A1cModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 刪除糖化血色素記錄
    success = A1cModule.delete_a1c_records(
        user_id=user_id,
        ids=request.ids
    )
    
    if success:
        return BaseResponse(status="0", message="ok")
    else:
        return BaseResponse(status="1", message="失敗")
