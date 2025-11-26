from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app._user.models import UserProfileUpdate, UserSettingsUpdate, BaseResponse, UserProfileResponse
from app._user.module import UserModule
from typing import Optional

router = APIRouter()

@router.patch("", response_model=BaseResponse, summary="更新個人資料", tags=["個人資訊"])
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


@router.get("", summary="獲取個人資料", tags=["個人資訊"])
def get_user_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    獲取個人資料
    
    - **需要 Bearer Token**
    - **回傳用戶所有相關資料**
    """
    # 1. 解析 Token
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return {"status": "1", "message": "身份驗證失敗", "user": None}
    
    # 2. 獲取用戶完整資料
    user_data = UserModule.get_user_complete_data(db, user_id)
    if not user_data:
        return {"status": "1", "message": "找不到用戶資料", "user": None}
        
    # 3. 按照 App 預期的格式回傳
    try:
        # 嘗試驗證數據，避免 FastAPI 自動驗證失敗導致回傳 422 (缺少 status 欄位)
        from app._user.models import UserProfileData
        # 確保 user_data 符合 UserProfileData 的結構
        validated_user_data = UserProfileData(**user_data)
        
        final_response = {
            "status": "0",
            "message": "成功",
            "user": validated_user_data
        }
        print(f"API 最終回傳資料: {final_response}")
        return final_response
    except Exception as e:
        print(f"資料驗證失敗: {e}")
        # 若驗證失敗，回傳帶有 status 的錯誤訊息，防止 App 崩潰
        return {
            "status": "1", 
            "message": f"資料格式錯誤: {str(e)}", 
            "user": None
        }


@router.patch("/setting", response_model=BaseResponse, summary="更新個人設定", tags=["個人資訊"])
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


@router.put("/badge", response_model=BaseResponse, summary="更新徽章", tags=["個人資訊"])
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