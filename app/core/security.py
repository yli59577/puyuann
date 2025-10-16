import os
import bcrypt
import jwt
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta

# 載入環境變數
load_dotenv()

# 修正 ACCESS_TOKEN_EXPIRE_HOURS 未定義的問題
ACCESS_TOKEN_EXPIRE_HOURS = 1  # 預設為 1 小時

def hash_password(password: str) -> str:
    """雜湊密碼"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def vertify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """創建 JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def vertify_token(token: str):
    """驗證 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def generate_verification_code() -> str:
    """生成6位數驗證碼"""
    return ''.join(random.choices(string.digits, k=6))



SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"