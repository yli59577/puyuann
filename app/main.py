from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import engine, Base, get_db
from app._user.api import router as user_router
from app.account.api import router as account_router
from app._else.api import router as else_router
from app._journal.api import router as journal_router
from app._user.models import UserProfile
from pydantic import BaseModel
import sys
import os

# 將 Measurement upload 資料夾加入路徑
measurement_path = os.path.join(os.path.dirname(__file__), 'Measurement upload')
sys.path.insert(0, measurement_path)

# 導入測量上傳 API
import api as measurement_api
measurement_router = measurement_api.router

# 移除並清除模組
sys.path.remove(measurement_path)
if 'api' in sys.modules:
    del sys.modules['api']
if 'models' in sys.modules:
    del sys.modules['models']
if 'module' in sys.modules:
    del sys.modules['module']

# 將 Glycated Hemoglobin 資料夾加入路徑
a1c_path = os.path.join(os.path.dirname(__file__), 'Glycated Hemoglobin')
sys.path.insert(0, a1c_path)

# 導入糖化血色素 API
import api as a1c_api
a1c_router = a1c_api.router

# 移除並清除模組
sys.path.remove(a1c_path)
if 'api' in sys.modules:
    del sys.modules['api']
if 'models' in sys.modules:
    del sys.modules['models']
if 'module' in sys.modules:
    del sys.modules['module']

# 將 memecine im 資料夾加入路徑
medicine_path = os.path.join(os.path.dirname(__file__), 'memecine im')
sys.path.insert(0, medicine_path)

# 導入就醫、藥物資訊 API
import api as medicine_api
medicine_router = medicine_api.router

# 移除並清除模組
sys.path.remove(medicine_path)
if 'api' in sys.modules:
    del sys.modules['api']
if 'models' in sys.modules:
    del sys.modules['models']
if 'module' in sys.modules:
    del sys.modules['module']

# 將 care  info 資料夾加入路徑
care_path = os.path.join(os.path.dirname(__file__), 'care  info')
sys.path.insert(0, care_path)

# 導入關懷諮詢 API
import api as care_api
care_router = care_api.router

# 移除並清除模組
sys.path.remove(care_path)
if 'api' in sys.modules:
    del sys.modules['api']
if 'models' in sys.modules:
    del sys.modules['models']
if 'module' in sys.modules:
    del sys.modules['module']

# 建立所有資料表
Base.metadata.create_all(bind=engine)

# 創建 FastAPI 應用程式
app = FastAPI(
    title='普元後端 API',
    description='普元 IoT 專案後端 API 服務',
    version='1.0.0',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
    }
)

# 添加安全方案 - 讓 Swagger UI 顯示 Authorize 按鈕
from fastapi.security import HTTPBearer
security = HTTPBearer(scheme_name='Bearer')

# 設定 CORS (允許前端連接)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 包含路由
app.include_router(account_router, prefix='/api/account')
app.include_router(user_router, prefix='/api/user')
app.include_router(measurement_router)
app.include_router(journal_router)
app.include_router(a1c_router)
app.include_router(medicine_router)
app.include_router(care_router)
app.include_router(else_router, prefix='/api')

@app.get('/')
async def root():
    return {'message': '普元後端 API 服務正在運行', 'version': '1.0.0'}
