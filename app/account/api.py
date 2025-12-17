# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.account.models import (
    UserRegister, UserLogin, PasswordReset, PasswordForgot,
    VerificationSend, VerificationCheck,
    BaseResponse, RegisterResponse, TokenResponse, VerificationSendResponse, CheckRegisterResponse
)
from app.account.module import AccountModule
from app._user.module import UserModule
from typing import Optional
from common.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=BaseResponse, summary="用戶註冊", tags=["用戶身份"])
def register_user(
    request: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用戶註冊（使用 Request Body）
    
    - **email**: 電子郵件（唯一）
    - **password**: 密碼（至少6位）`
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
        # 返回具體的錯誤訊息
        return BaseResponse(
            status="1",
            message=result["message"]
        )


@router.get("/register/check", response_model=BaseResponse, summary="檢查帳號是否可以註冊", tags=["用戶身份"])
def check_register(email: str, db: Session = Depends(get_db)):
    """
    檢查帳號是否可以註冊
    
    - **email**: 電子郵件（Query Parameter）
    
    ### Response 說明：
    - **status**: 
      - "0" = 帳號可以註冊（不存在或未驗證）
      - "1" = 帳號已存在且已驗證（不能註冊）
    - **message**: 訊息
    
    ### 可以註冊範例（帳號不存在）：
    ```json
    {
        "status": "0",
        "message": "帳號可以註冊"
    }
    ```
    
    ### 可以重新註冊範例（帳號未驗證）：
    ```json
    {
        "status": "0",
        "message": "帳號未驗證，可以重新註冊"
    }
    ```
    
    ### 不能註冊範例（帳號已驗證）：
    ```json
    {
        "status": "1",
        "message": "帳號已存在"
    }
    ```
    """
    try:
        result = AccountModule.check_register_status(db, email)
        logger.debug(f"check_register_status 返回: {result}")
        
        # 帳號不存在 → status = "0"（可以註冊）
        if not result["exists"]:
            response = BaseResponse(status="0", message="帳號可以註冊")
            logger.debug("帳號不存在，允許註冊")
        # 帳號已驗證 → status = "1"（不能註冊）
        elif result["verified"]:
            response = BaseResponse(status="1", message="帳號已存在")
            logger.debug("帳號已驗證，不允許註冊")
        # 帳號未驗證 → status = "0"（可以重新註冊）
        else:
            response = BaseResponse(status="0", message="帳號未驗證，可以重新註冊")
            logger.debug("帳號未驗證，允許重新註冊")
        
        response_dict = response.model_dump()
        response_json = response.model_dump_json()
        logger.debug(f"返回的 response dict: {response_dict}")
        logger.debug(f"返回的 response JSON: {response_json}")
        return response
    except Exception as e:
        logger.error(f"check_register 錯誤: {str(e)}", exc_info=True)
        return BaseResponse(status="1", message="查詢失敗")


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
    重設密碼（只需要新密碼）
    
    - **需要 Bearer Token**
    - **password**: 新密碼（至少6位）
    
    ### 範例請求：
    ```json
    POST /api/password/reset
    Authorization: Bearer {token}
    Content-Type: application/json
    
    {
        "password": "新密碼"
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
    # 1. 解析 Token 獲取用戶 ID
    user_id = UserModule.parse_user_id_from_token(authorization)
    if not user_id:
        return BaseResponse(status="1", message="失敗")
    
    # 2. 直接重設密碼（不需要舊密碼）
    success = AccountModule.reset_password(db, user_id, request.password)
    
    if success:
        return BaseResponse(status="0", message="成功")
    else:
        return BaseResponse(status="1", message="失敗")


@router.post("/password/forgot", response_model=BaseResponse, summary="忘記密碼", tags=["用戶身份"])
def forgot_password(request: PasswordForgot, db: Session = Depends(get_db)):
    """
    忘記密碼 - 發送臨時密碼到郵件
    
    - **email**: 電子郵件
    
    ### 範例請求：
    ```json
    POST /api/password/forgot
    Content-Type: application/json
    
    {
        "email": "example@gmail.com"
    }
    ```
    
    ### Response 說明：
    - **status**: "0" = 成功, "1" = 失敗
    - **message**: 訊息
    
    ### 成功範例：
    ```json
    {
        "status": "0",
        "message": "成功"
    }
    ```
    
    ### 流程：
    1. 使用者呼叫此 API 提供 email
    2. 系統生成 6 位數臨時密碼
    3. 臨時密碼取代原本的密碼
    4. 發送臨時密碼到郵件
    5. 用戶使用臨時密碼登入後可重設密碼
    """
    result = AccountModule.forgot_password_send_temp(db, request.email)
    
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