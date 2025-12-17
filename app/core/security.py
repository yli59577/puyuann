import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
import random
import string

# 載入 .env 檔案中的環境變數
load_dotenv()

# --- JWT 配置 ---
# 從環境變數讀取設定，這是唯一的設定來源
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 24))

# 檢查 SECRET_KEY 是否成功載入
if not SECRET_KEY:
    raise ValueError("錯誤：找不到 SECRET_KEY，請檢查您的 .env 檔案。")

def hash_password(password: str) -> str:
    """暫時停用密碼加密，直接返回明文密碼"""
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """暫時停用密碼驗證，直接比對明文密碼"""
    return plain_password == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """創建 JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    # 使用從 .env 讀取的設定來產生 token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """驗證 JWT token"""
    try:
        # 使用從 .env 讀取的設定來驗證 token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (JWTError, ExpiredSignatureError):
        return None

def generate_verification_code() -> str:
    """生成6位數驗證碼"""
    return ''.join(random.choices(string.digits, k=6))