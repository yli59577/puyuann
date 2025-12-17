# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.account.models import User, VerificationCodeDB
from app._user.models import UserProfile  # 導入 UserProfile 模型
from app.core.security import hash_password, verify_password, create_access_token
from typing import Optional, Dict
from datetime import datetime, timedelta
import random
from common.utils import get_logger

logger = get_logger(__name__)

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
        用戶註冊 - 支持未驗證帳號重新註冊
        
        邏輯：
        - 如果帳號已驗證 → 返回「帳號已存在」
        - 如果帳號未驗證 → 允許重新註冊（更新密碼和驗證過期時間，刪除舊驗證碼）
        - 如果帳號不存在 → 創建新帳號
        
        Returns:
            {"success": bool, "message": str, "user_id": int}
        """
        try:
            from datetime import datetime, timezone, timedelta
            TAIWAN_TZ = timezone(timedelta(hours=8))
            
            # 1. 檢查 email 是否已存在
            existing_user = AccountModule.get_user_by_email(db, email)
            
            if existing_user:
                # 帳號已存在，檢查是否已驗證
                if existing_user.verified:
                    # 帳號已驗證 → 不允許重新註冊
                    logger.info(f"帳號 {email} 已驗證，拒絕重新註冊")
                    return {"success": False, "message": "帳號已經存在", "user_id": None}
                else:
                    # 帳號未驗證 → 允許重新註冊
                    logger.info(f"帳號 {email} 未驗證，允許重新註冊")
                    
                    # 1.1 刪除舊的驗證碼
                    old_verifications = db.query(VerificationCodeDB).filter(
                        VerificationCodeDB.email == email
                    ).all()
                    for old_verification in old_verifications:
                        db.delete(old_verification)
                    logger.debug(f"已刪除 {len(old_verifications)} 條舊驗證碼")
                    
                    # 1.2 更新帳號密碼和驗證過期時間
                    hashed_pwd = hash_password(password)
                    verification_expires_at = datetime.now(TAIWAN_TZ).replace(tzinfo=None) + timedelta(minutes=5)
                    
                    existing_user.password = hashed_pwd
                    existing_user.verification_expires_at = verification_expires_at
                    existing_user.code = None  # 清除舊驗證碼
                    
                    db.commit()
                    db.refresh(existing_user)
                    
                    logger.info(f"帳號 {email} 已更新密碼和驗證過期時間: {verification_expires_at}")
                    return {"success": True, "message": "註冊成功", "user_id": existing_user.id}
            
            # 2. 帳號不存在，創建新帳號
            logger.info(f"帳號 {email} 不存在，創建新帳號")
            
            # 2.1 密碼加密
            hashed_pwd = hash_password(password)
            
            # 2.2 計算驗證過期時間（5分鐘後）
            verification_expires_at = datetime.now(TAIWAN_TZ).replace(tzinfo=None) + timedelta(minutes=5)
            
            # 2.3 創建新用戶 (UserAuth) - 預設未驗證
            new_user = User(
                email=email,
                password=hashed_pwd,
                account=email.split('@')[0],
                verified=False,  # 需要驗證碼驗證後才能登入
                verification_expires_at=verification_expires_at  # 設定驗證過期時間
            )
            db.add(new_user)
            db.flush()

            # 2.4 檢查是否已有 user_profiles，沒有才創建
            existing_profile = db.query(UserProfile).filter(
                UserProfile.user_id == new_user.id
            ).first()
            
            if not existing_profile:
                new_profile = UserProfile(
                    user_id=new_user.id,
                    name=email.split('@')[0]
                )
                db.add(new_profile)
            
            # 2.5 提交交易
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"用戶 {email} 已註冊，驗證過期時間: {verification_expires_at}")
            return {"success": True, "message": "註冊成功", "user_id": new_user.id}
            
        except Exception as e:
            logger.error(f"註冊時發生錯誤: {str(e)}", exc_info=True)
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
            logger.info("--- 登入流程開始 ---")
            # 1. 查詢用戶
            logger.debug(f"步驟 1: 正在資料庫中查詢用戶 {email}...")
            user = AccountModule.get_user_by_email(db, email)
            if not user:
                logger.warning(f"結果: 找不到用戶 {email}。")
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            logger.debug("結果: 已找到用戶。")
            
            # 2. 檢查是否已驗證
            logger.debug("步驟 2: 檢查帳號是否已驗證...")
            if not user.verified:
                logger.warning("結果: 帳號尚未驗證。")
                return {"success": False, "message": "帳號尚未驗證", "token": None}
            logger.debug("結果: 帳號已驗證。")
            
            # 3. 驗證密碼
            logger.debug("步驟 3: 正在驗證密碼...")
            if not verify_password(password, user.password):
                logger.warning("結果: 密碼驗證失敗。")
                return {"success": False, "message": "帳號或密碼錯誤", "token": None}
            logger.debug("結果: 密碼驗證成功。")
            
            # 4. 生成 Token
            logger.debug("步驟 4: 正在生成 JWT Token...")
            token = create_access_token({"sub": str(user.id)})
            logger.debug("結果: Token 生成成功。")
            logger.info("--- 登入流程成功結束 ---")
            
            return {"success": True, "message": "登入成功", "token": token}
            
        except Exception as e:
            logger.error(f"登入流程中發生嚴重錯誤: {str(e)}", exc_info=True)
            db.rollback()  # 發生例外時回滾
            return {"success": False, "message": f"登入失敗: {e}", "token": None}
    
    
    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        """
        重設密碼（不需要舊密碼，透過 Token 驗證身份）
        
        Returns:
            True = 成功, False = 失敗
        """
        try:
            # 1. 查詢用戶
            user = AccountModule.get_user_by_id(db, user_id)
            if not user:
                return False
            
            # 2. 更新密碼
            user.password = hash_password(new_password)
            user.must_change_password = False
            db.commit()
            
            logger.info(f"用戶 {user_id} 密碼已更新")
            return True
            
        except Exception as e:
            logger.error(f"重設密碼錯誤: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    
    @staticmethod
    def forgot_password_send_temp(db: Session, email: str) -> Dict[str, any]:
        """
        忘記密碼 - 發送臨時密碼到郵件
        臨時密碼會取代原本的密碼，用戶登入後可重設密碼
        
        Returns:
            {"success": bool, "message": str}
        """
        try:
            logger.info(f"開始處理: {email}")
            
            # 1. 查詢用戶
            user = AccountModule.get_user_by_email(db, email)
            if not user:
                logger.warning(f"用戶不存在: {email}")
                return {"success": False, "message": "用戶不存在"}
            
            # 2. 生成 6 位數臨時密碼
            temp_password = AccountModule.generate_code()
            logger.debug(f"生成臨時密碼: {temp_password}")
            
            # 3. 用臨時密碼取代原本的密碼
            user.password = hash_password(temp_password)
            user.must_change_password = True  # 標記需要更改密碼
            db.commit()
            logger.debug(f"已更新密碼為臨時密碼")
            
            # 4. 發送臨時密碼到郵件
            from app.core.email_config import EmailService
            email_sent = EmailService.send_temp_password(email, temp_password)
            if email_sent:
                logger.info(f"臨時密碼郵件發送成功")
            else:
                logger.warning(f"郵件發送失敗，但臨時密碼已設定: {temp_password}")
            
            return {"success": True, "message": "成功"}
            
        except Exception as e:
            logger.error(f"錯誤: {str(e)}", exc_info=True)
            db.rollback()
            return {"success": False, "message": "失敗"}
    
    
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
            logger.error(f"檢查註冊狀態錯誤: {str(e)}", exc_info=True)
            return {"exists": False, "verified": False, "message": "查詢失敗"}
    
    
    # ========== 驗證碼相關功能 ==========
    
    @staticmethod
    def generate_code() -> str:
        """生成 6 位數驗證碼"""
        return f"{random.randint(100000, 999999)}"
    
    
    @staticmethod
    def send_verification_code(db: Session, email: str) -> Dict[str, any]:
        """
        發送驗證碼
        
        Returns:
            {"success": bool, "message": str, "code": str}
        """
        try:
            logger.info(f"開始發送驗證碼到: {email}")
            
            # 1. 生成驗證碼
            code = AccountModule.generate_code()
            logger.debug(f"生成驗證碼: {code}")
            
            # 2. 所有驗證碼都存到 verification_codes 表
            verification = VerificationCodeDB(
                email=email,
                code=code,
                expires_at=datetime.now() + timedelta(minutes=10),
                is_used=False
            )
            db.add(verification)
            logger.debug(f"驗證碼已存到 verification_codes 表")
            
            db.commit()
            logger.debug(f"已儲存到資料庫")
            
            # 發送郵件
            from app.core.email_config import EmailService
            email_sent = EmailService.send_verification_code(email, code)
            if email_sent:
                logger.info(f"郵件發送成功")
            else:
                logger.warning(f"郵件發送失敗，但驗證碼已儲存: {code}")
            
            return {"success": True, "message": "成功", "code": code}
            
        except Exception as e:
            logger.error(f"發送失敗: {str(e)}", exc_info=True)
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
            logger.debug(f"開始驗證 - Email: {email}, Code: {code}")
            
            # 1. 先檢查 UserAuth.code（已註冊用戶）
            user = AccountModule.get_user_by_email(db, email)
            if user:
                logger.debug(f"找到用戶，資料庫中的 code: '{user.code}', 輸入的 code: '{code}'")
                # 確保兩邊都是字串並去除空白
                db_code = str(user.code).strip() if user.code else None
                input_code = str(code).strip() if code else None
                logger.debug(f"比對: db_code='{db_code}' vs input_code='{input_code}'")
                
                if db_code and input_code and db_code == input_code:
                    logger.info(f"從 UserAuth.code 驗證成功")
                    user.verified = True
                    user.code = None  # 清除驗證碼
                    db.commit()
                    return True
                else:
                    logger.debug(f"UserAuth.code 不匹配，繼續檢查 verification_codes 表")
            else:
                logger.debug(f"用戶不存在，檢查 verification_codes 表")
            
            # 2. 再檢查 verification_codes 表（未註冊用戶）
            verification = db.query(VerificationCodeDB).filter(
                VerificationCodeDB.email == email,
                VerificationCodeDB.code == code,
                VerificationCodeDB.is_used == False
            ).order_by(VerificationCodeDB.created_at.desc()).first()
            
            if not verification:
                logger.warning(f"驗證碼不存在或已使用 - Email: {email}, Code: {code}")
                return False
            
            # 3. 檢查是否過期
            if verification.expires_at and datetime.now() > verification.expires_at:
                logger.warning(f"驗證碼已過期 - Email: {email}, Code: {code}")
                return False
            
            # 4. 標記為已使用
            verification.is_used = True
            
            # 5. 將用戶標記為已驗證，並清除驗證過期時間
            if user:
                user.verified = True
                user.verification_expires_at = None  # 清除驗證過期時間
            
            db.commit()
            
            logger.info(f"Email: {email}, Code: {code}, 用戶已驗證")
            return True
            
        except Exception as e:
            logger.error(f"驗證驗證碼錯誤: {str(e)}", exc_info=True)
            db.rollback()
            return False
