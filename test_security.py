#!/usr/bin/env python3
"""
Comprehensive Authentication & Security Test Suite
Tests all endpoints, authorization, rate limiting, and security
"""
import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} | {name}")
    if details:
        print(f"     {details}")

def test_1_register_new_user():
    """Test user registration"""
    print(f"\n{Colors.BLUE}=== TEST 1: User Registration ==={Colors.END}")
    
    # Test with strong password
    response = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        },
        timeout=5
    )
    
    if response.status_code == 201:
        print_test("Register with valid data", True, f"User ID: {response.json()['id']}")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print_test("User already exists", True, "Expected - user exists from previous test")
        return True
    else:
        print_test("Register with valid data", False, f"Status: {response.status_code}, Response: {response.text}")
        return False

def test_2_register_weak_password():
    """Test password strength validation"""
    print(f"\n{Colors.BLUE}=== TEST 2: Password Strength Validation ==={Colors.END}")
    
    response = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "Weak Password User"
        },
        timeout=5
    )
    
    passed = response.status_code == 400 and "password" in response.text.lower()
    print_test("Reject weak password", passed, response.json().get("detail", ""))
    return passed

def test_3_login_valid():
    """Test login with valid credentials"""
    print(f"\n{Colors.BLUE}=== TEST 3: Login (Valid Credentials) ==={Colors.END}")
    
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": "admin@stockmarket.com", "password": "Admin@123"},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test("Login successful", True, f"Access token length: {len(data['access_token'])}")
        print_test("Refresh token provided", "refresh_token" in data, f"Refresh token length: {len(data.get('refresh_token', ''))}")
        return data
    else:
        print_test("Login successful", False, f"Status: {response.status_code}")
        return None

def test_4_login_invalid():
    """Test login with invalid credentials"""
    print(f"\n{Colors.BLUE}=== TEST 4: Login (Invalid Credentials) ==={Colors.END}")
    
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": "admin@stockmarket.com", "password": "WrongPassword123!"},
        timeout=5
    )
    
    passed = response.status_code == 401
    print_test("Reject invalid password", passed, f"Status: {response.status_code}")
    return passed

def test_5_get_current_user(access_token):
    """Test /auth/me endpoint"""
    print(f"\n{Colors.BLUE}=== TEST 5: Get Current User Info ==={Colors.END}")
    
    response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5
    )
    
    if response.status_code == 200:
        user = response.json()
        print_test("Get user info", True, f"Email: {user['email']}, Role: {user['role']}")
        print_test("User role is admin", user['role'] == 'admin', f"Role: {user['role']}")
        return user
    else:
        print_test("Get user info", False, f"Status: {response.status_code}")
        return None

def test_6_access_without_token():
    """Test protected endpoint without token"""
    print(f"\n{Colors.BLUE}=== TEST 6: Access Protected Endpoint Without Token ==={Colors.END}")
    
    response = requests.get(f"{API_URL}/auth/me", timeout=5)
    passed = response.status_code == 403  # Forbidden - no auth header
    print_test("Reject request without token", passed, f"Status: {response.status_code}")
    return passed

def test_7_access_with_invalid_token():
    """Test protected endpoint with invalid token"""
    print(f"\n{Colors.BLUE}=== TEST 7: Access With Invalid Token ==={Colors.END}")
    
    response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"},
        timeout=5
    )
    
    passed = response.status_code == 401
    print_test("Reject invalid token", passed, f"Status: {response.status_code}")
    return passed

def test_8_admin_endpoint(access_token):
    """Test admin-only endpoint"""
    print(f"\n{Colors.BLUE}=== TEST 8: Admin Endpoint Access ==={Colors.END}")
    
    response = requests.get(
        f"{API_URL}/auth/admin/users",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=5
    )
    
    if response.status_code == 200:
        users = response.json()
        print_test("Admin can access admin endpoint", True, f"Found {len(users)} users")
        return users
    else:
        print_test("Admin can access admin endpoint", False, f"Status: {response.status_code}")
        return None

def test_9_refresh_token(refresh_token):
    """Test token refresh"""
    print(f"\n{Colors.BLUE}=== TEST 9: Refresh Access Token ==={Colors.END}")
    
    response = requests.post(
        f"{API_URL}/auth/refresh",
        json={"refresh_token": refresh_token},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print_test("Token refresh successful", True, f"New access token received")
        return data
    else:
        print_test("Token refresh successful", False, f"Status: {response.status_code}")
        return None

def test_10_rate_limiting():
    """Test rate limiting (100 req/hour = ~1.67 req/min)"""
    print(f"\n{Colors.BLUE}=== TEST 10: Rate Limiting ==={Colors.END}")
    
    print(f"     {Colors.YELLOW}Making 10 rapid requests to test rate limiting...{Colors.END}")
    success_count = 0
    rate_limited = False
    
    for i in range(10):
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited = True
            print_test(f"Rate limit triggered after {success_count} requests", True, "Status: 429 Too Many Requests")
            break
        time.sleep(0.1)
    
    if not rate_limited:
        print_test("Rate limiting active", success_count < 10, f"{success_count}/10 requests succeeded")
    
    return True

def test_11_account_lockout():
    """Test account lockout after failed attempts"""
    print(f"\n{Colors.BLUE}=== TEST 11: Account Lockout (5 Failed Attempts) ==={Colors.END}")
    
    test_email = "lockout@example.com"
    
    # Try to register test user first
    requests.post(
        f"{API_URL}/auth/register",
        json={"email": test_email, "password": "ValidPass123!", "full_name": "Lockout Test"},
        timeout=5
    )
    
    print(f"     {Colors.YELLOW}Testing 6 failed login attempts...{Colors.END}")
    for i in range(6):
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": test_email, "password": "WrongPassword123!"},
            timeout=5
        )
        
        if response.status_code == 403 and "locked" in response.text.lower():
            print_test(f"Account locked after {i+1} attempts", True, response.json().get("detail"))
            return True
        time.sleep(0.2)
    
    print_test("Account lockout working", False, "Account not locked after 6 attempts")
    return False

def test_12_sql_injection():
    """Test SQL injection protection"""
    print(f"\n{Colors.BLUE}=== TEST 12: SQL Injection Protection ==={Colors.END}")
    
    # Try SQL injection in email field
    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": "admin@stockmarket.com' OR '1'='1", "password": "anything"},
        timeout=5
    )
    
    passed = response.status_code == 401  # Should fail authentication, not execute SQL
    print_test("SQL injection blocked", passed, f"Status: {response.status_code}")
    return passed

def test_13_xss_protection():
    """Test XSS protection in input fields"""
    print(f"\n{Colors.BLUE}=== TEST 13: XSS Protection ==={Colors.END}")
    
    xss_payload = "<script>alert('XSS')</script>"
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"email": "xss@test.com", "password": "Valid123!", "full_name": xss_payload},
        timeout=5
    )
    
    # Should either reject or sanitize
    if response.status_code in [201, 400]:
        if response.status_code == 201:
            # Check if data was sanitized
            user = response.json()
            passed = "<script>" not in str(user)
            print_test("XSS payload sanitized", passed, f"Full name stored: {user.get('full_name', 'N/A')[:50]}")
        else:
            print_test("XSS payload rejected", True, "Input validation working")
        return True
    return False

if __name__ == "__main__":
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}🔒 COMPREHENSIVE AUTHENTICATION & SECURITY TESTING{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    tokens = None
    user_info = None
    
    try:
        # Run all tests
        test_1_register_new_user()
        test_2_register_weak_password()
        
        tokens = test_3_login_valid()
        if tokens:
            test_4_login_invalid()
            user_info = test_5_get_current_user(tokens['access_token'])
            test_6_access_without_token()
            test_7_access_with_invalid_token()
            test_8_admin_endpoint(tokens['access_token'])
            test_9_refresh_token(tokens['refresh_token'])
        
        test_10_rate_limiting()
        test_11_account_lockout()
        test_12_sql_injection()
        test_13_xss_protection()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✅ Security Testing Complete!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ Test suite crashed: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
