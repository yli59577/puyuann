# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('Puyuan.db')
cursor = conn.cursor()

print("=" * 50)
print("測試1: 查看所有血壓記錄")
cursor.execute('SELECT id, user_id, measured_at FROM blood_pressure_records WHERE user_id = 1')
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, User: {row[1]}, measured_at: {row[2]}")

print("\n" + "=" * 50)
print("測試2: 使用 DATE() 函數")
cursor.execute("SELECT id, measured_at, DATE(measured_at) as date_only FROM blood_pressure_records WHERE user_id = 1")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, measured_at: {row[1]}, date_only: {row[2]}")

print("\n" + "=" * 50)
print("測試3: 查詢特定日期 (使用 DATE())")
cursor.execute("SELECT id, measured_at FROM blood_pressure_records WHERE user_id = ? AND DATE(measured_at) = ?", (1, '2025-10-27'))
rows = cursor.fetchall()
print(f"找到 {len(rows)} 筆記錄 (使用 DATE()):")
for row in rows:
    print(f"  ID: {row[0]}, measured_at: {row[1]}")

print("\n" + "=" * 50)
print("測試4: 查詢特定日期 (使用 LIKE)")
cursor.execute("SELECT id, measured_at FROM blood_pressure_records WHERE user_id = ? AND measured_at LIKE ?", (1, '2025-10-27%'))
rows = cursor.fetchall()
print(f"找到 {len(rows)} 筆記錄 (使用 LIKE):")
for row in rows:
    print(f"  ID: {row[0]}, measured_at: {row[1]}")

print("\n" + "=" * 50)
print("測試5: 使用 strftime")
cursor.execute("SELECT id, measured_at, strftime('%Y-%m-%d', measured_at) as date_str FROM blood_pressure_records WHERE user_id = 1")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, measured_at: {row[1]}, date_str: {row[2]}")

print("\n" + "=" * 50)
print("測試6: 查詢特定日期 (使用 strftime)")
cursor.execute("SELECT id, measured_at FROM blood_pressure_records WHERE user_id = ? AND strftime('%Y-%m-%d', measured_at) = ?", (1, '2025-10-27'))
rows = cursor.fetchall()
print(f"找到 {len(rows)} 筆記錄 (使用 strftime):")
for row in rows:
    print(f"  ID: {row[0]}, measured_at: {row[1]}")

conn.close()
print("\n" + "=" * 50)
print("測試完成!")
