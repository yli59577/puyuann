# -*- coding: utf-8 -*-
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from common.utils import get_logger

logger = get_logger(__name__)
# 載入環境變數
load_dotenv()

# Gmail SMTP 設定（從環境變數讀取）
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "yli59577@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "vxby hzle nhmb frhj")
SEND_EMAIL = os.getenv("SEND_EMAIL", "true").lower() == "true"  


class EmailService:
    """郵件服務"""
    
    @staticmethod
    def send_verification_code(to_email: str, code: str) -> bool:
        """
        發送驗證碼郵件到 Gmail
        
        Args:
            to_email: 收件人 email
            code: 六位數驗證碼
            
        Returns:
            True = 發送成功, False = 發送失敗
        """
        try:
            # 檢查是否啟用郵件發送
            if not SEND_EMAIL:
                logger.info(f"郵件發送已停用 (SEND_EMAIL=false)")
                return False
            
            logger.info(f"準備發送驗證碼到: {to_email}")
            logger.debug(f"SMTP設定: {SMTP_SERVER}:{SMTP_PORT}, 寄件人: {SMTP_EMAIL}")
            
            # 建立郵件內容
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = to_email
            msg['Subject'] = "【普元健康】驗證碼通知"
            
            # HTML 郵件內容
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
                        <h2 style="color: #333;">普元健康 - 驗證碼</h2>
                        <p style="font-size: 16px; color: #555;">您的驗證碼是：</p>
                        <div style="background-color: #007bff; color: white; font-size: 32px; font-weight: bold; padding: 20px; text-align: center; border-radius: 5px; letter-spacing: 5px;">
                            {code}
                        </div>
                        <p style="margin-top: 20px; font-size: 14px; color: #777;">
                            此驗證碼將在 <strong>10 分鐘</strong> 後失效。<br>
                            如果這不是您的操作，請忽略此郵件。
                        </p>
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="font-size: 12px; color: #999; text-align: center;">
                            © 2025 普元健康 IoT 系統
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # 連接 Gmail SMTP 伺服器
            logger.debug(f"正在連接 Gmail SMTP...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # 啟用 TLS 加密
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            
            # 發送郵件
            server.send_message(msg)
            server.quit()
            
            logger.info(f"驗證碼已發送到: {to_email}, Code: {code}")
            return True
            
        except Exception as e:
            logger.error(f"發送失敗: {str(e)}", exc_info=True)
            return False
  

    @staticmethod
    def send_temp_password(to_email: str, temp_password: str) -> bool:
        """
        發送臨時密碼郵件
        
        Args:
            to_email: 收件人 email
            temp_password: 六位數臨時密碼
            
        Returns:
            True = 發送成功, False = 發送失敗
        """
        try:
            # 檢查是否啟用郵件發送
            if not SEND_EMAIL:
                logger.info(f"郵件發送已停用 (SEND_EMAIL=false)")
                return False
            
            logger.info(f"準備發送臨時密碼到: {to_email}")
            
            # 建立郵件內容
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = to_email
            msg['Subject'] = "【普元健康】臨時密碼通知"
            
            # HTML 郵件內容
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
                        <h2 style="color: #333;">普元健康 - 臨時密碼</h2>
                        <p style="font-size: 16px; color: #555;">您的臨時密碼是：</p>
                        <div style="background-color: #dc3545; color: white; font-size: 32px; font-weight: bold; padding: 20px; text-align: center; border-radius: 5px; letter-spacing: 5px;">
                            {temp_password}
                        </div>
                        <p style="margin-top: 20px; font-size: 14px; color: #777;">
                            請使用此臨時密碼登入，登入後請立即重設您的密碼。<br>
                            如果這不是您的操作，請立即聯繫客服。
                        </p>
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                        <p style="font-size: 12px; color: #999; text-align: center;">
                            © 2025 普元健康 IoT 系統
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # 連接 Gmail SMTP 伺服器
            logger.debug(f"正在連接 Gmail SMTP...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            
            # 發送郵件
            server.send_message(msg)
            server.quit()
            
            logger.info(f"臨時密碼已發送到: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"發送失敗: {str(e)}", exc_info=True)
            return False
