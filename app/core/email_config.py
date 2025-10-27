# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP 設定
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "yli59577@gmail.com"  
SMTP_PASSWORD = "vxby hzle nhmb frhj"  


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
            print(f"[郵件] 正在連接 Gmail SMTP...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # 啟用 TLS 加密
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            
            # 發送郵件
            server.send_message(msg)
            server.quit()
            
            print(f"✅ [郵件] 驗證碼已發送到: {to_email}, Code: {code}")
            return True
            
        except Exception as e:
            print(f"❌ [郵件] 發送失敗: {str(e)}")
            return False
  