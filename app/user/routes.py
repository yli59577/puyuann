from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("")
async def get_user_info(user_id: int, db: Session = Depends(get_db)):
    """查看個人資訊"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "1", "message": "失敗"}

        return {
            "status": "0",
            "user": user.to_dict(),
            "message": "ok"
        }
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("")
async def update_user_info(request: dict, db: Session = Depends(get_db)):
    """更新個人資料"""
    try:
        user = db.query(User).filter(User.id == request.get("id")).first()
        if not user:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("/default")
async def update_user_defaults(request: dict, db: Session = Depends(get_db)):
    """更新個人預設值"""
    try:
        user_defaults = db.query(UserDefaults).filter(UserDefaults.user_id == request.get("user_id")).first()
        if not user_defaults:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user_defaults, key):
                setattr(user_defaults, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}

@router.patch("/setting")
async def update_user_settings(request: dict, db: Session = Depends(get_db)):
    """更新個人設定"""
    try:
        user_settings = db.query(UserSettings).filter(UserSettings.user_id == request.get("user_id")).first()
        if not user_settings:
            return {"status": "1", "message": "失敗"}

        for key, value in request.items():
            if hasattr(user_settings, key):
                setattr(user_settings, key, value)
        db.commit()

        return {"status": "0", "message": "成功"}
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return {"status": "1", "message": "失敗"}