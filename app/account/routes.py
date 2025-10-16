from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from sqlalchemy.sql.expression import and_
from app.core.database import get_db
from app.account.models import *
from app.account.service import AccountService
from app.core.utils import send_email
router = APIRouter(prefix="/api", tags=["account"])
from app.core.security import vertify_token, create_access_token, vertify_password
from jose import jwt
from datetime import datetime, timedelta



@router.get("/register/check")
async def register_check(email: str, db: Session = Depends(get_db)):
    """註冊確認 - 檢查信箱是否已存在"""
    try:
        exists = AccountService.check_email_exists(db, email)
        if exists:
            return {"status": "0", "message": "成功"}
        return {"status": "1", "message": "失敗"}
    except Exception:
        return {"status": "1", "message": "失敗"}

@router.post("/register")
async def register(request: UserCreate, db: Session = Depends(get_db)):
    """用戶註冊"""
    try:
        # 檢查信箱是否已存在
        if AccountService.check_email_exists(db, request.email):
            return {
                "status": "1",
                "message": "失敗",
                "payload": {"reason": "信箱已存在", "email": request.email}
            }
        
        # 創建新用戶
        AccountService.create_user(db, request.email, request.password)
        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"註冊錯誤: {str(e)}")  # 調試用
        return {"status": "1", "message": "失敗"}
    
@router.post("/verification/send")
async def send_verification(request: VerificationBase, db: Session = Depends(get_db)):
    """發送驗證碼"""
    try:
        # 檢查信箱是否已存在
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return {"status": "1", "message": "電子郵件不存在"}

        # 生成隨機驗證碼
        code = AccountService.create_verification_code(db, request.email)
        print(f"生成的驗證碼: {code}")  # 調試用

        # 返回驗證碼到 payload
        return {"status": "0", "code": code, "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")  # 調試用
        return {"status": "1", "message": "失敗"}
@router.post("/verification/check")
async def check_verification(request: VerificationCode, db: Session = Depends(get_db)):
    """檢查驗證碼"""
    try:
        print(f"收到請求: email={request.email}, code={request.code}")  # 調試用

        # 查詢資料庫中的驗證碼
        verification = db.query(VerificationCodeDB).filter(
            and_(
                VerificationCodeDB.email == request.email,
                VerificationCodeDB.code == request.code,
                VerificationCodeDB.is_used == False
            )
        ).first()

        print(f"查詢結果: {verification}")  # 調試用

        # 如果驗證碼不存在或已使用，返回失敗    
        if not verification:
            return {"status": "1", "message": "驗證碼無效或已使用"}

        # 檢查驗證碼是否過期（假設驗證碼有效期為 10 分鐘）
        expiration_time = verification.created_at + timedelta(minutes=10)
        print(f"驗證碼過期時間: {expiration_time}")  # 調試用

        if datetime.now() > expiration_time:
            return {"status": "1", "message": "驗證碼已過期"}

        # 更新驗證碼狀態為已使用
        verification.is_used = True
        db.commit()
        print(f"驗證碼狀態更新成功: {verification.is_used}")  # 調試用

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")  # 調試用
        return {"status": "1", "message": "失敗"}
    
@router.post("/auth")
async def login(request: UserLogin, db: Session = Depends(get_db)):
    """用戶登入"""
    try:
        # 檢查信箱是否存在
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return {"status": "1", "message": "帳號未註冊"}

        # 驗證密碼是否正確
        if not vertify_password(request.password, user.hashed_password):
            return {"status": "1", "message": "密碼錯誤"}

        # 生成 Token
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        return {"status": "0", "token": token, "message": "登入成功"}
    except Exception as e:
        print(f"登入錯誤: {str(e)}")  # 調試用
        return {"status": "1", "message": "登入失敗"}
@router.post("/password/reset")
async def reset_password(
    request: PasswordReset, 
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """重設密碼 (需要 Bearer Token)"""
    try:
        print(f" 收到的 Authorization header: {authorization}")  # Debug
        
        # 1. 檢查 Authorization Header
        if not authorization or not authorization.startswith("Bearer "):
            print(" Authorization header 格式錯誤")  # Debug
            return {"status": "1", "message": "失敗"}
        
        # 2. 解析 token
        token = authorization.split(" ")[1]
        print(f" 解析出的 token: {token[:50]}...")  # Debug (只顯示前50字元)
        
        payload = vertify_token(token)
        print(f"Token payload: {payload}")  # Debug
        
        if not payload:
            print(" Token 驗證失敗")  # Debug
            return {"status": "1", "message": "失敗"}
        
        # 3. 從 token 取得 user_id
        user_id = int(payload.get("sub"))
        print(f" 用戶 ID: {user_id}")  # Debug
        
        # 4. 執行密碼重設
        print(f" 嘗試重設密碼，舊密碼: {request.oldPassword}")  # Debug
        
        success = AccountService.reset_password(
            db, user_id, request.oldPassword, request.newPassword
        )
        
        print(f"密碼重設結果: {success}")  # Debug
        
        if success:
            return {"status": "0", "message": "成功"}
        return {"status": "1", "message": "失敗"}
        
    except Exception as e:
        print(f" 重設密碼錯誤: {str(e)}")  # Debug
        return {"status": "1", "message": "失敗"}

@router.post("/password/forgot")
async def forgot_password(request: VerificationBase, db: Session = Depends(get_db)):
    """忘記密碼 API"""
    try:
        # 檢查電子郵件是否存在
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return {"status": "1", "message": "電子郵件不存在"}

        # 生成驗證碼並儲存到資料庫
        code = AccountService.create_verification_code(db, request.email)

        # 發送驗證碼到 Gmail
        subject = "重置密碼驗證碼"
        body = f"您的重置密碼驗證碼是：{code}"
        send_email(request.email, subject, body)

        return {"status": "0", "message": "重置密碼的驗證碼已發送"}
    except Exception as e:
        print(f"錯誤: {str(e)}")  # 調試用
        return {"status": "1", "message": "失敗"}
@router.get("/user")
async def get_user_info(user_id: int, db: Session = Depends(get_db)):
    """查看個人資訊"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "1", "message": "失敗"}

        return {
            "status": "0",
            "user": user.to_dict(),
            "message": "ok"
        }
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("/user")
async def update_user_info(request: dict, db: Session = Depends(get_db)):
    """更新個人資料"""
    try:
        user = db.query(User).filter(User.id == request.get("id")).first()
        if not user:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("/user/default")
async def update_user_defaults(request: dict, db: Session = Depends(get_db)):
    """更新個人預設值"""
    try:
        user_defaults = db.query(UserDefaults).filter(UserDefaults.user_id == request.get("user_id")).first()
        if not user_defaults:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user_defaults, key):
                setattr(user_defaults, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("/user/setting")
async def update_user_settings(request: dict, db: Session = Depends(get_db)):
    """更新個人設定"""
    try:
        user_settings = db.query(UserSettings).filter(UserSettings.user_id == request.get("user_id")).first()
        if not user_settings:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user_settings, key):
                setattr(user_settings, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}