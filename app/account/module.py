# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User, VerificationCodeDB
from app.core.security import hash_password, verify_password, create_access_token
from typing import Optional, Dict
from datetime import datetime, timedelta
import random

class AccountModule:
    """帳號模組 - 處理註冊、登入、密碼管理"""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """根據 email 查詢用戶"""
        return db.query(User).filter(User.email == email).first()
    
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根據 ID 查詢用戶"""
        return db.query(User).filter(User.id == user_id).first()
    
    
    @staticmethod
    def register_user(db: Session, email: str, password: str) -> Dict[str, any]:
        """
        用戶註冊
        
        Returns:
            {"success": bool, "message": str, "user_id": int}
        """
        try:
            # 1. 檢查 email 是否已存在
            existing_user = AccountModule.get_user_by_email(db, email)
            if existing_user:
                return {"success": False, "message": "帳號已經存在", "user_id": None}
            
            # 2. 密碼加密
            hashed_pwd = hash_password(password)
            
            # 3. 創建新用戶
            new_user = User(
                email=email,
                password=hashed_pwd,
                account=email.split('@')[0],
                verified=False
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return {"success": True, "message": "註冊成功", "user_id": new_user.id}
            
        except Exception as e:
            print(f"註冊錯誤: {str(e)}")
            db.rollback()
            return {"success": False, "message": "註冊失敗", "user_id": None}
    
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> Dict[str, any]:
        """
        用戶登入
        
        Returns:
            {"success": bool, "message": str, "token": str}
        """
        try:
            # 1. 查詢用戶
            user = AccountModule.get_user_by_email(db, email)
            if not user:
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            
            # 2. 驗證密碼
            if not verify_password(password, user.password):
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            
            # 3. 生成 Token
            token = create_access_token({"sub": str(user.id)})
            
            # 4. 更新登入 token（可選）
            user.login_token = token
            db.commit()
            
            return {"success": True, "message": "登入成功", "token": token}
            
        except Exception as e:
            print(f"登入錯誤: {str(e)}")
            return {"success": False, "message": "登入失敗", "token": None}
    
    
    @staticmethod
    def reset_password_with_old(
        db: Session, 
        user_id: int, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """
        重設密碼（需要提供舊密碼）
        
        Returns:
            True = 成功, False = 失敗
        """
        try:
            # 1. 查詢用戶
            user = AccountModule.get_user_by_id(db, user_id)
            if not user:
                return False
            
            # 2. 驗證舊密碼
            if not verify_password(old_password, user.password):
                print("舊密碼錯誤")
                return False
            
            # 3. 更新密碼
            user.password = hash_password(new_password)
            user.must_change_password = False
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"重設密碼錯誤: {str(e)}")
            db.rollback()
            return False
    
    
    @staticmethod
    def forgot_password(db: Session, email: str, code: str, new_password: str) -> Dict[str, any]:
        """
        忘記密碼（透過驗證碼重設密碼）
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 1. 驗證驗證碼
            if not AccountModule.verify_code(db, email, code):
                return {"success": False, "message": "驗證碼錯誤或已過期"}
            
            # 2. 查詢用戶
            user = AccountModule.get_user_by_email(db, email)
            if not user:
                return {"success": False, "message": "用戶不存在"}
            
            # 3. 更新密碼
            user.password = hash_password(new_password)
            user.must_change_password = False
            db.commit()
            
            return {"success": True, "message": "密碼重設成功"}
            
        except Exception as e:
            print(f"忘記密碼錯誤: {str(e)}")
            db.rollback()
            return {"success": False, "message": "密碼重設失敗"}
    
    
    @staticmethod
    def check_register_status(db: Session, email: str) -> Dict[str, any]:
        """
        檢查註冊狀態
        
        Returns:
            {"exists": bool, "verified": bool, "message": str}
        """
        try:
            user = AccountModule.get_user_by_email(db, email)
            
            if not user:
                return {"exists": False, "verified": False, "message": "帳號不存在"}
            
            return {
                "exists": True,
                "verified": user.verified,
                "message": "帳號已註冊" if user.verified else "帳號已註冊但未驗證"
            }
            
        except Exception as e:
            print(f"檢查註冊狀態錯誤: {str(e)}")
            return {"exists": False, "verified": False, "message": "查詢失敗"}
    
    
    # ========== 驗證碼相關功能 ==========
    
    @staticmethod
    def generate_code() -> str:
        """生成 6 位數驗證碼"""
        return f"{random.randint(100000, 999999)}"
    
    
    @staticmethod
    def send_verification_code(db: Session, email: str) -> Dict[str, any]:
        """
        發送驗證碼（真的發送到 Gmail）
        
        Returns:
            {"success": bool, "message": str, "code": str}
        """
        try:
            # 1. 生成驗證碼
            code = AccountModule.generate_code()
            
            # 2. 設定過期時間（10分鐘）
            expires_at = datetime.now() + timedelta(minutes=10)
            
            # 3. 儲存到資料庫
            verification = VerificationCodeDB(
                email=email,
                code=code,
                expires_at=expires_at,
                is_used=False
            )
            db.add(verification)
            db.commit()
            
            # 4. 🆕 真的發送郵件到 Gmail
            from app.core.email_config import EmailService
            email_sent = EmailService.send_verification_code(email, code)
            
            if not email_sent:
                # 郵件發送失敗，但驗證碼已儲存（開發環境可用）
                print(f"⚠️ [驗證碼] 郵件發送失敗，但驗證碼已生成: {code}")
            
            # 根據規格書，Response 中要顯示驗證碼
            return {"success": True, "message": "成功", "code": code}
            
        except Exception as e:
            print(f"❌ [驗證碼] 發送失敗: {str(e)}")
            db.rollback()
            return {"success": False, "message": "失敗", "code": None}
    
    
    @staticmethod
    def verify_code(db: Session, email: str, code: str) -> bool:
        """
        驗證驗證碼（符合規格書）
        
        Returns:
            True = 驗證成功, False = 驗證失敗
        """
        try:
            # 1. 查詢驗證碼（最新的一筆）
            verification = db.query(VerificationCodeDB).filter(
                VerificationCodeDB.email == email,
                VerificationCodeDB.code == code,
                VerificationCodeDB.is_used == False
            ).order_by(VerificationCodeDB.created_at.desc()).first()
            
            if not verification:
                print(f"[驗證失敗] 驗證碼不存在或已使用 - Email: {email}, Code: {code}")
                return False
            
            # 2. 檢查是否過期
            if verification.expires_at and datetime.now() > verification.expires_at:
                print(f"[驗證失敗] 驗證碼已過期 - Email: {email}, Code: {code}")
                return False
            
            # 3. 標記為已使用
            verification.is_used = True
            
            # 4. 將用戶標記為已驗證
            user = AccountModule.get_user_by_email(db, email)
            if user:
                user.verified = True
            
            db.commit()
            
            print(f"[驗證成功] Email: {email}, Code: {code}, 用戶已驗證")
            return True
            
        except Exception as e:
            print(f"驗證驗證碼錯誤: {str(e)}")
            db.rollback()
            return False
