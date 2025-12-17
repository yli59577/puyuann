#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify user profile update functionality
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "password123"

def test_user_profile_update():
    """Test the user profile update endpoint"""
    
    print("=" * 60)
    print("Testing User Profile Update")
    print("=" * 60)
    
    # Step 1: Register a new user
    print("\n[Step 1] Registering a new user...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/register", json=register_data)
    print(f"Register Response: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("Registration failed!")
        return
    
    # Step 2: Login to get token
    print("\n[Step 2] Logging in to get token...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"Login Response: {response.status_code}")
    login_response = response.json()
    print(f"Response: {login_response}")
    
    if response.status_code != 200 or "token" not in login_response:
        print("Login failed!")
        return
    
    token = login_response["token"]
    print(f"Token: {token}")
    
    # Step 3: Update user profile
    print("\n[Step 3] Updating user profile...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "name": "Test User",
        "gender": 1,
        "birthday": "1990-01-01",
        "height": 170.5,
        "weight": 75.0,
        "phone": "0912345678",
        "address": "Taipei, Taiwan",
        "avatar": "https://example.com/avatar.jpg",
        "fcm_id": "fcm_token_123"
    }
    
    response = requests.patch(f"{BASE_URL}/api/user", json=update_data, headers=headers)
    print(f"Update Response: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Step 4: Get user profile to verify update
    print("\n[Step 4] Getting user profile to verify update...")
    response = requests.get(f"{BASE_URL}/api/user", headers=headers)
    print(f"Get Profile Response: {response.status_code}")
    profile_response = response.json()
    print(f"Response: {json.dumps(profile_response, indent=2, ensure_ascii=False)}")
    
    # Verify the data was saved
    if profile_response.get("status") == "0" and profile_response.get("user"):
        user = profile_response["user"]
        print("\n[Verification Results]")
        print(f"Name: {user.get('name')} (Expected: Test User)")
        print(f"Gender: {user.get('gender')} (Expected: 1)")
        print(f"Birthday: {user.get('birthday')} (Expected: 1990-01-01)")
        print(f"Height: {user.get('height')} (Expected: 170.5)")
        print(f"Weight: {user.get('weight')} (Expected: 75.0)")
        print(f"Phone: {user.get('phone')} (Expected: 0912345678)")
        print(f"Address: {user.get('address')} (Expected: Taipei, Taiwan)")
        print(f"Avatar: {user.get('avatar')} (Expected: https://example.com/avatar.jpg)")
        print(f"FCM ID: {user.get('fcm_id')} (Expected: fcm_token_123)")
        
        # Check if all values match
        all_match = (
            user.get('name') == 'Test User' and
            user.get('gender') == 1 and
            user.get('birthday') == '1990-01-01' and
            user.get('height') == 170.5 and
            user.get('weight') == 75.0 and
            user.get('phone') == '0912345678' and
            user.get('address') == 'Taipei, Taiwan' and
            user.get('avatar') == 'https://example.com/avatar.jpg' and
            user.get('fcm_id') == 'fcm_token_123'
        )
        
        if all_match:
            print("\n✅ All values match! Profile update is working correctly.")
        else:
            print("\n❌ Some values don't match. There may be an issue with the update.")
    else:
        print("\n❌ Failed to retrieve user profile.")

if __name__ == "__main__":
    test_user_profile_update()
