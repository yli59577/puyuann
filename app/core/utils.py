from datetime import datetime, timezone, timedelta
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from app.core.email_config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD
# 台灣時區
TAIWAN_TZ = timezone(timedelta(hours=8))

def format_taiwan_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    將 datetime 物件格式化為台灣時間字串
    
    Args:
        dt: datetime 物件
        
    Returns:
        格式化的時間字串 (YYYY-MM-DD HH:MM:SS UTC+8)
    """
    if dt is None:
        return None

    # 如果沒有時區資訊，假設為 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 轉換為台灣時間
    taiwan_time = dt.astimezone(TAIWAN_TZ)
    
    # 格式化為字串
    return taiwan_time.strftime('%Y-%m-%d %H:%M:%S UTC+8')

def get_taiwan_now() -> datetime:
    """取得當前台灣時間"""
    return datetime.now(TAIWAN_TZ)

def taiwan_now_string() -> str:
    """取得當前台灣時間字串"""
    return format_taiwan_datetime(get_taiwan_now())




def send_email(to_email: str, subject: str, body: str):
    """發送電子郵件"""
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        # 連接到 Gmail SMTP 伺服器
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # 啟用加密
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        print(f"成功發送電子郵件到 {to_email}")
    except Exception as e:
        print(f"發送電子郵件失敗: {str(e)}")