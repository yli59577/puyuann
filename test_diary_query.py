# -*- coding: utf-8 -*-
"""
完整測試 get_diary_list 函數
"""
import sqlite3
from datetime import datetime

def test_get_diary_list():
    user_id = 1
    date = "2025-10-27"
    
    print(f'測試參數: user_id={user_id}, date={date}')
    print("=" * 50)
    
    # 解析日期
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    query_date = str(target_date)
    print(f'解析後的日期: target_date={target_date}, query_date={query_date}')
    
    # 連接資料庫
    conn = sqlite3.connect('Puyuan.db')
    cursor = conn.cursor()
    
    # 測試血壓查詢
    print("\n" + "=" * 50)
    print("測試血壓記錄查詢:")
    cursor.execute("""
        SELECT id, user_id, systolic, diastolic, pulse, measured_at
        FROM blood_pressure_records
        WHERE user_id = ? AND DATE(measured_at) = ?
    """, (user_id, query_date))
    blood_pressure_records = cursor.fetchall()
    print(f'  找到 {len(blood_pressure_records)} 筆記錄')
    for record in blood_pressure_records:
        print(f'  - ID: {record[0]}, 收縮壓: {record[2]}, 舒張壓: {record[3]}, 時間: {record[5]}')
    
    # 測試體重查詢
    print("\n" + "=" * 50)
    print("測試體重記錄查詢:")
    cursor.execute("""
        SELECT id, user_id, weight, bmi, body_fat, measured_at
        FROM weight_records
        WHERE user_id = ? AND DATE(measured_at) = ?
    """, (user_id, query_date))
    weight_records = cursor.fetchall()
    print(f'  找到 {len(weight_records)} 筆記錄')
    for record in weight_records:
        print(f'  - ID: {record[0]}, 體重: {record[2]}, BMI: {record[3]}, 時間: {record[5]}')
    
    # 測試血糖查詢
    print("\n" + "=" * 50)
    print("測試血糖記錄查詢:")
    cursor.execute("""
        SELECT id, user_id, glucose, meal_time, measured_at
        FROM blood_sugar_records
        WHERE user_id = ? AND DATE(measured_at) = ?
    """, (user_id, query_date))
    blood_sugar_records = cursor.fetchall()
    print(f'  找到 {len(blood_sugar_records)} 筆記錄')
    for record in blood_sugar_records:
        print(f'  - ID: {record[0]}, 血糖: {record[2]}, 時段: {record[3]}, 時間: {record[4]}')
    
    # 測試飲食查詢
    print("\n" + "=" * 50)
    print("測試飲食記錄查詢:")
    cursor.execute("""
        SELECT id, user_id, description, meal, tag, image, lat, lng, recorded_at
        FROM DiaryDiet
        WHERE user_id = ? AND DATE(recorded_at) = ?
    """, (user_id, query_date))
    diet_records = cursor.fetchall()
    print(f'  找到 {len(diet_records)} 筆記錄')
    for record in diet_records:
        print(f'  - ID: {record[0]}, 描述: {record[2]}, 餐點: {record[3]}, 時間: {record[8]}')
    
    conn.close()
    
    total = len(blood_pressure_records) + len(weight_records) + len(blood_sugar_records) + len(diet_records)
    print("\n" + "=" * 50)
    print(f'總計: {total} 筆記錄')
    print(f'  血壓: {len(blood_pressure_records)} 筆')
    print(f'  體重: {len(weight_records)} 筆')
    print(f'  血糖: {len(blood_sugar_records)} 筆')
    print(f'  飲食: {len(diet_records)} 筆')
    
    if total == 0:
        print("\n⚠️  警告: 沒有找到任何記錄!")
        print("請檢查:")
        print("1. user_id 是否正確")
        print("2. 日期格式是否正確")
        print("3. 資料庫中是否有該日期的資料")

if __name__ == '__main__':
    test_get_diary_list()
