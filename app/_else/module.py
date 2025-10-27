# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app._else.models import News, ShareDB, NewsItem, ShareRecord, UserInfo, LocationData
from datetime import datetime
from typing import List, Optional

class NewsModule:
    """最新消息業務邏輯"""
    
    @staticmethod
    def get_news_list(db: Session, limit: int = 20) -> List[NewsItem]:
        """
        獲取最新消息列表
        
        Args:
            db: 資料庫 session
            limit: 返回數量限制
            
        Returns:
            最新消息列表
        """ 
        try:
            news_list = db.query(News).order_by(desc(News.created_at)).limit(limit).all()
            
            return [
                NewsItem(
                    id=news.id,
                    member_id=news.member_id or 0,
                    group=news.group or 0,
                    title=news.title,
                    message=news.message,
                    pushed_at=str(news.pushed_at) if news.pushed_at else str(news.created_at),
                    created_at=str(news.created_at),
                    updated_at=str(news.updated_at)
                )
                for news in news_list
            ]
        except Exception as e:
            print(f"查詢最新消息失敗: {str(e)}")
            return []


class ShareModule:
    """分享業務邏輯"""
    
    @staticmethod
    def create_share(db: Session, record_id: int, data_type: int, relation_type: int, user_id: int) -> bool:
        """
        創建分享記錄
        
        Args:
            db: 資料庫 session
            record_id: 記錄ID
            data_type: 資料類型 (0:血壓, 1:體重, 2:血糖, 3:飲食, 4:其他)
            relation_type: 關係類型 (1:親友, 2:糖友)
            user_id: 用戶ID
            
        Returns:
            是否成功
        """
        try:
            # 檢查記錄是否存在
            if not ShareModule._check_record_exists(db, record_id, data_type):
                return False
            
            # 創建分享記錄
            share = ShareDB(
                fid=str(record_id),
                data_type=data_type,
                relation_type=relation_type,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(share)
            db.commit()
            return True
            
        except Exception as e:
            print(f"創建分享記錄失敗: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def _check_record_exists(db: Session, record_id: int, data_type: int) -> bool:
        """
        檢查記錄是否存在
        
        Args:
            db: 資料庫 session
            record_id: 記錄ID
            data_type: 資料類型
            
        Returns:
            是否存在
        """
        # TODO: 根據 data_type 查詢對應的資料表
        # 0: BloodPressure, 1: Weight, 2: BloodSugar, 3: DiaryDiet, 4: 其他
        # 暫時返回 True
        return True
    
    @staticmethod
    def get_shared_records(db: Session, data_type: int, user_id: int) -> List[ShareRecord]:
        """
        獲取分享記錄列表
        
        Args:
            db: 資料庫 session
            data_type: 資料類型
            user_id: 當前用戶ID
            
        Returns:
            分享記錄列表
        """
        try:
            # 查詢分享給當前用戶的記錄
            shares = db.query(ShareDB).filter(
                ShareDB.data_type == data_type,
                # TODO: 添加分享對象過濾條件
                # ShareDB.shared_with_user_id == user_id
            ).all()
            
            records = []
            for share in shares:
                # TODO: 根據 data_type 查詢對應的健康記錄
                record = ShareModule._get_health_record(db, int(share.fid), data_type)
                if record:
                    records.append(record)
            
            return records
            
        except Exception as e:
            print(f"查詢分享記錄失敗: {str(e)}")
            return []
    
    @staticmethod
    def _get_health_record(db: Session, record_id: int, data_type: int) -> Optional[ShareRecord]:
        """
        獲取健康記錄詳情
        
        Args:
            db: 資料庫 session
            record_id: 記錄ID
            data_type: 資料類型
            
        Returns:
            健康記錄或 None
        """
        # TODO: 根據 data_type 查詢對應的健康記錄
        # 目前返回假資料
        return ShareRecord(
            id=record_id,
            user_id=0,
            sugar=0.0,
            timeperiod=0,
            weight=0.0,
            body_fat=0.0,
            bmi=0.0,
            systolic=0,
            diastolic=0,
            pulse=0,
            meal=0,
            tag=[],
            image=[],
            location=LocationData(lat="0", lng="0"),
            relation_type=1,
            relation_id=0,
            message="",
            type=data_type,
            url="",
            recorded_at="2023-06-26 17:10:11",
            created_at="2023-06-26 17:10:11",
            user=UserInfo(id=0, name="測試用戶", account="test")
        )


class BadgeModule:
    """徽章業務邏輯"""
    
    @staticmethod
    def update_user_badge(db: Session, user_id: int) -> bool:
        """
        更新用戶徽章
        
        Args:
            db: 資料庫 session
            user_id: 用戶ID
            
        Returns:
            是否成功
        """
        try:
            # TODO: 計算用戶的各種成就
            # 1. 連續記錄天數
            # 2. 分享次數
            # 3. 血糖/血壓控制良好天數
            # 4. 其他成就條件
            
            # TODO: 更新用戶的徽章資料
            
            return True
            
        except Exception as e:
            print(f"更新徽章失敗: {str(e)}")
            return False