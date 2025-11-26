from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.database import engine, Base

# 導入所有 API 路由
from app._user.api import router as user_router
from app.account.api import router as account_router
from app._else.api import router as else_router
from app._journal.api import router as journal_router
from app.measurement.api import router as measurement_router
from app.a1c.api import router as a1c_router
from app.medicine.api import router as medicine_router
from app.care.api import router as care_router
from app.friend.api import router as friend_router

# 建立所有資料表
Base.metadata.create_all(bind=engine)

# 創建 FastAPI 應用程式
app = FastAPI(
    title='普元後端 API',
    description='普元 IoT 專案後端 API 服務',
    version='1.0.0',
)

# 全域異常處理：確保所有錯誤都回傳 status 欄位，防止 App 崩潰
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"捕捉到驗證錯誤: {exc}")
    # 處理 Pydantic 驗證錯誤 (例如缺少欄位、類型錯誤)
    return JSONResponse(
        status_code=200, # 使用 200 讓 App 能夠解析 JSON
        content={"status": "1", "message": f"資料驗證錯誤: {exc.errors()}"},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(f"捕捉到 HTTP 錯誤: {exc.detail}")
    # 處理 HTTP 錯誤 (例如 404, 401)
    return JSONResponse(
        status_code=200,
        content={"status": "1", "message": str(exc.detail)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"捕捉到未預期錯誤: {exc}")
    # 處理其他未預期的伺服器錯誤
    return JSONResponse(
        status_code=200,
        content={"status": "1", "message": f"伺服器內部錯誤: {str(exc)}"},
    )

# 設定 CORS (允許前端連接)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # 允許所有來源，在生產環境中應更嚴格
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 包含路由
app.include_router(account_router, prefix='/api', tags=['用戶身份'])
app.include_router(account_router, prefix='/api/account', include_in_schema=False) # 為了兼容舊版 APP
app.include_router(user_router, prefix='/api/user', tags=['個人資訊'])
app.include_router(measurement_router, prefix='/api/user', tags=['測量上傳'])
app.include_router(journal_router, prefix='/api/user', tags=['日記'])
app.include_router(a1c_router, prefix='/api/user', tags=['糖化血色素'])
app.include_router(medicine_router, prefix='/api/user', tags=['就醫、藥物資訊'])
app.include_router(care_router, prefix='/api/user', tags=['關懷諮詢'])
app.include_router(friend_router, prefix='/api/friend', tags=['糖友圈'])
app.include_router(else_router, prefix='/api', tags=['其他'])


@app.get('/')
async def root():
    return {'message': '普元後端 API 服務正在運行', 'version': '1.0.0'}
