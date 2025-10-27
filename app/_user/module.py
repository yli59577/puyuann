# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User
from app._user.models import UserProfile, UserDefaults, UserSettings
from app.core.security import verify_token
from typing import Optional, Dict

class UserModule:
    '''用戶模組 - 提供可重用的業務邏輯'''

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
    def get_profile(db: Session, user_id: int) -> Optional[UserProfile]:
        '''查詢用戶個人資料'''
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    @staticmethod
    def get_defaults(db: Session, user_id: int) -> Optional[UserDefaults]:
        '''查詢用戶預設值'''
        return db.query(UserDefaults).filter(UserDefaults.user_id == user_id).first()
    
    @staticmethod
    def get_settings(db: Session, user_id: int) -> Optional[UserSettings]:
        '''查詢用戶設定'''
        return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    @staticmethod
    def create_or_update_profile(db: Session, user_id: int, update_data: dict) -> bool:
        '''創建或更新用戶個人資料'''
        try:
            profile = UserModule.get_profile(db, user_id)
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.add(profile)
            for key, value in update_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            db.commit()
            db.refresh(profile)
            return True
        except Exception as e:
            print(f'更新個人資料錯誤: {str(e)}')
            db.rollback()
            return False
    
    @staticmethod
    def create_or_update_defaults(db: Session, user_id: int, update_data: dict) -> bool:
        '''創建或更新用戶預設值'''
        try:
            defaults = UserModule.get_defaults(db, user_id)
            if not defaults:
                defaults = UserDefaults(user_id=user_id)
                db.add(defaults)
            for key, value in update_data.items():
                if hasattr(defaults, key):
                    setattr(defaults, key, value)
            db.commit()
            db.refresh(defaults)
            return True
        except Exception as e:
            print(f'更新預設值錯誤: {str(e)}')
            db.rollback()
            return False
    
    @staticmethod
    def create_or_update_settings(db: Session, user_id: int, update_data: dict) -> bool:
        '''創建或更新用戶設定'''
        try:
            settings = UserModule.get_settings(db, user_id)
            if not settings:
                settings = UserSettings(user_id=user_id)
                db.add(settings)
            for key, value in update_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            db.commit()
            db.refresh(settings)
            return True
        except Exception as e:
            print(f'更新設定錯誤: {str(e)}')
            db.rollback()
            return False
    
    @staticmethod
    def get_user_complete_data(db: Session, user_id: int) -> Optional[Dict]:
        '''獲取用戶完整資料'''
        try:
            user = UserModule.get_user(db, user_id)
            if not user:
                return None
            profile = UserModule.get_profile(db, user_id)
            defaults = UserModule.get_defaults(db, user_id)
            settings = UserModule.get_settings(db, user_id)
            return {
                'id': user.id,
                'email': user.email,
                'account': user.account,
                'profile': {
                    'name': profile.name if profile else None,
                    'gender': profile.gender if profile else None,
                    'birthday': profile.birthday if profile else None,
                    'height': profile.height if profile else None,
                    'weight': profile.weight if profile else None,
                    'phone': profile.phone if profile else None,
                    'address': profile.address if profile else None,
                    'avatar': profile.avatar if profile else None,
                } if profile else None,
                'defaults': {
                    'sugar_morning_max': defaults.sugar_morning_max if defaults else 0,
                    'sugar_morning_min': defaults.sugar_morning_min if defaults else 0,
                    'sugar_afternoon_max': defaults.sugar_afternoon_max if defaults else 0,
                    'sugar_afternoon_min': defaults.sugar_afternoon_min if defaults else 0,
                    'sugar_evening_max': defaults.sugar_evening_max if defaults else 0,
                    'sugar_evening_min': defaults.sugar_evening_min if defaults else 0,
                } if defaults else None,
                'settings': {
                    'after_recording': settings.after_recording if settings else False,
                    'no_recording_for_a_day': settings.no_recording_for_a_day if settings else False,
                    'notification_enabled': settings.notification_enabled if settings else True,
                    'language': settings.language if settings else 'zh-TW',
                    'theme': settings.theme if settings else 'light',
                } if settings else None,
            }
        except Exception as e:
            print(f'獲取用戶資料錯誤: {str(e)}')
            return None
