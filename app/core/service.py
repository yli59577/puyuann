from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.account.models import User, VerificationCodeDB
from app.core.security import hash_password, vertify_password, generate_verification_code

# 台灣時區
TAIWAN_TZ = timezone(timedelta(hours=8))

class AccountService:
    @staticmethod
    def check_email_exists(db: Session, email: str) -> bool:
        """檢查信箱是否已存在"""
        user = db.query(User).filter(User.email == email).first()
        return user is not None

    @staticmethod
    def create_user(db: Session, email: str, password: str) -> User:
        """創建新用戶"""
        hashed_password = hash_password(password)
        new_user = User(email=email, hashed_password=hashed_password, created_at=datetime.now(TAIWAN_TZ))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """驗證用戶信箱和密碼"""
        user = db.query(User).filter(User.email == email).first()
        if user and vertify_password(password, user.hashed_password):
            return user
        return None

    @staticmethod
    def create_verification_code(db: Session, email: str) -> str:
        """生成隨機驗證碼並儲存到資料庫"""
        code = generate_verification_code()
        verification_code = VerificationCodeDB(
            email=email,
            code=code,
            created_at=datetime.now(TAIWAN_TZ),
            is_used=False
        )
        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)
        return code

    @staticmethod
    def verify_code(db: Session, email: str, code: str) -> bool:
        """驗證驗證碼是否正確"""
        verification = db.query(VerificationCodeDB).filter(
            and_(
                VerificationCodeDB.email == email,
                VerificationCodeDB.code == code,
                VerificationCodeDB.is_used == False
            )
        ).first()
        if not verification:
            return False

        # 檢查驗證碼是否過期（假設有效期為 10 分鐘）
        expiration_time = verification.created_at + timedelta(minutes=10)
        if datetime.now(TAIWAN_TZ) > expiration_time:
            return False

        # 更新驗證碼狀態為已使用
        verification.is_used = True
        db.commit()
        return True