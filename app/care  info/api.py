"""
關懷諮詢 API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from models import CareMessageUpload, CareListResponse, BaseResponse
from module import CareModule

router = APIRouter(tags=["關懷諮詢"])

care_module = CareModule()


@router.get("/api/user/care", response_model=CareListResponse)
async def get_care_list(
    authorization: Optional[str] = Header(None)
):
    """
    獲取關懷諮詢列表
    
    需要認證: 是
    """
    try:
        # 驗證 token 並獲取 user_id
        user_id = CareModule.parse_user_id_from_token(authorization)
        
        # 獲取關懷諮詢列表
        cares = care_module.get_care_list(user_id)
        
        return CareListResponse(
            status="0",
            message="ok",
            cares=cares
        )
        
    except Exception as e:
        return CareListResponse(
            status="1",
            message="失敗",
            cares=[]
        )


@router.post("/api/user/care", response_model=BaseResponse)
async def upload_care_message(
    data: CareMessageUpload,
    authorization: Optional[str] = Header(None)
):
    """
    上傳關懷諮詢
    
    需要認證: 是
    """
    try:
        # 驗證 token 並獲取 user_id
        user_id = CareModule.parse_user_id_from_token(authorization)
        
        # 上傳關懷訊息
        care_module.upload_care_message(user_id, data)
        
        return BaseResponse(
            status="0",
            message="成功"
        )
        
    except Exception as e:
        return BaseResponse(
            status="1",
            message="失敗"
        )
