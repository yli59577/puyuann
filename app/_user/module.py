# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token
from app.account.models import User as UserAuth
from app._user.models import UserProfile, UserDefaults, UserSettings
from app.care.models import Care
from typing import Optional
import jwt
from datetime import datetime, timedelta

# JWT 設定
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 天

class UserModule:
    
    @staticmethod
    def parse_user_id_from_token(authorization: Optional[str]) -> Optional[int]:
        """從 Authorization Header 中解析用戶 ID"""
        if not authorization:
            print("缺少 Authorization header")
            return None
        
        try:
            token_type, token = authorization.split(" ")
            if token_type != "Bearer":
                print(f"Token 類型錯誤: {token_type}")
                return None
            
            # print(f"接收到的 Authorization header: {authorization[:50]}...")
            # print(f"解析出的 token: {token}")

            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload.get("sub"))
            
            # print(f"解碼後的 payload: {payload}, User ID: {user_id}")
            return user_id
        except jwt.ExpiredSignatureError:
            print("Token 已過期")
            return None
        except (jwt.PyJWTError, ValueError, TypeError) as e:
            print(f"Token 解析失敗: {e}")
            return None

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[UserAuth]:
        '''查詢用戶基本認證資料'''
        return db.query(UserAuth).filter(UserAuth.id == user_id).first()

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
    def get_user_complete_data(db: Session, user_id: int) -> Optional[dict]:
        """獲取用戶所有相關資料，組合成一個字典"""
        try:
            # 1. 查詢 UserAuth 表 (這是主要表格，必須存在)
            user_auth = db.query(UserAuth).filter(UserAuth.id == user_id).first()
            if not user_auth:
                return None

            # 2. 查詢 UserProfile 表 (這是附屬表格，可能不存在)
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            # 3. 組合資料
            user_data = {
                "id": user_auth.id,
                "account": user_auth.account or "",
                "email": user_auth.email or "",
                "phone": (user_profile.phone or "") if user_profile else "",
                "name": (user_profile.name or "") if user_profile else "",
                "group": "",
                "gender": (user_profile.gender if user_profile and user_profile.gender is not None else 0),
                "birthday": (user_profile.birthday or "") if user_profile else "",
                "height": (user_profile.height or 0.0) if user_profile else 0.0,
                "weight": (user_profile.weight or 0.0) if user_profile else 0.0,
                "fcm_id": (user_profile.fcm_id or "") if user_profile else "",
                "address": (user_profile.address or "") if user_profile else "",
                "avatar": (user_profile.avatar or "") if user_profile else "",
                "fb_id": (user_profile.fb_id or "") if user_profile else "",
                "google_id": (user_profile.google_id or "") if user_profile else "",
                "apple_id": (user_profile.apple_id or "") if user_profile else "",
                "unread_records": []
            }
            
            return user_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None