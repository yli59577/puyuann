from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app._user.api import router as user_router
from app.account.api import router as account_router
from app._else.api import router as else_router
from app._user.models import UserProfile  # 修正導入
from pydantic import BaseModel

# 建立所有資料表
Base.metadata.create_all(bind=engine)

# 創建 FastAPI 應用程式
app = FastAPI(
    title="普元後端 API",
    description="普元 IoT 專案後端 API 服務",
    version="1.0.0"
)

# 設定 CORS (允許前端連接)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # 在生產環境中請設定具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(account_router, prefix="/api/account")
app.include_router(user_router, prefix="/api/user")
app.include_router(else_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "普元後端 API 服務正在運行", "version": "1.0.0"}