# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.core.security import verify_token
import json


class JournalModule:
    '''日記模組 - 提供可重用的業務邏輯'''

    @staticmethod
    def parse_user_id_from_token(authorization: str) -> Optional[int]:
        '''從 Authorization Header 解析用戶 ID'''
        try:
            print(f'[DEBUG] 收到的 authorization: {authorization[:50] if authorization else "None"}...')
            
            if not authorization or not authorization.startswith('Bearer '):
                print('[DEBUG] authorization 格式錯誤或為空')
                return None
            
            token = authorization.split(' ')[1]
            print(f'[DEBUG] 解析出的 token: {token[:30]}...')
            
            payload = verify_token(token)
            print(f'[DEBUG] verify_token 回傳: {payload}')
            
            if not payload:
                print('[DEBUG] payload 為空')
                return None
            
            user_id = int(payload.get('sub'))
            print(f'[DEBUG] 解析出的 user_id: {user_id}')
            return user_id
            
        except Exception as e:
            print(f'[DEBUG] parse_user_id_from_token 錯誤: {str(e)}')
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        '''查詢用戶'''
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_diary_list(db: Session, user_id: int, date: str) -> List[Dict[str, Any]]:
        '''獲取指定日期的日記列表'''
        try:
            print(f'[DEBUG] 開始查詢日記列表: user_id={user_id}, date={date}')
            
            # 使用 sqlite3 直接查詢,避免導入問題
            import sqlite3
            
            diary_list = []
            
            # 解析日期範圍
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
            print(f'[DEBUG] 解析後的日期: {target_date}')
            
            # 連接資料庫
            conn = sqlite3.connect('Puyuan.db')
            cursor = conn.cursor()
            
            # 先檢查資料庫中有哪些日期的資料
            cursor.execute("""
                SELECT DATE(measured_at), COUNT(*) 
                FROM blood_pressure_records 
                WHERE user_id = ? 
                GROUP BY DATE(measured_at)
            """, (user_id,))
            available_dates = cursor.fetchall()
            print(f'[DEBUG] 用戶 {user_id} 的血壓記錄日期: {available_dates}')
            
            # 查詢血壓記錄
            query_date = str(target_date)
            print(f'[DEBUG] 查詢日期字串: {query_date}')
            
            cursor.execute("""
                SELECT id, user_id, systolic, diastolic, pulse, measured_at
                FROM blood_pressure_records
                WHERE user_id = ? AND DATE(measured_at) = ?
            """, (user_id, query_date))
            
            blood_pressure_records = cursor.fetchall()
            print(f'[DEBUG] 查詢到 {len(blood_pressure_records)} 筆血壓記錄')
            if blood_pressure_records:
                print(f'[DEBUG] 第一筆血壓記錄: {blood_pressure_records[0]}')
            
            for record in blood_pressure_records:
                diary_list.append({
                    'id': record[0],
                    'user_id': record[1],
                    'systolic': record[2],
                    'diastolic': record[3],
                    'pulse': record[4],
                    'weight': 0.0,
                    'body_fat': 0.0,
                    'bmi': 0.0,
                    'sugar': 0,
                    'exercise': 0,
                    'drug': 0,
                    'timeperiod': 0,
                    'description': '',
                    'meal': None,
                    'tag': [],
                    'image': [],
                    'location': None,
                    'reply': '',
                    'recorded_at': record[5],
                    'type': 'blood_pressure'
                })
            
            # 查詢體重記錄
            cursor.execute("""
                SELECT id, user_id, weight, bmi, body_fat, measured_at
                FROM weight_records
                WHERE user_id = ? AND DATE(measured_at) = ?
            """, (user_id, query_date))
            
            weight_records = cursor.fetchall()
            print(f'[DEBUG] 查詢到 {len(weight_records)} 筆體重記錄')
            if weight_records:
                print(f'[DEBUG] 第一筆體重記錄: {weight_records[0]}')
            
            for record in weight_records:
                diary_list.append({
                    'id': record[0],
                    'user_id': record[1],
                    'systolic': 0,
                    'diastolic': 0,
                    'pulse': 0,
                    'weight': record[2],
                    'body_fat': record[4] or 0.0,
                    'bmi': record[3] or 0.0,
                    'sugar': 0,
                    'exercise': 0,
                    'drug': 0,
                    'timeperiod': 0,
                    'description': '',
                    'meal': None,
                    'tag': [],
                    'image': [],
                    'location': None,
                    'reply': '',
                    'recorded_at': record[5],
                    'type': 'weight'
                })
            
            # 查詢血糖記錄
            cursor.execute("""
                SELECT id, user_id, sugar_level, meal_time, measured_at
                FROM blood_sugar_records
                WHERE user_id = ? AND DATE(measured_at) = ?
            """, (user_id, query_date))
            
            blood_sugar_records = cursor.fetchall()
            print(f'[DEBUG] 查詢到 {len(blood_sugar_records)} 筆血糖記錄')
            if blood_sugar_records:
                print(f'[DEBUG] 第一筆血糖記錄: {blood_sugar_records[0]}')
            
            for record in blood_sugar_records:
                diary_list.append({
                    'id': record[0],
                    'user_id': record[1],
                    'systolic': 0,
                    'diastolic': 0,
                    'pulse': 0,
                    'weight': 0.0,
                    'body_fat': 0.0,
                    'bmi': 0.0,
                    'sugar': record[2],
                    'exercise': 0,
                    'drug': 0,
                    'timeperiod': record[3],
                    'description': '',
                    'meal': None,
                    'tag': [],
                    'image': [],
                    'location': None,
                    'reply': '',
                    'recorded_at': record[4],
                    'type': 'blood_sugar'
                })
            
            # 查詢飲食記錄 (從 DiaryDiet 表,需要處理 recorded_at 可能是字串的情況)
            # 先查詢所有該用戶的記錄,然後在 Python 中過濾
            cursor.execute("""
                SELECT id, user_id, description, meal, tag, image, lat, lng, recorded_at, created_at
                FROM DiaryDiet
                WHERE user_id = ?
            """, (user_id,))
            
            diet_records = cursor.fetchall()
            print(f'[DEBUG] 查詢到 {len(diet_records)} 筆飲食記錄(未過濾)')
            
            # 在 Python 中過濾符合日期的記錄
            filtered_diet_records = []
            for record in diet_records:
                recorded_at_str = record[8]  # recorded_at 欄位
                created_at_str = record[9]   # created_at 欄位
                
                # 嘗試從 recorded_at 提取日期
                match = False
                if recorded_at_str and recorded_at_str != 'string':
                    try:
                        if recorded_at_str.startswith(query_date):
                            match = True
                    except:
                        pass
                
                # 如果 recorded_at 是 'string',則使用 created_at
                if not match and recorded_at_str == 'string' and created_at_str:
                    try:
                        if created_at_str.startswith(query_date):
                            match = True
                    except:
                        pass
                
                if match:
                    filtered_diet_records.append(record)
            
            print(f'[DEBUG] 過濾後符合日期 {query_date} 的飲食記錄: {len(filtered_diet_records)} 筆')
            
            for record in filtered_diet_records:
                # 處理 None 的 id (使用 user_id 和時間戳生成臨時 ID)
                record_id = record[0] if record[0] else f"temp_{record[1]}_{record[9]}"
                
                # 解析 tag (JSON 格式)
                try:
                    tags = json.loads(record[4]) if record[4] else []
                    tag_list = [{'name': tags, 'message': 'ok'}] if tags else []
                except:
                    tag_list = []
                
                # 解析 image
                try:
                    images = [str(record[5])] if record[5] else []
                except:
                    images = []
                
                # 解析 location
                location = None
                if record[6] and record[7]:
                    location = {'lat': str(record[6]), 'lng': str(record[7])}
                
                diary_list.append({
                    'id': record_id,  # 使用處理過的 id
                    'user_id': record[1],
                    'systolic': 0,
                    'diastolic': 0,
                    'pulse': 0,
                    'weight': 0.0,
                    'body_fat': 0.0,
                    'bmi': 0.0,
                    'sugar': 0,
                    'exercise': 0,
                    'drug': 0,
                    'timeperiod': 0,
                    'description': str(record[2]),
                    'meal': record[3],
                    'tag': tag_list,
                    'image': images,
                    'location': location,
                    'reply': '',
                    'recorded_at': record[8],
                    'type': 'diet'
                })
            
            # 關閉資料庫連接
            conn.close()
            
            print(f'[DEBUG] 總共查詢到 {len(diary_list)} 筆日記記錄')
            return diary_list
            
        except Exception as e:
            print(f'獲取日記列表錯誤: {str(e)}')
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def upload_diet(
        db: Session,
        user_id: int,
        description: str,
        meal: int,
        tags: List[str],
        image: int,
        lat: Optional[float],
        lng: Optional[float],
        recorded_at: str
    ) -> bool:
        '''上傳飲食日記'''
        try:
            import sqlite3
            
            # 使用 sqlite3 直接操作
            conn = sqlite3.connect('Puyuan.db')
            cursor = conn.cursor()
            
            # 將 tags 轉換為 JSON 字符串
            tag_json = json.dumps(tags)
            
            # 不指定 id,讓資料庫自動生成 (AUTOINCREMENT)
            cursor.execute("""
                INSERT INTO DiaryDiet (user_id, description, meal, tag, image, lat, lng, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, description, meal, tag_json, image, lat, lng, recorded_at))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f'上傳飲食日記錯誤: {str(e)}')
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete_records(
        db: Session,
        user_id: int,
        delete_object: Dict[str, List[int]]
    ) -> bool:
        '''刪除日記記錄'''
        try:
            from app.Measurement_upload.models import (
                BloodPressureRecord,
                WeightRecord,
                BloodSugarRecord
            )
            import sqlite3
            
            # 刪除血壓記錄
            if 'blood_pressures' in delete_object:
                for record_id in delete_object['blood_pressures']:
                    record = db.query(BloodPressureRecord).filter(
                        BloodPressureRecord.id == record_id,
                        BloodPressureRecord.user_id == user_id
                    ).first()
                    if record:
                        db.delete(record)
            
            # 刪除體重記錄
            if 'weights' in delete_object:
                for record_id in delete_object['weights']:
                    record = db.query(WeightRecord).filter(
                        WeightRecord.id == record_id,
                        WeightRecord.user_id == user_id
                    ).first()
                    if record:
                        db.delete(record)
            
            # 刪除血糖記錄
            if 'blood_sugars' in delete_object:
                for record_id in delete_object['blood_sugars']:
                    record = db.query(BloodSugarRecord).filter(
                        BloodSugarRecord.id == record_id,
                        BloodSugarRecord.user_id == user_id
                    ).first()
                    if record:
                        db.delete(record)
            
            # 刪除飲食記錄
            if 'diets' in delete_object:
                conn = sqlite3.connect('Puyuan.db')
                cursor = conn.cursor()
                
                for record_id in delete_object['diets']:
                    cursor.execute("""
                        DELETE FROM DiaryDiet
                        WHERE id = ? AND user_id = ?
                    """, (record_id, user_id))
                
                conn.commit()
                conn.close()
            
            db.commit()
            return True
            
        except Exception as e:
            print(f'刪除記錄錯誤: {str(e)}')
            import traceback
            traceback.print_exc()
            db.rollback()
            return False


# 添加缺少的 func 導入
from sqlalchemy import func
