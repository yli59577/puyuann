from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app._user.models import UserProfileUpdate, UserSettingsUpdate, BaseResponse, UserProfileResponse
from app._user.module import UserModule
from typing import Optional

router = APIRouter()

@router.patch("/api/user", response_model=BaseResponse, summary="更新個人資料", tags=["個人資訊"])
def update_user_profile(
    request: UserProfileUpdate, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    更新個人資料
    
    - **需要 Bearer Token**
    - **可更新欄位**: name, gender, birthday, height, weight, phone, address, avatar, fcm_id
    - **只更新提供的欄位**，未提供的欄位保持原值
    """
    # 1. 解析 Token
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 檢查用戶是否存在
    user = UserModule.get_user(db, user_id)
    if not user:
        return BaseResponse(status="1", message="用戶不存在")
    
    # 3. 更新資料
    update_data = request.dict(exclude_unset=True)
    success = UserModule.create_or_update_profile(db, user_id, update_data)
    
    if success:
        return BaseResponse(status="0", message="更新成功")
    else:
        return BaseResponse(status="1", message="更新失敗")


@router.get("/api/user", response_model=UserProfileResponse, summary="獲取個人資料", tags=["個人資訊"])
def get_user_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    獲取個人資料
    
    - **需要 Bearer Token**
    - **回傳**: 完整的用戶資料（包含個人資料、預設值、設定）
    """
    # 1. 解析 Token
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return UserProfileResponse(status="1", message="身份驗證失敗", data=None)
    
    # 2. 查詢完整用戶資料
    user_data = UserModule.get_user_complete_data(db, user_id)
    
    if not user_data:
        return UserProfileResponse(status="1", message="用戶不存在", data=None)
    
    return UserProfileResponse(status="0", message="成功", data=user_data)


@router.patch("/api/user/setting", response_model=BaseResponse, summary="更新個人設定", tags=["個人資訊"])
def update_user_settings(
    request: UserSettingsUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    更新個人設定
    
    - **需要 Bearer Token**
    - **可更新欄位**: after_recording, no_recording_for_a_day, notification_enabled, language, theme
    - **只更新提供的欄位**，未提供的欄位保持原值
    """
    # 1. 解析 Token
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 檢查用戶是否存在
    user = UserModule.get_user(db, user_id)
    if not user:
        return BaseResponse(status="1", message="用戶不存在")
    
    # 3. 更新設定
    update_data = request.dict(exclude_unset=True)
    success = UserModule.create_or_update_settings(db, user_id, update_data)
    
    if success:
        return BaseResponse(status="0", message="設定更新成功")
    else:
        return BaseResponse(status="1", message="設定更新失敗")


@router.put("/api/user/badge", response_model=BaseResponse, summary="更新徽章", tags=["個人資訊"])
def update_user_badge(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    更新用戶徽章
    
    - **需要 Bearer Token**
    - **功能**: 更新用戶的徽章/成就狀態
    
    ### 徽章類型
    - 🏆 連續記錄 7 天
    - 🏆 連續記錄 30 天
    - 🏆 血糖控制良好
    - 🏆 樂於分享
    - 🏆 健康生活達人
    """
    # 1. 解析 Token
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="身份驗證失敗")
    
    # 2. 檢查用戶是否存在
    user = UserModule.get_user(db, user_id)
    if not user:
        return BaseResponse(status="1", message="用戶不存在")
    
    # 3. 更新徽章 (這裡簡化處理,實際應該根據業務邏輯計算)
    try:
        # TODO: 實作徽章計算邏輯
        # - 查詢用戶記錄天數
        # - 檢查血糖控制情況
        # - 統計分享次數等
        return BaseResponse(status="0", message="徽章更新成功")
    except Exception as e:
        return BaseResponse(status="1", message=f"徽章更新失敗: {str(e)}")