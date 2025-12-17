# -*- coding: utf-8 -*-
"""
Common utilities and logging functions
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

# 定義台灣時區 UTC+8
TAIWAN_TZ = timezone(timedelta(hours=8))

# ==================== Logging 配置 ====================

def get_logger(name: str) -> logging.Logger:
    """
    取得指定名稱的 logger
    
    Args:
        name (str): logger 名稱（通常使用 __name__）
    
    Returns:
        logging.Logger: logger 物件
    """
    return logging.getLogger(name)


# ==================== 時間相關函式 ====================

def get_taiwan_time() -> datetime:
    """
    取得台灣時間 (UTC+8)，精確到秒，去除時區資訊
    
    Returns:
        台灣時間 (datetime 物件)
    """
    return datetime.now(TAIWAN_TZ).replace(tzinfo=None, microsecond=0)


def get_taiwan_time_iso() -> str:
    """
    取得台灣時間的 ISO 格式字符串
    
    Returns:
        ISO 格式的時間字符串
    """
    return get_taiwan_time().isoformat()


# ==================== 數據驗證函式 ====================

def is_valid_email(email: str) -> bool:
    """
    驗證電子郵件格式
    
    Args:
        email: 電子郵件地址
    
    Returns:
        是否有效
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone: str) -> bool:
    """
    驗證電話號碼格式 (台灣格式)
    
    Args:
        phone: 電話號碼
    
    Returns:
        是否有效
    """
    import re
    # 支援多種台灣電話格式
    pattern = r'^(\+886|0)[0-9]{9,10}$'
    return re.match(pattern, phone.replace('-', '').replace(' ', '')) is not None


def is_valid_password(password: str, min_length: int = 6) -> bool:
    """
    驗證密碼強度
    
    Args:
        password: 密碼
        min_length: 最小長度 (預設: 6)
    
    Returns:
        是否有效
    """
    if len(password) < min_length:
        return False
    return True


# ==================== 字符串處理函式 ====================

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截斷字符串
    
    Args:
        text: 原始字符串
        max_length: 最大長度
        suffix: 後綴 (預設: "...")
    
    Returns:
        截斷後的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    安全地從字典中獲取值
    
    Args:
        data: 字典
        key: 鍵
        default: 預設值
    
    Returns:
        值或預設值
    """
    return data.get(key, default) if isinstance(data, dict) else default


# ==================== 數據轉換函式 ====================

def to_int(value: Any, default: int = 0) -> int:
    """
    將值轉換為整數
    
    Args:
        value: 值
        default: 預設值
    
    Returns:
        整數值
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    """
    將值轉換為浮點數
    
    Args:
        value: 值
        default: 預設值
    
    Returns:
        浮點數值
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_bool(value: Any, default: bool = False) -> bool:
    """
    將值轉換為布爾值
    
    Args:
        value: 值
        default: 預設值
    
    Returns:
        布爾值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return value != 0
    return default
