import sqlite3
import os
from datetime import datetime, timezone, timedelta

def format_taiwan_time(time_str):
    """格式化時間顯示"""
    try:
        # 解析時間字串
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # 轉換為台灣時間顯示
        taiwan_tz = timezone(timedelta(hours=8))
        taiwan_time = dt.astimezone(taiwan_tz)
        return taiwan_time.strftime('%Y-%m-%d %H:%M:%S (UTC+8)')
    except:
        return time_str

def check_database():
    db_path = "app.db"
    
    if not os.path.exists(db_path):
        print("❌ 資料庫檔案不存在，請先啟動 FastAPI 應用程式")
        return
    
    print("✅ 找到資料庫檔案")
    
    # 連接資料庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 資料庫內容檢查 (時間顯示為 UTC+8)")
    print("="*60)
    
    # 查看所有資料表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📋 資料表: {[table[0] for table in tables]}")
    
    # 查看用戶資料
    print(f"\n👥 用戶資料表 (users):")
    print("-" * 40)
    try:
        cursor.execute("SELECT id, email, is_active FROM users;")
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"ID: {user[0]} | Email: {user[1]} | 啟用: {user[2]}")
        else:
            print("📝 目前沒有用戶資料")
        print(f"總計: {len(users)} 個用戶")
    except Exception as e:
        print(f"❌ 讀取用戶資料失敗: {e}")
    
    # 查看驗證碼資料
    print(f"\n🔐 驗證碼資料表 (verification_codes):")
    print("-" * 50)
    try:
        cursor.execute("SELECT email, code, created_at, is_used FROM verification_codes ORDER BY created_at DESC;")
        codes = cursor.fetchall()
        if codes:
            for code in codes:
                formatted_time = format_taiwan_time(code[2]) if code[2] else "未知時間"
                print(f"Email: {code[0]}")
                print(f"驗證碼: {code[1]}")
                print(f"建立時間: {formatted_time}")
                print(f"已使用: {code[3]}")
                print("-" * 30)
        else:
            print("📝 目前沒有驗證碼資料")
        print(f"總計: {len(codes)} 個驗證碼")
    except Exception as e:
        print(f"❌ 讀取驗證碼失敗: {e}")
    
    conn.close()
    print("="*60)

if __name__ == "__main__":
    check_database()