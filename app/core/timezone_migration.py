# -*- coding: utf-8 -*-
"""
時區遷移工具 - 將所有現有的時間資料轉換為 UTC+8
"""
import sqlite3
from datetime import datetime, timezone, timedelta
from common.utils import get_logger

logger = get_logger(__name__)
TAIWAN_TZ = timezone(timedelta(hours=8))


def migrate_timezone_to_utc8(db_path: str = "Puyuan.db"):
    """
    將資料庫中所有的時間欄位轉換為 UTC+8
    
    Args:
        db_path: 資料庫路徑
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 定義所有包含時間欄位的表和欄位
    tables_with_datetime = {
        'UserAuth': ['created_at', 'updated_at', 'token_expire_at', 'verification_expires_at'],
        'user_profiles': ['created_at', 'updated_at'],
        'user_defaults': ['created_at', 'updated_at'],
        'user_settings': ['created_at', 'updated_at'],
        'verification_codes': ['created_at', 'expires_at'],
        'blood_pressure_records': ['measured_at', 'created_at', 'updated_at'],
        'weight_records': ['measured_at', 'created_at', 'updated_at'],
        'blood_sugar_records': ['measured_at', 'created_at', 'updated_at'],
        'measurement_records': ['uploaded_at', 'created_at', 'updated_at'],
        'News': ['pushed_at', 'created_at', 'updated_at'],
        'Share': ['created_at', 'updated_at'],
        'UserCare': ['created_at', 'updated_at'],
        'medical_info': ['created_at', 'updated_at'],
        'drug_used': ['recorded_at', 'created_at', 'updated_at'],
        'a1c_records': ['recorded_at', 'created_at', 'updated_at'],
        'Friendship': ['created_at', 'updated_at'],
        'friend_requests': ['created_at', 'updated_at'],
        'DiaryDiet': ['recorded_at', 'created_at', 'updated_at'],
    }
    
    try:
        for table_name, datetime_columns in tables_with_datetime.items():
            # 檢查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                logger.info(f"表 {table_name} 不存在")
                continue
            
            for column_name in datetime_columns:
                # 檢查欄位是否存在
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if column_name not in columns:
                    logger.info(f"表 {table_name} 中的欄位 {column_name} 不存在")
                    continue
                
                # 查詢所有非 NULL 的時間值
                cursor.execute(f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL")
                rows = cursor.fetchall()
                
                if not rows:
                    logger.info(f"表 {table_name} 的欄位 {column_name} 沒有資料需要更新")
                    continue
                
                # 更新每一行
                updated_count = 0
                for row_id, datetime_str in rows:
                    try:
                        # 嘗試解析時間字串
                        if datetime_str:
                            # 假設現有資料是 UTC 時間，轉換為 UTC+8
                            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                            # 轉換為 UTC+8
                            dt_utc8 = dt.astimezone(TAIWAN_TZ).replace(tzinfo=None)
                            
                            # 更新資料庫
                            cursor.execute(
                                f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?",
                                (dt_utc8.isoformat(), row_id)
                            )
                            updated_count += 1
                    except Exception as e:
                        logger.warning(f"更新 {table_name}.{column_name} (id={row_id}) 時出錯: {str(e)}")
                
                if updated_count > 0:
                    logger.info(f"表 {table_name} 的欄位 {column_name}: 更新了 {updated_count} 行")
        
        conn.commit()
        logger.info("所有時間欄位已轉換為 UTC+8")
        
    except Exception as e:
        logger.error(f"時區遷移失敗: {str(e)}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_timezone_to_utc8()
