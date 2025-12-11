#!/usr/bin/env python3
"""Quick login test with proper timeout"""
import requests
import sys

try:
    print("Testing login endpoint...")
    response = requests.post(
        "http://localhost:8000/auth/login",
        json={"email": "admin@stockmarket.com", "password": "Admin@123"},
        timeout=5
    )
    print(f"✅ Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"   Access token (first 50 chars): {data['access_token'][:50]}...")
        print(f"   Token type: {data['token_type']}")
        sys.exit(0)
    else:
        print(f"❌ Failed: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
