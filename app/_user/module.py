# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User as UserAuth
from app._user.models import UserProfile, UserDefaults, UserSettings
from app.care.models import Care
from typing import Optional
import jwt
from datetime import datetime, timedelta
# 導入統一的設定，移除本地的 SECRET_KEY 和 ALGORITHM
from app.core.security import SECRET_KEY, ALGORITHM, verify_token

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

            # 直接使用從 core.security 導入的 verify_token 函數
            payload = verify_token(token)
            
            if payload:
                user_id = int(payload.get("sub"))
                return user_id
            else:
                # 如果 verify_token 回傳 None，表示驗證失敗
                print("Token 解析失敗: 簽名驗證失敗或格式錯誤")
                return None

        except (jwt.ExpiredSignatureError, ValueError, TypeError) as e:
            print(f"Token 處理錯誤: {e}")
            return None

    # ... (此檔案的其他部分維持不變) ...
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
            print(f"[get_user_complete_data] 開始獲取用戶資料，user_id={user_id}")
            
            user_auth = db.query(UserAuth).filter(UserAuth.id == user_id).first()
            if not user_auth:
                print(f"[get_user_complete_data] 找不到 UserAuth，user_id={user_id}")
                return None

            print(f"[get_user_complete_data] 找到 UserAuth: email={user_auth.email}")
            
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not user_profile:
                print(f"[get_user_complete_data] 警告: 找不到 UserProfile，user_id={user_id}")
            else:
                print(f"[get_user_complete_data] 找到 UserProfile: name={user_profile.name}")

            # 獲取用戶預設值
            user_defaults = db.query(UserDefaults).filter(UserDefaults.user_id == user_id).first()
            
            # 構建 default 字典 - 根據規格書順序（max 在前，min 在後）
            default_data = {
                "id": user_defaults.id if user_defaults else 0,
                "user_id": user_id,
                "sugar_morning_max": user_defaults.sugar_morning_max if user_defaults and user_defaults.sugar_morning_max is not None else 0,
                "sugar_morning_min": user_defaults.sugar_morning_min if user_defaults and user_defaults.sugar_morning_min is not None else 0,
                "sugar_evening_max": user_defaults.sugar_evening_max if user_defaults and user_defaults.sugar_evening_max is not None else 0,
                "sugar_evening_min": user_defaults.sugar_evening_min if user_defaults and user_defaults.sugar_evening_min is not None else 0,
                "sugar_before_max": user_defaults.sugar_before_max if user_defaults and user_defaults.sugar_before_max is not None else 0,
                "sugar_before_min": user_defaults.sugar_before_min if user_defaults and user_defaults.sugar_before_min is not None else 0,
                "sugar_after_max": user_defaults.sugar_after_max if user_defaults and user_defaults.sugar_after_max is not None else 0,
                "sugar_after_min": user_defaults.sugar_after_min if user_defaults and user_defaults.sugar_after_min is not None else 0,
                "systolic_max": user_defaults.systolic_max if user_defaults and user_defaults.systolic_max is not None else 0,
                "systolic_min": user_defaults.systolic_min if user_defaults and user_defaults.systolic_min is not None else 0,
                "diastolic_max": user_defaults.diastolic_max if user_defaults and user_defaults.diastolic_max is not None else 0,
                "diastolic_min": user_defaults.diastolic_min if user_defaults and user_defaults.diastolic_min is not None else 0,
                "pulse_max": user_defaults.pulse_max if user_defaults and user_defaults.pulse_max is not None else 0,
                "pulse_min": user_defaults.pulse_min if user_defaults and user_defaults.pulse_min is not None else 0,
                "weight_max": user_defaults.weight_max if user_defaults and user_defaults.weight_max is not None else 0,
                "weight_min": user_defaults.weight_min if user_defaults and user_defaults.weight_min is not None else 0,
                "bmi_max": user_defaults.bmi_max if user_defaults and user_defaults.bmi_max is not None else 0,
                "bmi_min": user_defaults.bmi_min if user_defaults and user_defaults.bmi_min is not None else 0,
                "body_fat_max": user_defaults.body_fat_max if user_defaults and user_defaults.body_fat_max is not None else 0,
                "body_fat_min": user_defaults.body_fat_min if user_defaults and user_defaults.body_fat_min is not None else 0,
                "created_at": user_defaults.created_at.isoformat() if user_defaults and user_defaults.created_at else "",
                "updated_at": user_defaults.updated_at.isoformat() if user_defaults and user_defaults.updated_at else ""
            }
            
            if user_defaults:
                print(f"[get_user_complete_data] 找到 UserDefaults 資料")
            else:
                print(f"[get_user_complete_data] 警告: 找不到 UserDefaults，返回 null 值，user_id={user_id}")

            # 獲取用戶設定
            user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            
            # 構建 setting 字典 - 所有欄位使用預設值，避免 Swift 解析失敗
            setting_data = {
                "id": user_settings.id if user_settings else 0,
                "user_id": user_id,
                "after_recording": 1 if user_settings and user_settings.after_recording else 0,
                "no_recording_for_a_day": 1 if user_settings and user_settings.no_recording_for_a_day else 0,
                "over_max_or_under_min": 1 if user_settings and user_settings.over_max_or_under_min else 0,
                "after_meal": 1 if user_settings and user_settings.after_meal else 0,
                "unit_of_sugar": 1 if user_settings and user_settings.unit_of_sugar else 0,
                "unit_of_weight": 1 if user_settings and user_settings.unit_of_weight else 0,
                "unit_of_height": 1 if user_settings and user_settings.unit_of_height else 0,
                "created_at": user_settings.created_at.isoformat() if user_settings and user_settings.created_at else "",
                "updated_at": user_settings.updated_at.isoformat() if user_settings and user_settings.updated_at else ""
            }
            
            if user_settings:
                print(f"[get_user_complete_data] 找到 UserSettings 資料")
            else:
                print(f"[get_user_complete_data] 警告: 找不到 UserSettings，返回預設值，user_id={user_id}")

            user_data = {
                # 從 UserAuth 獲取
                "id": user_auth.id,
                "account": user_auth.account or "",
                "email": user_auth.email or "",
                "phone": user_auth.phone or "",
                "verified": 1 if user_auth.verified else 0,  # 轉換 bool 為 int
                "privacy_policy": 1 if user_auth.privacy_policy else 0,  # 轉換 bool 為 int
                "must_change_password": 1 if user_auth.must_change_password else 0,  # 轉換 bool 為 int
                "fcm_id": user_auth.fcm_id or "",
                "fb_id": user_auth.fb_id or "",
                "google_id": user_auth.google_id or "",
                "apple_id": user_auth.apple_id or "",
                "login_times": user_auth.login_times or 0,

                # 從 UserProfile 獲取
                "name": user_profile.name or "" if user_profile else "",
                "gender": user_profile.gender if user_profile and user_profile.gender is not None else 0,
                "birthday": user_profile.birthday or "" if user_profile else "",
                "height": user_profile.height or 0.0 if user_profile else 0.0,
                "weight": user_profile.weight or 0.0 if user_profile else 0.0,
                "address": user_profile.address or "" if user_profile else "",
                "invite_code": user_profile.invite_code or "" if user_profile else "",
                "inviteCode": user_profile.invite_code or "" if user_profile else "",  # 駝峰命名版本
                "badge": user_profile.badge or 0 if user_profile else 0,
                "avatar": "",  # UserProfile 模型中沒有此欄位，但前端需要，固定返回空字串

                # 固定或暫時性欄位
                "group": "",
                "unread_records": [0, 0, 0],  # 根據規格書，預設為 [0, 0, 0]
                "status": "0",
                # VIP 狀態對象
                "vip": {
                    "id": 0,
                    "user_id": user_id,
                    "level": 0,
                    "started_at": "",
                    "ended_at": "",
                    "remark": 0.0,
                    "created_at": "",
                    "updated_at": ""
                },
                
                # 時間戳欄位
                "created_at": user_auth.created_at.isoformat() if user_auth.created_at else "",
                "updated_at": user_auth.updated_at.isoformat() if user_auth.updated_at else "",
                
                # 預設值欄位（從 user_defaults 表獲取）
                "default": default_data,
                
                # 設定欄位（從 user_settings 表獲取）
                "setting": setting_data
            }
            
            print(f"[get_user_complete_data] 成功組合用戶資料")
            return user_data
        except Exception as e:
            print(f"[get_user_complete_data] 發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return None