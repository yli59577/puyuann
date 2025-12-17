# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.core.security import verify_token
import sqlite3
from common.utils import get_logger

logger = get_logger(__name__)

class A1cModule:
    '''糖化血色素模組 - 提供可重用的業務邏輯'''

    @staticmethod
    def parse_user_id_from_token(authorization: str) -> Optional[int]:
        '''從 Authorization Header 解析用戶 ID'''
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

    @staticmethod
    def upload_a1c(user_id: int, a1c: str, recorded_at: str) -> bool:
        '''上傳糖化血色素記錄'''
        try:
            logger.debug(f'上傳糖化血色素: user_id={user_id}, a1c={a1c}, recorded_at={recorded_at}')
            
            # 使用 sqlite3 直接操作
            conn = sqlite3.connect('Puyuan.db')
            cursor = conn.cursor()
            
            # 插入記錄
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO a1c_records 
                (user_id, a1c, recorded_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, a1c, recorded_at, now, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f'糖化血色素上傳成功')
            return True
            
        except Exception as e:
            logger.error(f'上傳糖化血色素錯誤: {str(e)}', exc_info=True)
            return False

    @staticmethod
    def get_a1c_list(user_id: int) -> List[Dict[str, Any]]:
        '''獲取用戶的所有糖化血色素記錄'''
        try:
            logger.debug(f'查詢糖化血色素列表: user_id={user_id}')
            
            # 使用 sqlite3 直接查詢
            conn = sqlite3.connect('Puyuan.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, a1c, recorded_at, created_at, updated_at
                FROM a1c_records
                WHERE user_id = ?
                ORDER BY recorded_at DESC
            """, (user_id,))
            
            records = cursor.fetchall()
            conn.close()
            
            logger.debug(f'查詢到 {len(records)} 筆糖化血色素記錄')
            
            # 轉換為字典列表
            result = []
            for record in records:
                result.append({
                    'id': record[0],
                    'user_id': record[1],
                    'a1c': record[2],
                    'recorded_at': record[3],
                    'created_at': record[4],
                    'updated_at': record[5]
                })
            
            return result
            
        except Exception as e:
            logger.error(f'查詢糖化血色素列表錯誤: {str(e)}', exc_info=True)
            return []

    @staticmethod
    def delete_a1c_records(user_id: int, ids: List[int]) -> bool:
        '''刪除糖化血色素記錄'''
        try:
            logger.debug(f'刪除糖化血色素記錄: user_id={user_id}, ids={ids}')
            
            if not ids:
                logger.debug('沒有要刪除的記錄')
                return True
            
            # 使用 sqlite3 直接操作
            conn = sqlite3.connect('Puyuan.db')
            cursor = conn.cursor()
            
            # 刪除記錄(確保只能刪除自己的記錄)
            placeholders = ','.join('?' * len(ids))
            query = f"""
                DELETE FROM a1c_records 
                WHERE user_id = ? AND id IN ({placeholders})
            """
            
            cursor.execute(query, [user_id] + ids)
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f'成功刪除 {deleted_count} 筆糖化血色素記錄')
            return True
            
        except Exception as e:
            logger.error(f'刪除糖化血色素記錄錯誤: {str(e)}', exc_info=True)
            return False
