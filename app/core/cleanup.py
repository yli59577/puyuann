# -*- coding: utf-8 -*-
"""
清理過期未驗證帳號的任務
"""
from sqlalchemy.orm import Session
from app.account.models import User
from app._user.models import UserProfile
from datetime import datetime, timezone, timedelta
import threading
import time
from common.utils import get_logger

logger = get_logger(__name__)
TAIWAN_TZ = timezone(timedelta(hours=8))


class CleanupService:
    """清理服務"""
    
    @staticmethod
    def cleanup_expired_unverified_users(db: Session) -> int:
        """
        清理過期未驗證的帳號
        
        Returns:
            刪除的帳號數量
        """
        try:
            now = datetime.now(TAIWAN_TZ).replace(tzinfo=None)
            
            # 查詢所有過期未驗證的帳號
            expired_users = db.query(User).filter(
                User.verified == False,
                User.verification_expires_at != None,
                User.verification_expires_at <= now
            ).all()
            
            deleted_count = 0
            for user in expired_users:
                try:
                    logger.info(f"刪除過期未驗證帳號: {user.email} (過期時間: {user.verification_expires_at})")
                    
                    # 刪除相關的 user_profile
                    db.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
                    
                    # 刪除用戶
                    db.delete(user)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"刪除帳號 {user.email} 時出錯: {str(e)}", exc_info=True)
            
            db.commit()
            
            if deleted_count > 0:
                logger.info(f"成功刪除 {deleted_count} 個過期未驗證帳號")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理過期帳號時出錯: {str(e)}", exc_info=True)
            db.rollback()
            return 0


def start_cleanup_scheduler(db_session_factory):
    """
    啟動定期清理任務（每分鐘檢查一次）
    
    Args:
        db_session_factory: SQLAlchemy session factory
    """
    def cleanup_loop():
        while True:
            try:
                db = db_session_factory()
                CleanupService.cleanup_expired_unverified_users(db)
                db.close()
            except Exception as e:
                logger.error(f"清理任務出錯: {str(e)}", exc_info=True)
            
            # 每分鐘檢查一次
            time.sleep(60)
    
    # 以後台線程啟動清理任務
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("已啟動過期帳號清理任務（每分鐘檢查一次）")
