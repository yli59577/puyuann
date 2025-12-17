"""
關懷諮詢模組
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import CareMessageUpload, CareRecord
import sys
import os
from common.utils import get_logger

logger = get_logger(__name__)
# 加入 core 資料夾路徑
core_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core')
sys.path.insert(0, core_path)

from security import verify_token

# 移除路徑避免衝突
sys.path.remove(core_path)


class CareModule:
    """關懷諮詢模組"""
    
    def __init__(self, db_path: str = "Puyuan.db"):
        """初始化模組"""
        self.db_path = db_path
    
    @staticmethod
    def parse_user_id_from_token(authorization: str) -> Optional[int]:
        """從 Authorization Header 解析用戶 ID"""
        try:
            if not authorization or not authorization.startswith('Bearer '):
                return None
            
            token = authorization.split(' ')[1]
            payload = verify_token(token)
            
            if not payload:
                return None
            
            user_id = int(payload.get('sub'))
            return user_id
            
        except Exception as e:
            logger.error(f'parse_user_id_from_token 錯誤: {str(e)}', exc_info=True)
            return None
    
    def get_db_connection(self):
        """獲取資料庫連線"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_care_list(self, user_id: int) -> List[CareRecord]:
        """
        獲取使用者的關懷諮詢紀錄列表
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            關懷諮詢紀錄列表
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT * FROM UserCare 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            return [
                CareRecord(
                    id=row['id'],
                    user_id=row['user_id'],
                    member_id=row['member_id'],
                    reply_id=row['reply_id'],
                    message=row['message'],
                    updated_at=row['updated_at'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
        finally:
            conn.close()
    
    def upload_care_message(self, user_id: int, data: CareMessageUpload) -> CareRecord:
        """
        上傳關懷訊息
        
        Args:
            user_id: 使用者 ID
            data: 關懷訊息資料
            
        Returns:
            創建的關懷諮詢紀錄
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                """INSERT INTO UserCare 
                   (user_id, message, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (user_id, data.message, now, now)
            )
            
            conn.commit()
            record_id = cursor.lastrowid
            
            # 獲取並返回創建的記錄
            cursor.execute("SELECT * FROM UserCare WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            return CareRecord(
                id=row['id'],
                user_id=row['user_id'],
                member_id=row['member_id'],
                reply_id=row['reply_id'],
                message=row['message'],
                updated_at=row['updated_at'],
                created_at=row['created_at']
            )
            
        finally:
            conn.close()
