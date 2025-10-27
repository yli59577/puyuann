"""
普元後端 API - 帳號管理模組

專案套件清單:
─────────────────────────────────
Web 框架:
  - fastapi==0.104.1 - Python Web API 框架
  - uvicorn[standard]==0.24.0 - ASGI 伺服器,運行 FastAPI

資料庫:
  - sqlalchemy==2.0.23 - ORM 資料庫操作工具

資料驗證:
  - pydantic[email]==2.5.0 - 資料驗證和模型定義
  - python-multipart==0.0.6 - 處理表單和檔案上傳

安全性:
  - bcrypt==4.0.1 - 密碼加密 (已安裝但未使用)
  - PyJWT==2.8.0 - JWT Token 生成和驗證

工具:
  - python-dotenv==1.0.0 - 讀取環境變數檔案
─────────────────────────────────
共 8 個套件
"""

__version__ = "1.0.0"
__author__ = "普元 IoT 開發團隊"