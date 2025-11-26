"""
控糖團好友資料模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FriendInfo(BaseModel):
    """好友資訊"""
    id: int
    name: str
    relation_type: int


class FriendListResponse(BaseModel):
    """好友列表回應"""
    status: str = Field(..., description="訊息代碼,0=成功,1=失敗")
    message: str = Field(..., description="訊息")
    friends: List[FriendInfo] = Field(default_factory=list, description="好友名單列表")


class InviteCodeResponse(BaseModel):
    """邀請碼回應"""
    status: str = Field(..., description="訊息代碼,0=成功,1=失敗")
    message: str = Field(..., description="訊息")
    invite_code: Optional[str] = Field(None, description="自己的邀請碼")


class UserInfo(BaseModel):
    """用戶資訊"""
    id: int
    name: str
    account: str


class FriendRequest(BaseModel):
    """好友邀請"""
    id: int
    user_id: int
    relation_id: int
    type: int
    read: int
    status: int
    created_at: str
    updated_at: str
    user: UserInfo


class FriendRequestsResponse(BaseModel):
    """好友邀請列表回應"""
    status: str = Field(..., description="訊息代碼,0=成功,1=失敗")
    message: str = Field(..., description="訊息")
    requests: List[FriendRequest] = Field(default_factory=list, description="查看有誰寄送邀請")


class SendInviteRequest(BaseModel):
    """送出邀請請求"""
    type: int = Field(..., description="好友類型")
    invite_code: str = Field(..., description="邀請碼")


class RemoveFriendsRequest(BaseModel):
    """刪除好友請求"""
    ids: List[int] = Field(..., alias="ids[]", description="好友ID列表")


class RelationInfo(BaseModel):
    """關係資訊"""
    id: int
    name: str
    account: str


class FriendResult(BaseModel):
    """好友結果"""
    id: int
    user_id: int
    relation_id: int
    type: int
    status: int
    read: int
    created_at: str
    updated_at: str
    relation: RelationInfo


class FriendResultsResponse(BaseModel):
    """好友結果列表回應"""
    status: str = Field(..., description="訊息代碼,0=成功,1=失敗")
    message: str = Field(..., description="訊息")
    results: List[FriendResult] = Field(default_factory=list, description="好友結果列表")


class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="訊息代碼,0=成功,1=失敗")
    message: str = Field(..., description="訊息")
