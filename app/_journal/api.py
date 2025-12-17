# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db

# 導入模型和模組
from app._journal.models import (
    DietUpload,
    DeleteRecordsRequest,
    BaseResponse,
    DietUploadResponse,
    DiaryListResponse
)
from app._journal.module import JournalModule
from common.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

# ==================== 日記 ====================

@router.get("/diary", response_model=DiaryListResponse, summary="獲取日記列表資料", tags=["日記"])
def get_diary_list(
    date: str = Query(..., description="要查詢日期 (格式: YYYY-MM-DD)"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    獲取日記列表資料
    
    - **需要 Bearer Token**
    - **date**: 要查詢的日期 (格式: YYYY-MM-DD)
    
    ### 回傳內容
    - **blood_pressure**: 血壓記錄
    - **blood_sugar**: 血糖記錄
    - **weight**: 體重記錄
    - **diet**: 飲食記錄
    
    ### 範例請求
    ```
    GET /api/user/diary?date=2023-06-05
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    logger.debug(f"Authorization header: {authorization[:50]}...")
    user_id = JournalModule.parse_user_id_from_token(authorization)
    logger.debug(f"Parsed user_id: {user_id}")
    
    if not user_id:
        return DiaryListResponse(status="1", message="身份驗證失敗", diary=[])
    
    # 2. 檢查用戶是否存在
    user = JournalModule.get_user(db, user_id)
    logger.debug(f"User exists: {user is not None}")
    
    if not user:
        return DiaryListResponse(status="1", message="用戶不存在", diary=[])
    
    # 3. 獲取日記列表
    logger.debug(f"Calling get_diary_list with user_id={user_id}, date={date}")
    diary_list = JournalModule.get_diary_list(db, user_id, date)
    logger.debug(f"get_diary_list returned {len(diary_list) if diary_list else 0} records")
    
    if diary_list is not None:
        return DiaryListResponse(
            status="0",
            message="ok",
            diary=diary_list
        )
    else:
        return DiaryListResponse(status="1", message="失敗", diary=[])


@router.post("/diet", response_model=DietUploadResponse, summary="上傳飲食日記", tags=["日記"])
def upload_diet(
    request: DietUpload,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    上傳飲食日記
    
    - **需要 Bearer Token**
    - **description**: 描述
    - **meal**: 時段 (0:早餐, 1:午餐, 2:晚餐)
    - **tag[]**: 標籤列表
    - **image**: 照片數量
    - **lat**: 緯度 (可選)
    - **lng**: 經度 (可選)
    - **recorded_at**: 記錄時間
    
    ### 範例請求
    ```json
    {
        "description": "美味的午餐",
        "meal": 1,
        "tag[]": ["健康", "美味"],
        "image": 3,
        "lat": 15.0,
        "lng": 16.0,
        "recorded_at": "2023-06-06 07:40:59"
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = JournalModule.parse_user_id_from_token(authorization)
    if not user_id:
        return DietUploadResponse(status="1", message="身份驗證失敗", image_url=None)
    
    # 2. 檢查用戶是否存在
    user = JournalModule.get_user(db, user_id)
    if not user:
        return DietUploadResponse(status="1", message="用戶不存在", image_url=None)
    
    # 3. 上傳飲食日記
    success = JournalModule.upload_diet(
        db=db,
        user_id=user_id,
        description=request.description,
        meal=request.meal,
        tags=request.tag,
        image=request.image,
        lat=request.lat,
        lng=request.lng,
        recorded_at=request.recorded_at
    )
    
    if success:
        return DietUploadResponse(
            status="0",
            message="ok",
            image_url=""  # TODO: 實作圖片上傳功能後返回圖片 URL
        )
    else:
        return DietUploadResponse(status="1", message="失敗", image_url=None)


@router.delete("/records", response_model=BaseResponse, summary="刪除日記記錄", tags=["日記"])
def delete_records(
    request: DeleteRecordsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    刪除日記記錄
    
    - **需要 Bearer Token**
    - **deleteObject**: 要刪除的記錄 ID
      - blood_pressures: 血壓記錄 ID 列表
      - blood_sugars: 血糖記錄 ID 列表
      - weights: 體重記錄 ID 列表
      - diets: 飲食記錄 ID 列表
    
    ### 範例請求
    ```json
    {
        "deleteObject": {
            "blood_pressures": [52],
            "blood_sugars": [52],
            "weights": [52],
            "diets": [52]
        }
    }
    ```
    """
    # 1. 從 credentials 解析 Token
    authorization = f"Bearer {credentials.credentials}"
    user_id = JournalModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 檢查用戶是否存在
    user = JournalModule.get_user(db, user_id)
    if not user:
        return BaseResponse(status="1", message="用戶不存在")
    
    # 3. 刪除記錄
    success = JournalModule.delete_records(
        db=db,
        user_id=user_id,
        delete_object=request.deleteObject
    )
    
    if success:
        return BaseResponse(status="0", message="ok")
    else:
        return BaseResponse(status="1", message="失敗")
