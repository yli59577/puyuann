# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('Puyuan.db')
cursor = conn.cursor()

user_id = 1
query_date = '2025-10-28'

print(f'測試查詢 {query_date} 的飲食記錄')
print("=" * 50)

# 先查詢所有記錄
cursor.execute("SELECT id, user_id, recorded_at, created_at FROM DiaryDiet WHERE user_id = ?", (user_id,))
all_records = cursor.fetchall()
print(f'用戶 {user_id} 的所有飲食記錄:')
for record in all_records:
    record_id = str(record[0]) if record[0] else 'None'
    record_id_display = record_id[:20] if len(record_id) > 20 else record_id
    print(f'  ID: {record_id_display}, recorded_at: {record[2]}, created_at: {record[3]}')

print("\n" + "=" * 50)
print("Python 過濾邏輯測試:")

filtered = []
for record in all_records:
    recorded_at_str = record[2]
    created_at_str = record[3]
    
    match = False
    record_id = str(record[0]) if record[0] else 'None'
    record_id_display = record_id[:20] if len(record_id) > 20 else record_id
    print(f'\n檢查記錄: {record_id_display}')
    print(f'  recorded_at: {recorded_at_str}')
    print(f'  created_at: {created_at_str}')
    
    # 檢查 recorded_at
    if recorded_at_str and recorded_at_str != 'string':
        if recorded_at_str.startswith(query_date):
            print(f'  ✓ recorded_at 符合 (startswith)')
            match = True
    
    # 檢查 created_at (如果 recorded_at 是 'string')
    if not match and recorded_at_str == 'string' and created_at_str:
        if created_at_str.startswith(query_date):
            print(f'  ✓ created_at 符合 (recorded_at 是 string)')
            match = True
    
    if match:
        filtered.append(record)
        print(f'  → 加入結果')
    else:
        print(f'  → 不符合')

print("\n" + "=" * 50)
print(f'過濾結果: {len(filtered)} 筆符合 {query_date}')

conn.close()
