from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.core.database import Base

# ==================== SQLAlchemy 資料庫模型 ====================

class News(Base):
    """最新消息資料表"""
    __tablename__ = "News"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, nullable=True)
    group = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    pushed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShareDB(Base):
    """分享記錄資料表"""
    __tablename__ = "Share"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fid = Column(String(50), nullable=False)  # 外部 ID (紀錄 ID)
    data_type = Column(Integer, nullable=False)  # 種類 (0:血壓; 1:體重; 2:血糖; 3:飲食; 4:其他)
    relation_type = Column(Integer, nullable=False)  # 關係類型 (1:親友; 2:糖友)
    user_id = Column(Integer, ForeignKey('UserAuth.id'))  # 分享者的使用者 ID
    shared_with_user_id = Column(Integer, nullable=True)  # 被分享對象的使用者 ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== Pydantic API 模型 ====================

class BaseResponse(BaseModel):
    """基本回應格式"""
    status: str
    message: str

class NewsItem(BaseModel):
    """最新消息項目"""
    id: int
    member_id: int
    group: int
    title: str
    message: str
    pushed_at: str
    created_at: str
    updated_at: str

class NewsResponse(BaseResponse):
    """最新消息回應"""
    news: List[NewsItem] = []

class ShareRequest(BaseModel):
    """分享請求"""
    type: int = Field(..., ge=0, le=4, description="種類, 0：血壓；1：體重；2：血糖；3：飲食；4：其他")
    id: int = Field(..., gt=0, description="紀錄ID")
    relation_type: int = Field(..., ge=1, le=2, description="1：親友；2：糖友")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": 1,
                "id": 1,
                "relation_type": 1
            }
        }   

class LocationData(BaseModel):
    """位置資料"""
    lat: str
    lng: str

class UserInfo(BaseModel):
    """用戶資訊"""
    id: int
    name: str
    account: str

class ShareRecord(BaseModel):
    """分享記錄"""
    id: int
    user_id: int
    sugar: Optional[float] = None
    timeperiod: Optional[int] = None
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    bmi: Optional[float] = None
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    pulse: Optional[int] = None
    meal: Optional[int] = None
    tag: List[str] = []
    image: List[str] = []
    location: Optional[LocationData] = None
    relation_type: int
    relation_id: int
    message: str
    type: int
    url: str
    recorded_at: str
    created_at: str
    user: UserInfo

class ShareRecordsResponse(BaseResponse):
    """查看分享回應"""
    records: List[ShareRecord] = []