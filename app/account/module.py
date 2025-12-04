# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User, VerificationCodeDB
from app._user.models import UserProfile  # 導入 UserProfile 模型
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
            
            # 3. 創建新用戶 (UserAuth) - 預設未驗證
            new_user = User(
                email=email,
                password=hashed_pwd,
                account=email.split('@')[0],
                verified=False  # 需要驗證碼驗證後才能登入
            )
            db.add(new_user)
            
            # 為了獲取 new_user.id，我們需要先 flush 到資料庫
            db.flush()

            # 4. 檢查是否已有 user_profiles，沒有才創建
            existing_profile = db.query(UserProfile).filter(
                UserProfile.user_id == new_user.id
            ).first()
            
            if not existing_profile:
                new_profile = UserProfile(
                    user_id=new_user.id,
                    name=email.split('@')[0]
                )
                db.add(new_profile)
            
            # 5. 提交交易
            db.commit()
            db.refresh(new_user)
            
            return {"success": True, "message": "註冊成功", "user_id": new_user.id}
            
        except Exception as e:
            print(f"註冊時發生錯誤: {str(e)}")
            db.rollback()
            return {"success": False, "message": f"註冊失敗: {e}", "user_id": None}
    
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> Dict[str, any]:
        """
        用戶登入
        
        Returns:
            {"success": bool, "message": str, "token": str}
        """
        try:
            print("--- [登入流程開始] ---")
            # 1. 查詢用戶
            print(f"步驟 1: 正在資料庫中查詢用戶 {email}...")
            user = AccountModule.get_user_by_email(db, email)
            if not user:
                print(f"結果: 找不到用戶 {email}。")
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            print("結果: 已找到用戶。")
            
            # 2. 檢查是否已驗證
            print("步驟 2: 檢查帳號是否已驗證...")
            if not user.verified:
                print("結果: 帳號尚未驗證。")
                return {"success": False, "message": "帳號尚未驗證", "token": None}
            print("結果: 帳號已驗證。")
            
            # 3. 驗證密碼
            print("步驟 3: 正在驗證密碼...")
            if not verify_password(password, user.password):
                print("結果: 密碼驗證失敗。")
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            print("結果: 密碼驗證成功。")
            
            # 4. 生成 Token
            print("步驟 4: 正在生成 JWT Token...")
            token = create_access_token({"sub": str(user.id)})
            print("結果: Token 生成成功。")
            print("--- [登入流程成功結束] ---")
            
            return {"success": True, "message": "登入成功", "token": token}
            
        except Exception as e:
            print(f"登入流程中發生嚴重錯誤: {str(e)}")
            db.rollback()  # 發生例外時回滾
            return {"success": False, "message": f"登入失敗: {e}", "token": None}
    
    
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
        發送驗證碼 - 直接存到 UserAuth.code 欄位
        
        Returns:
            {"success": bool, "message": str, "code": str}
        """
        try:
            # 1. 生成驗證碼
            code = AccountModule.generate_code()
            
            # 2. 查詢用戶，將驗證碼存到 UserAuth.code
            user = AccountModule.get_user_by_email(db, email)
            if user:
                # 用戶已存在，更新 code
                user.code = code
            else:
                # 用戶不存在，先創建一個未完成註冊的用戶記錄
                # 或者只是暫存驗證碼（這裡選擇存到 verification_codes 表作為備用）
                verification = VerificationCodeDB(
                    email=email,
                    code=code,
                    expires_at=datetime.now() + timedelta(minutes=10),
                    is_used=False
                )
                db.add(verification)
            
            db.commit()
            
            print(f"[驗證碼] 已生成並儲存: email={email}, code={code}")
            
            # 發送郵件
            from app.core.email_config import EmailService
            email_sent = EmailService.send_verification_code(email, code)
            if not email_sent:
                print(f"[驗證碼] 郵件發送失敗，但驗證碼已儲存: {code}")
            
            # 根據規格書，Response 中要顯示驗證碼
            return {"success": True, "message": "成功", "code": code}
            
        except Exception as e:
            print(f"[驗證碼] 發送失敗: {str(e)}")
            db.rollback()
            return {"success": False, "message": "失敗", "code": None}
    
    
    @staticmethod
    def verify_code(db: Session, email: str, code: str) -> bool:
        """
        驗證驗證碼 - 優先檢查 UserAuth.code，備用檢查 verification_codes 表
        
        Returns:
            True = 驗證成功, False = 驗證失敗
        """
        try:
            # 1. 優先檢查 UserAuth.code
            user = AccountModule.get_user_by_email(db, email)
            if user and user.code == code:
                # 驗證成功，清除 code 並標記為已驗證
                user.code = None
                user.verified = True
                db.commit()
                print(f"[驗證成功] 使用 UserAuth.code - Email: {email}")
                return True
            
            # 2. 備用：檢查 verification_codes 表（用於尚未註冊的用戶）
            verification = db.query(VerificationCodeDB).filter(
                VerificationCodeDB.email == email,
                VerificationCodeDB.code == code,
                VerificationCodeDB.is_used == False
            ).order_by(VerificationCodeDB.created_at.desc()).first()
            
            if not verification:
                print(f"[驗證失敗] 驗證碼不存在或已使用 - Email: {email}, Code: {code}")
                return False
            
            # 3. 檢查是否過期
            if verification.expires_at and datetime.now() > verification.expires_at:
                print(f"[驗證失敗] 驗證碼已過期 - Email: {email}, Code: {code}")
                return False
            
            # 4. 標記為已使用
            verification.is_used = True
            
            # 5. 如果用戶存在，標記為已驗證
            if user:
                user.verified = True
            
            db.commit()
            
            print(f"[驗證成功] 使用 verification_codes 表 - Email: {email}")
            return True
            
        except Exception as e:
            print(f"驗證驗證碼錯誤: {str(e)}")
            db.rollback()
            return False
