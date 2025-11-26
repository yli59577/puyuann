"""
控糖團好友模組
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from .models import (
    FriendInfo, UserInfo, FriendRequest, 
    SendInviteRequest, FriendResult, RelationInfo
)
from app.core.security import verify_token


class FriendModule:
    """控糖團好友模組"""
    
    def __init__(self, db_path: str = "Puyuan.db"):
        """初始化模組"""
        self.db_path = db_path
    
    @staticmethod
    def parse_user_id_from_token(authorization: str) -> Optional[int]:
        """從 Authorization Header 解析用戶 ID"""
        try:
            if not authorization or not authorization.startswith('Bearer '):
                return None
            
            token = authorization.split(' ')[1]
            payload = verify_token(token)
            
            if not payload:
                return None
            
            user_id = int(payload.get('sub'))
            return user_id
            
        except Exception as e:
            print(f'[Friend] parse_user_id_from_token 錯誤: {str(e)}')
            return None
    
    def get_db_connection(self):
        """獲取資料庫連線"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_friend_list(self, user_id: int) -> List[FriendInfo]:
        """
        獲取好友列表
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            好友列表
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 查詢已接受的好友關係
            cursor.execute(
                """SELECT f.friend_id as id, u.name, fr.type as relation_type
                   FROM Friendship f
                   JOIN UserProfile u ON f.friend_id = u.id
                   JOIN friend_requests fr ON (fr.user_id = ? AND fr.relation_id = f.friend_id) 
                      OR (fr.relation_id = ? AND fr.user_id = f.friend_id)
                   WHERE f.user_id = ? AND f.status = 1 AND fr.status = 1
                   ORDER BY f.created_at DESC""",
                (user_id, user_id, user_id)
            )
            rows = cursor.fetchall()
            
            return [
                FriendInfo(
                    id=row['id'],
                    name=row['name'] or '',
                    relation_type=row['relation_type']
                )
                for row in rows
            ]
            
        finally:
            conn.close()
    
    def get_invite_code(self, user_id: int) -> Optional[str]:
        """
        獲取用戶的邀請碼
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            邀請碼
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT invitCode FROM UserProfile WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            return row['invitCode'] if row else None
            
        finally:
            conn.close()
    
    def get_friend_requests(self, user_id: int) -> List[FriendRequest]:
        """
        獲取好友邀請列表
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            好友邀請列表
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT fr.*, u.name, ua.account
                   FROM friend_requests fr
                   JOIN UserProfile u ON fr.user_id = u.id
                   JOIN UserAuth ua ON fr.user_id = ua.id
                   WHERE fr.relation_id = ? AND fr.status = 0
                   ORDER BY fr.created_at DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            return [
                FriendRequest(
                    id=row['id'],
                    user_id=row['user_id'],
                    relation_id=row['relation_id'],
                    type=row['type'],
                    read=row['read'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    user=UserInfo(
                        id=row['user_id'],
                        name=row['name'] or '',
                        account=row['account']
                    )
                )
                for row in rows
            ]
            
        finally:
            conn.close()
    
    def send_friend_invite(self, user_id: int, data: SendInviteRequest) -> bool:
        """
        送出好友邀請
        
        Args:
            user_id: 使用者 ID
            data: 邀請資料
            
        Returns:
            是否成功
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 根據邀請碼查找目標用戶
            cursor.execute(
                "SELECT id FROM UserProfile WHERE invitCode = ?",
                (data.invite_code,)
            )
            target_user = cursor.fetchone()
            
            if not target_user:
                return False
            
            target_user_id = target_user['id']
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 創建好友邀請
            cursor.execute(
                """INSERT INTO friend_requests 
                   (user_id, relation_id, type, read, status, created_at, updated_at)
                   VALUES (?, ?, ?, 0, 0, ?, ?)""",
                (user_id, target_user_id, data.type, now, now)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f'[Friend] send_friend_invite 錯誤: {str(e)}')
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def accept_friend_invite(self, user_id: int, invite_id: int) -> bool:
        """
        接受好友邀請
        
        Args:
            user_id: 使用者 ID
            invite_id: 邀請 ID
            
        Returns:
            是否成功
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 獲取邀請資訊
            cursor.execute(
                "SELECT user_id, relation_id FROM friend_requests WHERE id = ? AND relation_id = ?",
                (invite_id, user_id)
            )
            invite = cursor.fetchone()
            
            if not invite:
                return False
            
            # 更新邀請狀態為已接受
            cursor.execute(
                "UPDATE friend_requests SET status = 1, read = 1, updated_at = ? WHERE id = ?",
                (now, invite_id)
            )
            
            # 添加雙向好友關係
            cursor.execute(
                """INSERT INTO Friendship (user_id, friend_id, status, created_at, updated_at)
                   VALUES (?, ?, 1, ?, ?)""",
                (user_id, invite['user_id'], now, now)
            )
            
            cursor.execute(
                """INSERT INTO Friendship (user_id, friend_id, status, created_at, updated_at)
                   VALUES (?, ?, 1, ?, ?)""",
                (invite['user_id'], user_id, now, now)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f'[Friend] accept_friend_invite 錯誤: {str(e)}')
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def refuse_friend_invite(self, user_id: int, invite_id: int) -> bool:
        """
        拒絕好友邀請
        
        Args:
            user_id: 使用者 ID
            invite_id: 邀請 ID
            
        Returns:
            是否成功
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 更新邀請狀態為已拒絕
            cursor.execute(
                """UPDATE friend_requests 
                   SET status = 2, read = 1, updated_at = ? 
                   WHERE id = ? AND relation_id = ?""",
                (now, invite_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f'[Friend] refuse_friend_invite 錯誤: {str(e)}')
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def remove_friends(self, user_id: int, friend_ids: List[int]) -> bool:
        """
        刪除好友
        
        Args:
            user_id: 使用者 ID
            friend_ids: 要刪除的好友 ID 列表
            
        Returns:
            是否成功
        """
        if not friend_ids:
            return False
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join('?' * len(friend_ids))
            
            # 刪除雙向好友關係
            cursor.execute(
                f"DELETE FROM Friendship WHERE user_id = ? AND friend_id IN ({placeholders})",
                [user_id] + friend_ids
            )
            
            cursor.execute(
                f"DELETE FROM Friendship WHERE friend_id = ? AND user_id IN ({placeholders})",
                [user_id] + friend_ids
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f'[Friend] remove_friends 錯誤: {str(e)}')
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_friend_results(self, user_id: int) -> List[FriendResult]:
        """
        獲取好友結果列表(我送出的邀請的狀態)
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            好友結果列表
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT fr.*, u.name, ua.account
                   FROM friend_requests fr
                   JOIN UserProfile u ON fr.relation_id = u.id
                   JOIN UserAuth ua ON fr.relation_id = ua.id
                   WHERE fr.user_id = ? AND fr.status != 0
                   ORDER BY fr.updated_at DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            return [
                FriendResult(
                    id=row['id'],
                    user_id=row['user_id'],
                    relation_id=row['relation_id'],
                    type=row['type'],
                    status=row['status'],
                    read=row['read'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    relation=RelationInfo(
                        id=row['relation_id'],
                        name=row['name'] or '',
                        account=row['account']
                    )
                )
                for row in rows
            ]
            
        finally:
            conn.close()
