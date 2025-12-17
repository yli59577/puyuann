"""
就醫、藥物資訊模組
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import MedicalInfoUpdate, DrugUsedUpload, DrugUsedDeleteRequest, MedicalInfo, DrugUsedRecord
from common.utils import get_logger

logger = get_logger(__name__)


class MedicineModule:
    """就醫、藥物資訊模組"""
    
    DB_PATH = "Puyuan.db"
    
    @staticmethod
    def get_db_connection():
        """獲取資料庫連線"""
        conn = sqlite3.connect(MedicineModule.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def get_medical_info(user_id: int) -> Optional[MedicalInfo]:
        """獲取使用者的就醫資訊"""
        conn = MedicineModule.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM medical_info WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return MedicalInfo(
                    id=row['id'],
                    user_id=row['user_id'],
                    oad=row['oad'],
                    insulin=row['insulin'],
                    anti_hypertensives=row['anti_hypertensives'],
                    diabetes_type=row['diabetes_type'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
        except Exception as e:
            logger.error(f"get_medical_info error: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    @staticmethod
    def update_medical_info(user_id: int, oad: int = None, insulin: int = None, 
                           anti_hypertensives: int = None, diabetes_type: int = None) -> bool:
        """更新或創建使用者的就醫資訊"""
        conn = MedicineModule.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            cursor.execute("SELECT id FROM medical_info WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    """UPDATE medical_info 
                       SET oad = COALESCE(?, oad), insulin = COALESCE(?, insulin), 
                           anti_hypertensives = COALESCE(?, anti_hypertensives), 
                           diabetes_type = COALESCE(?, diabetes_type), updated_at = ?
                       WHERE user_id = ?""",
                    (oad, insulin, anti_hypertensives, diabetes_type, now, user_id)
                )
            else:
                cursor.execute(
                    """INSERT INTO medical_info 
                       (user_id, oad, insulin, anti_hypertensives, diabetes_type, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, oad or 0, insulin or 0, anti_hypertensives or 0, diabetes_type or 0, now, now)
                )
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"update_medical_info error: {e}", exc_info=True)
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_drug_used_list(user_id: int) -> List[DrugUsedRecord]:
        """獲取使用者的藥物使用紀錄列表"""
        conn = MedicineModule.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT * FROM drug_used WHERE user_id = ? ORDER BY recorded_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            return [
                DrugUsedRecord(
                    id=row['id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    type=row['type'],
                    recorded_at=row['recorded_at'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"get_drug_used_list error: {e}", exc_info=True)
            return []
        finally:
            conn.close()
    
    @staticmethod
    def upload_drug_used(user_id: int, drug_type: int, name: str, recorded_at: str) -> bool:
        """上傳藥物使用紀錄"""
        conn = MedicineModule.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            cursor.execute(
                """INSERT INTO drug_used 
                   (user_id, name, type, recorded_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, name, drug_type, recorded_at, now, now)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"upload_drug_used error: {e}", exc_info=True)
            return False
        finally:
            conn.close()
    
    @staticmethod
    def delete_drug_used_records(user_id: int, ids: List[int]) -> bool:
        """刪除藥物使用紀錄"""
        if not ids:
            return True
        
        conn = MedicineModule.get_db_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join('?' * len(ids))
            query = f"DELETE FROM drug_used WHERE user_id = ? AND id IN ({placeholders})"
            cursor.execute(query, [user_id] + ids)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"delete_drug_used_records error: {e}", exc_info=True)
            return False
        finally:
            conn.close()
