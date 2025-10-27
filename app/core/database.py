from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 資料庫連接設定（使用 Puyuan.db）
SQLALCHEMY_DATABASE_URL = "sqlite:///./Puyuan.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite 需要這個參數
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 獲取資料庫會話的函數
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()