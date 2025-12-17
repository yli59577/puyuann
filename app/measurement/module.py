# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User
from datetime import datetime
from typing import Optional
from app.core.security import verify_token
from .models import BloodPressureRecord, WeightRecord, BloodSugarRecord, MeasurementRecord
from common.utils import get_logger

logger = get_logger(__name__)


class MeasurementModule:
    '''測量上傳模組 - 提供可重用的業務邏輯'''

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
            return int(payload.get('sub'))
        except:
            return None
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        '''查詢用戶'''
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def upload_blood_pressure(
        db: Session, 
        user_id: int, 
        systolic: int, 
        diastolic: int, 
        pulse: Optional[int],
        measured_at: str
    ) -> Optional[int]:
        '''上傳血壓測量結果'''
        try:
            # 解析測量時間
            measured_time = datetime.fromisoformat(measured_at.replace('Z', '+00:00'))
            
            # 創建血壓記錄
            record = BloodPressureRecord(
                user_id=user_id,
                systolic=systolic,
                diastolic=diastolic,
                pulse=pulse,
                measured_at=measured_time
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(f'血壓記錄已儲存: id={record.id}, user_id={user_id}')
            return record.id
        except Exception as e:
            logger.error(f'上傳血壓記錄錯誤: {str(e)}', exc_info=True)
            db.rollback()
            return None
    
    @staticmethod
    def upload_weight(
        db: Session, 
        user_id: int, 
        weight: float, 
        bmi: Optional[float],
        body_fat: Optional[float],
        measured_at: str
    ) -> Optional[int]:
        '''上傳體重測量結果'''
        try:
            # 解析測量時間
            measured_time = datetime.fromisoformat(measured_at.replace('Z', '+00:00'))
            
            # 創建體重記錄
            record = WeightRecord(
                user_id=user_id,
                weight=weight,
                bmi=bmi,
                body_fat=body_fat,
                measured_at=measured_time
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(f'體重記錄已儲存: id={record.id}, user_id={user_id}')
            return record.id
        except Exception as e:
            logger.error(f'上傳體重記錄錯誤: {str(e)}', exc_info=True)
            db.rollback()
            return None
    
    @staticmethod
    def upload_blood_sugar(
        db: Session, 
        user_id: int, 
        glucose: int, 
        meal_time: int,
        measured_at: str
    ) -> Optional[int]:
        '''上傳血糖測量結果'''
        try:
            # 解析測量時間
            measured_time = datetime.fromisoformat(measured_at.replace('Z', '+00:00'))
            
            # 創建血糖記錄
            record = BloodSugarRecord(
                user_id=user_id,
                glucose=glucose,
                meal_time=meal_time,
                measured_at=measured_time
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(f'血糖記錄已儲存: id={record.id}, user_id={user_id}')
            return record.id
        except Exception as e:
            logger.error(f'上傳血糖記錄錯誤: {str(e)}', exc_info=True)
            db.rollback()
            return None
    
    @staticmethod
    def create_measurement_record(
        db: Session,
        user_id: int,
        record_type: int,
        record_id: int
    ) -> bool:
        '''創建測量記錄上傳記錄'''
        try:
            record = MeasurementRecord(
                user_id=user_id,
                record_type=record_type,
                record_id=record_id
            )
            db.add(record)
            db.commit()
            return True
        except Exception as e:
            logger.error(f'創建測量記錄錯誤: {str(e)}', exc_info=True)
            db.rollback()
            return False
    
    @staticmethod
    def get_last_upload_time(db: Session, user_id: int) -> Optional[str]:
        '''獲取最後上傳時間'''
        try:
            # 查詢最近的上傳記錄
            last_record = db.query(MeasurementRecord)\
                .filter(MeasurementRecord.user_id == user_id)\
                .order_by(MeasurementRecord.uploaded_at.desc())\
                .first()
            
            if last_record:
                return last_record.uploaded_at.isoformat()
            return None
        except Exception as e:
            logger.error(f'查詢最後上傳時間錯誤: {str(e)}', exc_info=True)
            return None
