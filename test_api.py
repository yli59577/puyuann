# -*- coding: utf-8 -*-
"""
測試 API 的腳本
"""
import requests

# API endpoint
url = "http://localhost:8000/api/user/diary"

# 從資料庫取得的正確 token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzYxNjM2OTA5fQ.3Yfb6ArZPpErrlX9RnWNCFrBRXK4tiMkr_I0IrhiqbU"

# Headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("測試1: 查詢 2025-10-27 (資料庫中有資料)")
print("=" * 50)
params = {"date": "2025-10-27"}
response = requests.get(url, headers=headers, params=params)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

print("\n測試2: 查詢 2025-10-28 (資料庫中有資料)")
print("=" * 50)
params = {"date": "2025-10-28"}
response = requests.get(url, headers=headers, params=params)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error Response Text: {response.text}")
