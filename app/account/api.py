# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.account.models import (
    UserRegister, UserLogin, PasswordReset, PasswordForgot,
    VerificationSend, VerificationCheck,
    BaseResponse, RegisterResponse, TokenResponse, VerificationSendResponse
)
from app.account.module import AccountModule
from app._user.module import UserModule
from typing import Optional

router = APIRouter()


@router.post("/register", response_model=BaseResponse, summary="用戶註冊", tags=["用戶身份"])
def register_user(
    request: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用戶註冊（使用 Request Body）
    
    - **email**: 電子郵件（唯一）
    - **password**: 密碼（至少6位）
    - **code**: 驗證碼（可選）
    
    ### 範例請求：
    ```json
    POST /api/register
    Content-Type: application/json
    
    {
        "email": "test@example.com",
        "password": "Test123456"
    }
    ```
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "message": "成功"
    }
    ```
    
    ### 失敗範例：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    """
    result = AccountModule.register_user(db, request.email, request.password)
    
    if result["success"]:
        return BaseResponse(
            status="0",
            message="成功"
        )
    else:
        return BaseResponse(
            status="1",
            message="失敗"
        )


@router.get("/register/check",response_model=BaseResponse, summary="註冊確認", tags=["用戶身份"])
def check_register(email: str, db: Session = Depends(get_db)):
    """
    檢查帳號註冊狀態
    
    - **email**: 電子郵件（Query Parameter）
    
    ### Response 說明：
    - **status**: "0" = 帳號已註冊, "1" = 帳號不存在
    - **message**: 訊息（帳號已註冊/帳號已註冊但未驗證/帳號不存在）
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "message": "帳號已註冊"
    }
    ```
    
    ### 失敗範例：
    ```json
    {
        "status": "1",
        "message": "帳號不存在"
    }
    ```
    """
    result = AccountModule.check_register_status(db, email)
    
    if result["exists"]:
        return BaseResponse(status="0", message=result["message"])
    else:
        return BaseResponse(status="1", message=result["message"])


@router.post("/auth", summary="用戶登入", tags=["用戶身份"])
def login_user(request: UserLogin, db: Session = Depends(get_db)):
    """
    用戶登入
    
    - **email**: 電子郵件
    - **password**: 密碼
    
    ### 範例請求：
    ```json
    POST /api/auth
    Content-Type: application/json
    
    {
        "email": "qqqq@qq.com",
        "password": "1234"
    }
    ```
    
    ### 成功範例（符合規格書）：
    ```json
    {
        "status": "0",
        "token": "eyJhbGciOiJIUzI1NiJ9....."
    }
    ```
    
    ### 失敗範例（符合規格書）：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    """
    result = AccountModule.login_user(db, request.email, request.password)
    
    if result["success"]:
        return {
            "status": "0",
            "token": result["token"]
        }
    else:
        return {
            "status": "1",
            "message": "登入失敗，帳號或密碼錯誤"
        }


@router.post("/password/reset", response_model=BaseResponse, summary="重設密碼", tags=["用戶身份"])
def reset_password(
    request: PasswordReset,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    重設密碼（需要舊密碼）
    
    - **需要 Bearer Token**
    - **oldPassword**: 舊密碼
    - **newPassword**: 新密碼（至少6位）
    
    ### 範例請求：
    ```json
    POST /api/password/reset
    Authorization: Bearer {token}
    Content-Type: application/json
    
    {
        "oldPassword": "1234",
        "newPassword": "5678"
    }
    ```
    
    ### 成功範例（符合規格書）：
    ```json
    {
        "status": "0",
        "message": "成功"
    }
    ```
    
    ### 失敗範例（符合規格書）：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    """
    # 1. 解析 Token 獲取用戶 ID
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="失敗")
    
    # 2. 重設密碼
    success = AccountModule.reset_password_with_old(
        db, user_id, request.oldPassword, request.newPassword
    )
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.post("/password/forgot", response_model=BaseResponse, summary="忘記密碼", tags=["用戶身份"])
def forgot_password(request: PasswordForgot, db: Session = Depends(get_db)):
    """
    忘記密碼（透過驗證碼重設密碼）
    
    - **email**: 電子郵件
    
    ### 範例請求（符合規格書）：
    ```json
    POST /api/password/forgot
    Content-Type: application/json
    
    {
        "email": "example@gmail.com"
    }
    ```
    
    ### Response 說明（符合規格書）：
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "message": "成功"
    }
    ```
    
    ### 失敗範例：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    
    ### 流程：
    1. 使用者呼叫此 API 提供 email
    2. 系統發送重設密碼的驗證碼到信箱
    """
    # 發送驗證碼到信箱
    result = AccountModule.send_verification_code(db, request.email)
    
    if result["success"]:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.post("/verification/send", response_model=VerificationSendResponse, response_model_exclude_none=True, summary="發送驗證碼", tags=["用戶身份"])
def send_verification(request: VerificationSend, db: Session = Depends(get_db)):
    """
    發送驗證碼到郵箱
    
    - **email**: 電子郵件
    
    ### 範例請求：
    ```json
    POST /api/verification/send
    Content-Type: application/json
    
    {
        "email": "qqqq@qq.com"
    }
    ```
    
    ### Response 說明（符合規格書欄位順序）：
    - **status**: "0" = 成功, "1" = 失敗
    - **code**: 六位數驗證碼（例如：089682）
    - **message**: 訊息
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "code": "089682",
        "message": "成功"
    }
    ```
    
    ### 失敗範例：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    """
    result = AccountModule.send_verification_code(db, request.email)
    
    if result["success"]:
        return VerificationSendResponse(
            status="0",
            code=result["code"],
            message="成功"
        )
    else:
        return VerificationSendResponse(
            status="1",
            code=None,
            message="失敗"
        )


@router.post("/verification/check", response_model=BaseResponse, summary="檢查驗證碼", tags=["用戶身份"])
def check_verification(request: VerificationCheck, db: Session = Depends(get_db)):
    """
    檢查驗證碼是否正確
    
    - **email**: 電子郵件
    - **code**: 驗證碼（六位數字）
    
    ### Response 說明（符合規格書）：
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "message": "成功"
    }
    ```
    
    ### 失敗範例：
    ```json
    {
        "status": "1",
        "message": "失敗"
    }
    ```
    """
    success = AccountModule.verify_code(db, request.email, request.code)
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")