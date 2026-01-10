import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

# Helper to generate unique email
from datetime import datetime
def get_unique_email():
    return f"test_{int(datetime.now().timestamp())}@example.com"

class TestAuthFlow:
    def test_public_key_access(self):
        """Test public key endpoint (Tracking/Encryption)"""
        response = client.get("/tracking/encryption/public-key")
        assert response.status_code == 200
        assert "public_key" in response.json()
        assert "BEGIN PUBLIC KEY" in response.json()["public_key"]

    def test_signup_and_login_flow(self):
        """Full flow: Register -> Login -> Me -> Refresh -> Logout"""
        email = get_unique_email()
        password = "Str0ng@Password123!"
        
        # 1. Register
        reg_payload = {
            "email": email,
            "password": password,
            "full_name": "Integration Test User"
        }
        response = client.post("/auth/register", json=reg_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert "id" in data

        # 2. Login
        login_payload = {
            "email": email,
            "password": password
        }
        login_res = client.post("/auth/login", json=login_payload)
        assert login_res.status_code == 200
        tokens = login_res.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. Get Me (Authenticated)
        headers = {"Authorization": f"Bearer {access_token}"}
        me_res = client.get("/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == email

        # 4. Refresh Token
        auth_cookies = {"refresh_token": refresh_token}
        refresh_res = client.post("/auth/refresh", cookies=auth_cookies)
        assert refresh_res.status_code == 200
        new_tokens = refresh_res.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != access_token

        # 5. Logout
        logout_res = client.post("/auth/logout", headers=headers, cookies=auth_cookies)
        assert logout_res.status_code == 200
        assert logout_res.json()["ok"] is True

class TestTrackingFlow:
    def test_guest_limit_check(self):
        """Test guest rate limit endpoint"""
        response = client.get("/tracking/user/check-limit")
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "guest"
        assert "remaining" in data
        assert "limit" in data

    def test_user_limit_check(self):
        """Test registered user rate limit"""
        # Create temporary user
        email = get_unique_email()
        client.post("/auth/register", json={"email": email, "password": "Pwd", "full_name": "Limit Tester"})
        login_res = client.post("/auth/login", json={"email": email, "password": "Pwd"})
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/tracking/user/check-limit", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        # User limit should be higher/different or at least valid
        assert data["limit"] > 0

class TestWatchlistFlow:
    def test_watchlist_operations(self):
        """Test Add/Remove/List Watchlist"""
        # 1. Create User
        email = get_unique_email()
        client.post("/auth/register", json={"email": email, "password": "Pwd", "full_name": "Watchlist Tester"})
        login = client.post("/auth/login", json={"email": email, "password": "Pwd"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Add Stock
        add_res = client.post("/user/watchlist/add", json={"ticker": "AAPL"}, headers=headers)
        assert add_res.status_code == 200
        assert add_res.json()["success"] is True
        
        # 3. Add Duplicate (Should Fail)
        dup_res = client.post("/user/watchlist/add", json={"ticker": "AAPL"}, headers=headers)
        assert dup_res.status_code == 400
        
        # 4. Get Watchlist
        get_res = client.get("/user/watchlist", headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["count"] == 1
        assert data["watchlist"][0]["ticker"] == "AAPL"
        
        # 5. Remove Stock
        del_res = client.delete("/user/watchlist/AAPL", headers=headers)
        assert del_res.status_code == 200
        
        # 6. Verify Empty
        final_res = client.get("/user/watchlist", headers=headers)
        assert final_res.json()["count"] == 0
