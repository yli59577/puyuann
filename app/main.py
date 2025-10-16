from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base

from app.account.routes import router as account_router
from app.user.routes import router as user_router

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
    allow_origins=[ "http://localhost:8000"],  # 在生產環境中請設定具體的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(account_router)
app.include_router(user_router)

@app.get("/")
async def root():
    return {"message": "普元後端 API 服務正在運行", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    
    return {"status": "healthy"}