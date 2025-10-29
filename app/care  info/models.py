"""
關懷諮詢資料模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CareMessageUpload(BaseModel):
    """上傳關懷訊息請求"""
    message: str = Field(..., description="關懷訊息")


class CareRecord(BaseModel):
    """關懷諮詢紀錄"""
    id: int
    user_id: int
    member_id: Optional[int] = None
    reply_id: Optional[int] = None
    message: str
    updated_at: str
    created_at: str


class CareListResponse(BaseModel):
    """關懷諮詢列表回應"""
    status: str = Field(..., description="訊息代碼，0=成功,1=失敗")
    message: str = Field(..., description="訊息")
    cares: List[CareRecord] = Field(default_factory=list, description="關懷資訊")


class BaseResponse(BaseModel):
    """基本回應"""
    status: str = Field(..., description="訊息代碼，0=成功,1=失敗")
    message: str = Field(..., description="訊息")
