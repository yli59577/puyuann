from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from app.account.models import User, VerificationCodeDB, get_taiwan_time
from app.core.security import hash_password, vertify_password, generate_verification_code
import random
# 台灣時區
TAIWAN_TZ = timezone(timedelta(hours=8))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AccountService:
    """帳號服務類別"""
    
    @staticmethod
    def check_email_exists(db: Session, email: str) -> bool:
        """檢查信箱是否已存在"""
        user = db.query(User).filter(User.email == email).first()
        return user is not None
    
    @staticmethod
    def create_user(db: Session, email: str, password: str) -> User:
        """創建新用戶"""
        hashed_pwd = hash_password(password)
        user = User(email=email, hashed_password=hashed_pwd)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    


    def vertify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證密碼"""
        return pwd_context.verify(plain_password, hashed_password)



    def vertify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證密碼"""
        return pwd_context.verify(plain_password, hashed_password)
    @staticmethod
    def create_verification_code(db: Session, email: str) -> str:
            """生成隨機驗證碼並儲存到資料庫"""
            # 生成 6 位數字的隨機驗證碼
            code = f"{random.randint(100000, 999999)}"
            
            # 儲存到資料庫
            verification_code = VerificationCodeDB(
                email=email,
                code=code,
                created_at=get_taiwan_time(),  # 使用台灣時間
                is_used=False  # 確保驗證碼未使用
            )
            db.add(verification_code)
            db.commit()
            db.refresh(verification_code)
            return code

    @staticmethod
    def reset_password(db: Session, user_id: int, old_password: str, new_password: str) -> bool:
        """重設密碼"""
        print(f"查找用戶 ID: {user_id}")  # Debug
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"找不到用戶 ID: {user_id}")  # Debug
            return False
        
        print(f"找到用戶: {user.email}")  # Debug
        print(f"驗證舊密碼...")  # Debug
        
        if not vertify_password(old_password, user.hashed_password):
            print(f"舊密碼驗證失敗")  # Debug
            return False
        
        print(f"舊密碼驗證成功，更新新密碼")  # Debug
        
        user.hashed_password = hash_password(new_password)
        db.commit()
        
        print(f"密碼更新完成")  # Debug
        return True
        @staticmethod
        def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
            """根據 ID 取得用戶"""
            return db.query(User).filter(User.id == user_id).first()