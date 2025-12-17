#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify password reset functionality
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_profile@example.com"
OLD_PASSWORD = "password123"
NEW_PASSWORD = "newpassword456"

def test_password_reset():
    """Test the password reset endpoint"""
    
    print("=" * 60)
    print("Testing Password Reset")
    print("=" * 60)
    
    # Step 1: Login with old password to get token
    print("\n[Step 1] Logging in with old password...")
    login_data = {
        "email": TEST_EMAIL,
        "password": OLD_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/auth", json=login_data)
    print(f"Login Response: {response.status_code}")
    login_response = response.json()
    print(f"Response: {login_response}")
    
    if response.status_code != 200 or "token" not in login_response:
        print("Login failed!")
        return
    
    token = login_response["token"]
    print(f"Token: {token}")
    
    # Step 2: Reset password
    print("\n[Step 2] Resetting password...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    reset_data = {
        "password": NEW_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/password/reset", json=reset_data, headers=headers)
    print(f"Reset Response: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Password reset failed!")
        return
    
    # Step 3: Try to login with new password
    print("\n[Step 3] Logging in with new password...")
    login_data = {
        "email": TEST_EMAIL,
        "password": NEW_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/auth", json=login_data)
    print(f"Login Response: {response.status_code}")
    login_response = response.json()
    print(f"Response: {login_response}")
    
    if response.status_code == 200 and "token" in login_response:
        print("\n✅ Password reset successful! New password works.")
    else:
        print("\n❌ Password reset failed! New password doesn't work.")

if __name__ == "__main__":
    test_password_reset()
