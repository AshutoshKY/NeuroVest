#!/usr/bin/env python3
"""
Quick test script for Phase 1 authentication endpoints
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("\n1️⃣ Testing Registration...")
    response = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "Test@12345",
            "full_name": "Test User"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        print(f"✅ Registration successful: {response.json()}")
        return True
    else:
        print(f"❌ Registration failed: {response.text}")
        return False

def test_login():
    """Test user login"""
    print("\n2️⃣ Testing Login...")
    response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "email": "admin@stockmarket.com",
            "password": "Admin@123"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        print(f"   Access Token: {data['access_token'][:50]}...")
        print(f"   Refresh Token: {data['refresh_token'][:50]}...")
        return data['access_token'], data['refresh_token']
    else:
        print(f"❌ Login failed: {response.text}")
        return None, None

def test_get_me(access_token):
    """Test get current user endpoint"""
    print("\n3️⃣ Testing /auth/me...")
    response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ User info: {json.dumps(response.json(), indent=2)}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
        return False

def test_refresh_token(refresh_token):
    """Test token refresh"""
    print("\n4️⃣ Testing Token Refresh...")
    response = requests.post(
        f"{API_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token refreshed successfully")
        print(f"   New Access Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Refresh failed: {response.text}")
        return None

def test_account_lockout():
    """Test account lockout after failed attempts"""
    print("\n5️⃣ Testing Account Lockout (5 failed attempts)...")
    for i in range(6):
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123!"
            }
        )
        print(f"   Attempt {i+1}: {response.status_code}")
        if response.status_code == 403:
            print(f"✅ Account locked after {i+1} attempts: {response.json()['detail']}")
            return True
    print("❌ Account lockout not working")
    return False

def test_admin_endpoints(access_token):
    """Test admin-only endpoints"""
    print("\n6️⃣ Testing Admin Endpoints...")
    response = requests.get(
        f"{API_URL}/auth/admin/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Admin endpoint works. Found {len(users)} users")
        return True
    else:
        print(f"❌ Admin endpoint failed: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Phase 1: Authentication System Tests")
    print("=" * 60)
    
    # Test 1: Registration (might fail if user exists)
    test_registration()
    
    # Test 2: Login
    access_token, refresh_token = test_login()
    
    if access_token:
        # Test 3: Get current user
        test_get_me(access_token)
        
        # Test 4: Refresh token
        new_token = test_refresh_token(refresh_token)
        
        # Test 5: Account lockout
        test_account_lockout()
        
        # Test 6: Admin endpoints (admin user only)
        test_admin_endpoints(access_token)
    
    print("\n=" * 60)
    print("✅ Phase 1 Authentication Tests Complete!")
    print("=" * 60)
