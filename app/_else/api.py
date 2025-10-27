from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app._else.models import (
    BaseResponse, 
    NewsResponse, 
    ShareRequest, 
    ShareRecordsResponse
)
from app._else.module import NewsModule, ShareModule, BadgeModule

router = APIRouter()

# ==================== 最新消息 API ====================
@router.get("/news", response_model=NewsResponse, summary="最新消息", tags=["其他"])
def get_news(db: Session = Depends(get_db)):
    """
    ## 最新消息
    
    獲取系統的最新消息列表
    
    ### HTTP Method: GET
    ### URL: /api/news
    
    ### Request Parameters
    - 無需參數
    
    ### Response
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    - **news**: 最新消息列表
      - id: 消息ID
      - member_id: 會員ID
      - group: 分組
      - title: 標題
      - message: 內容
      - pushed_at: 推送時間
      - created_at: 建立時間
      - updated_at: 更新時間
    """
    try:
        news_list = NewsModule.get_news_list(db)
        
        if not news_list:
            # 沒有消息時返回空列表
            return {
                "status": "0",
                "message": "目前沒有最新消息",
                "news": []
            }
        
        return {
            "status": "0",
            "message": "ok",
            "news": [news.dict() for news in news_list]
        }
    except Exception as e:
        return {
            "status": "1",
            "message": f"查詢失敗: {str(e)}",
            "news": []
        }


# ==================== 分享 API ====================
@router.post("/share", response_model=BaseResponse, summary="分享", tags=["其他"])
def share_content(request: ShareRequest, db: Session = Depends(get_db)):
    """
    ## 分享
    
    將健康記錄（血壓/體重/血糖/飲食）分享給親友或糖友
    
    ### HTTP Method: POST
    ### URL: /api/share
    
    ### Request Parameters
    - **type**: 種類
      - 0: 血壓
      - 1: 體重
      - 2: 血糖
      - 3: 飲食
      - 4: 其他
    - **id**: 要分享的紀錄ID (必須 > 0)
    - **relation_type**: 分享對象
      - 1: 親友
      - 2: 糖友
    
    ### Response
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    
    ### Example Request
    ```json
    {
        "type": 1,
        "id": 1,
        "relation_type": 1
    }
    ```
    """
    try:
        # TODO: 從 JWT token 獲取當前用戶ID
        current_user_id = 1  # 暫時硬編碼
        
        # 創建分享記錄
        success = ShareModule.create_share(
            db=db,
            record_id=request.id,
            data_type=request.type,
            relation_type=request.relation_type,
            user_id=current_user_id
        )
        
        if success:
            return {
                "status": "0",
                "message": "ok"
            }
        else:
            return {
                "status": "1",
                "message": "記錄不存在或分享失敗"
            }
            
    except Exception as e:
        return {
            "status": "1",
            "message": f"分享失敗: {str(e)}"
        }


# ==================== 查看分享 API ====================
@router.get("/share/{type}", response_model=ShareRecordsResponse, summary="查看分享", tags=["其他"])
def view_share_by_type(type: int, db: Session = Depends(get_db)):
    """
    ## 查看分享
    
    根據類型查詢分享給自己的健康記錄
    
    ### HTTP Method: GET
    ### URL: /api/share/{type}
    
    ### Path Parameters
    - **type**: 記錄類型
      - 0: 血壓
      - 1: 體重
      - 2: 血糖
      - 3: 飲食
      - 4: 其他
    
    ### Response
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    - **records**: 分享記錄列表，包含：
      - 健康數據（血壓值、體重、血糖等）
      - 記錄時間
      - 分享者資訊
      - 標籤、圖片、位置等
    """
    try:
        # 驗證 type 範圍
        if type < 0 or type > 4:
            return {
                "status": "1",
                "message": "無效的記錄類型",
                "records": []
            }
        
        # TODO: 從 JWT token 獲取當前用戶ID
        current_user_id = 1  # 暫時硬編碼
        
        # 查詢分享記錄
        records = ShareModule.get_shared_records(
            db=db,
            data_type=type,
            user_id=current_user_id
        )
        
        return {
            "status": "0",
            "message": "ok",
            "records": [record.dict() for record in records]
        }
        
    except Exception as e:
        return {
            "status": "1",
            "message": f"查詢失敗: {str(e)}",
            "records": []
        }


# ==================== 更新 Badge API ====================
@router.put("/user/badge", response_model=BaseResponse, summary="更新Badge", tags=["其他"])
def update_badge(db: Session = Depends(get_db)):
    """
    ## 更新Badge
    
    更新用戶的徽章/成就狀態
    
    ### HTTP Method: PUT
    ### URL: /api/user/badge
    
    ### Request Parameters
    - 無需參數（從 JWT token 獲取用戶資訊）
    
    ### Response
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    
    ### 徽章類型
    - 🏆 連續記錄 7 天
    - 🏆 連續記錄 30 天
    - 🏆 血糖控制良好
    - 🏆 樂於分享
    - 🏆 健康生活達人
    """
    try:
        # TODO: 從 JWT token 獲取當前用戶ID
        current_user_id = 1  # 暫時硬編碼
        
        # 更新徽章
        success = BadgeModule.update_user_badge(db, current_user_id)
        
        if success:
            return {
                "status": "0",
                "message": "成功"
            }
        else:
            return {
                "status": "1",
                "message": "更新失敗"
            }
            
    except Exception as e:
        return {
            "status": "1",
            "message": f"失敗: {str(e)}"
        }