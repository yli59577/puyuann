"""
控糖團好友 API
"""
from fastapi import APIRouter, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .models import (
    FriendListResponse, InviteCodeResponse, FriendRequestsResponse,
    SendInviteRequest, BaseResponse, RemoveFriendsRequest, FriendResultsResponse
)
from .module import FriendModule

router = APIRouter(tags=["控糖團好友"])
security = HTTPBearer(auto_error=False)  # auto_error=False 讓認證失敗不會拋出異常

friend_module = FriendModule()


@router.get("/list", response_model=FriendListResponse)
async def get_friend_list(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    獲取控糖團好友列表
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return FriendListResponse(
                status="1",
                message="未授權",
                friends=[]
            )
        
        # 獲取好友列表
        friends = friend_module.get_friend_list(user_id)
        
        return FriendListResponse(
            status="0",
            message="ok",
            friends=friends
        )
        
    except Exception as e:
        print(f'[Friend API] get_friend_list 錯誤: {str(e)}')
        return FriendListResponse(
            status="1",
            message="失敗",
            friends=[]
        )


@router.get("/code", response_model=InviteCodeResponse)
async def get_invite_code(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    獲取自己的邀請碼
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return InviteCodeResponse(
                status="1",
                message="未授權"
            )
        
        # 獲取邀請碼
        invite_code = friend_module.get_invite_code(user_id)
        
        return InviteCodeResponse(
            status="0",
            message="ok",
            invite_code=invite_code
        )
        
    except Exception as e:
        print(f'[Friend API] get_invite_code 錯誤: {str(e)}')
        return InviteCodeResponse(
            status="1",
            message="失敗"
        )


@router.get("/requests", response_model=FriendRequestsResponse)
async def get_friend_requests(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    獲取好友邀請列表(別人寄給我的邀請)
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return FriendRequestsResponse(
                status="1",
                message="未授權",
                requests=[]
            )
        
        # 獲取好友邀請列表
        requests = friend_module.get_friend_requests(user_id)
        
        return FriendRequestsResponse(
            status="0",
            message="ok",
            requests=requests
        )
        
    except Exception as e:
        print(f'[Friend API] get_friend_requests 錯誤: {str(e)}')
        return FriendRequestsResponse(
            status="1",
            message="失敗",
            requests=[]
        )


@router.post("/send", response_model=BaseResponse)
async def send_friend_invite(
    data: SendInviteRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    送出好友邀請
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return BaseResponse(
                status="1",
                message="未授權"
            )
        
        # 送出好友邀請
        success = friend_module.send_friend_invite(user_id, data)
        
        if success:
            return BaseResponse(
                status="0",
                message="成功"
            )
        else:
            return BaseResponse(
                status="1",
                message="邀請碼無效或已送出過邀請"
            )
        
    except Exception as e:
        print(f'[Friend API] send_friend_invite 錯誤: {str(e)}')
        return BaseResponse(
            status="1",
            message="失敗"
        )


@router.get("/{friend_invite_id}/accept", response_model=BaseResponse)
async def accept_friend_invite(
    friend_invite_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    接受好友邀請
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return BaseResponse(
                status="1",
                message="未授權"
            )
        
        # 接受好友邀請
        success = friend_module.accept_friend_invite(user_id, friend_invite_id)
        
        if success:
            return BaseResponse(
                status="0",
                message="ok"
            )
        else:
            return BaseResponse(
                status="1",
                message="邀請不存在或已處理"
            )
        
    except Exception as e:
        print(f'[Friend API] accept_friend_invite 錯誤: {str(e)}')
        return BaseResponse(
            status="1",
            message="失敗"
        )


@router.get("/{friend_invite_id}/refuse", response_model=BaseResponse)
async def refuse_friend_invite(
    friend_invite_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    拒絕好友邀請
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return BaseResponse(
                status="1",
                message="未授權"
            )
        
        # 拒絕好友邀請
        success = friend_module.refuse_friend_invite(user_id, friend_invite_id)
        
        if success:
            return BaseResponse(
                status="0",
                message="ok"
            )
        else:
            return BaseResponse(
                status="1",
                message="邀請不存在或已處理"
            )
        
    except Exception as e:
        print(f'[Friend API] refuse_friend_invite 錯誤: {str(e)}')
        return BaseResponse(
            status="1",
            message="失敗"
        )


@router.delete("/remove", response_model=BaseResponse)
async def remove_friends(
    data: RemoveFriendsRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    刪除好友
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return BaseResponse(
                status="1",
                message="未授權"
            )
        
        # 刪除好友
        success = friend_module.remove_friends(user_id, data.ids)
        
        if success:
            return BaseResponse(
                status="0",
                message="ok"
            )
        else:
            return BaseResponse(
                status="1",
                message="刪除失敗"
            )
        
    except Exception as e:
        print(f'[Friend API] remove_friends 錯誤: {str(e)}')
        return BaseResponse(
            status="1",
            message="失敗"
        )


@router.get("/results", response_model=FriendResultsResponse)
async def get_friend_results(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    獲取控糖團結果列表(我送出的邀請的狀態)
    
    需要認證: 是
    """
    try:
        # 從 credentials 獲取 token
        authorization = f"Bearer {credentials.credentials}" if credentials else None
        
        # 驗證 token 並獲取 user_id
        user_id = FriendModule.parse_user_id_from_token(authorization)
        
        if not user_id:
            return FriendResultsResponse(
                status="1",
                message="未授權",
                results=[]
            )
        
        # 獲取好友結果列表
        results = friend_module.get_friend_results(user_id)
        
        return FriendResultsResponse(
            status="0",
            message="ok",
            results=results
        )
        
    except Exception as e:
        print(f'[Friend API] get_friend_results 錯誤: {str(e)}')
        return FriendResultsResponse(
            status="1",
            message="失敗",
            results=[]
        )
