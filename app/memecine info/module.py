"""
就醫、藥物資訊模組
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from models import MedicalInfoUpdate, DrugUsedUpload, DrugUsedDeleteRequest, MedicalInfo, DrugUsedRecord


class MedicineModule:
    """就醫、藥物資訊模組"""
    
    def __init__(self, db_path: str = "Puyuan.db"):
        """初始化模組"""
        self.db_path = db_path
    
    def get_db_connection(self):
        """獲取資料庫連線"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_medical_info(self, user_id: int) -> Optional[MedicalInfo]:
        """
        獲取使用者的就醫資訊
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            就醫資訊或 None
        """
        conn = self.get_db_connection()
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
            
        finally:
            conn.close()
    
    def update_medical_info(self, user_id: int, data: MedicalInfoUpdate) -> MedicalInfo:
        """
        更新或創建使用者的就醫資訊
        
        Args:
            user_id: 使用者 ID
            data: 就醫資訊更新資料
            
        Returns:
            更新後的就醫資訊
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            # 檢查是否已存在
            cursor.execute(
                "SELECT id FROM medical_info WHERE user_id = ?",
                (user_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新現有記錄
                cursor.execute(
                    """UPDATE medical_info 
                       SET oad = ?, insulin = ?, anti_hypertensives = ?, 
                           diabetes_type = ?, updated_at = ?
                       WHERE user_id = ?""",
                    (data.oad, data.insulin, data.anti_hypertensives, 
                     data.diabetes_type, now, user_id)
                )
            else:
                # 創建新記錄
                cursor.execute(
                    """INSERT INTO medical_info 
                       (user_id, oad, insulin, anti_hypertensives, diabetes_type, 
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, data.oad, data.insulin, data.anti_hypertensives, 
                     data.diabetes_type, now, now)
                )
            
            conn.commit()
            
            # 返回更新後的記錄
            return self.get_medical_info(user_id)
            
        finally:
            conn.close()
    
    def get_drug_used_list(
        self, 
        user_id: int, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        type_filter: Optional[int] = None
    ) -> List[DrugUsedRecord]:
        """
        獲取使用者的藥物使用紀錄列表
        
        Args:
            user_id: 使用者 ID
            start_time: 開始時間 (可選)
            end_time: 結束時間 (可選)
            type_filter: 藥物類型篩選 (可選)
            
        Returns:
            藥物使用紀錄列表
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM drug_used WHERE user_id = ?"
            params = [user_id]
            
            if start_time:
                query += " AND recorded_at >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND recorded_at <= ?"
                params.append(end_time.isoformat())
            
            if type_filter is not None:
                query += " AND type = ?"
                params.append(type_filter)
            
            query += " ORDER BY recorded_at DESC"
            
            cursor.execute(query, params)
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
            
        finally:
            conn.close()
    
    def upload_drug_used(self, user_id: int, data: DrugUsedUpload) -> DrugUsedRecord:
        """
        上傳藥物使用紀錄
        
        Args:
            user_id: 使用者 ID
            data: 藥物使用資料
            
        Returns:
            創建的藥物使用紀錄
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            cursor.execute(
                """INSERT INTO drug_used 
                   (user_id, name, type, recorded_at, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, data.name, data.type, data.recorded_at.isoformat(), now, now)
            )
            
            conn.commit()
            record_id = cursor.lastrowid
            
            # 獲取並返回創建的記錄
            cursor.execute("SELECT * FROM drug_used WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            return DrugUsedRecord(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                type=row['type'],
                recorded_at=row['recorded_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        finally:
            conn.close()
    
    def delete_drug_used_records(self, user_id: int, record_ids: List[int]) -> int:
        """
        刪除藥物使用紀錄
        
        Args:
            user_id: 使用者 ID
            record_ids: 要刪除的記錄 ID 列表
            
        Returns:
            刪除的記錄數量
        """
        if not record_ids:
            return 0
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join('?' * len(record_ids))
            query = f"DELETE FROM drug_used WHERE user_id = ? AND id IN ({placeholders})"
            
            cursor.execute(query, [user_id] + record_ids)
            conn.commit()
            
            return cursor.rowcount
            
        finally:
            conn.close()
