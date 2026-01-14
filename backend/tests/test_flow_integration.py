import pytest
from app.core.config import settings

# Helper to generate unique email
# ... (function def is fine, but client usage inside classes needs changing)

# Helper to generate unique email
import uuid
def get_unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"

class TestAuthFlow:
    def test_public_key_access(self, client):
        """Test public key endpoint (Tracking/Encryption)"""
        response = client.get("/tracking/encryption/public-key")
        assert response.status_code == 200
        assert "public_key" in response.json()
        assert "BEGIN PUBLIC KEY" in response.json()["public_key"]

    def test_signup_and_login_flow(self, client):
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
        import time; time.sleep(1.1) # Ensure IAT changes
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
    def test_guest_limit_check(self, client):
        """Test guest rate limit endpoint"""
        # Mock valid tracking headers to pass strict middleware
        headers = {
            "X-Device-Token": '{"device_fp": "mock_fp_123"}',
            "X-Session-ID": "mock_sess_123"
        }
        response = client.get("/tracking/user/check-limit", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "guest"
        assert "remaining" in data
        assert "limit" in data

    def test_user_limit_check(self, client):
        """Test registered user rate limit"""
        # Create temporary user
        email = get_unique_email()
        password = "Str0ng@Password123!"
        reg = client.post("/auth/register", json={"email": email, "password": password, "full_name": "Limit Tester"})
        assert reg.status_code == 201, f"Register failed: {reg.text}"
        
        login_res = client.post("/auth/login", json={"email": email, "password": password})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Device-Token": '{"device_fp": "mock_fp_user"}',
            "X-Session-ID": "mock_sess_user"
        }
        response = client.get("/tracking/user/check-limit", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        # User limit should be higher/different or at least valid
        assert data["limit"] > 0

class TestWatchlistFlow:
    def test_watchlist_operations(self, client):
        """Test Add/Remove/List Watchlist"""
        # 1. Create User
        email = get_unique_email()
        password = "Str0ng@Password123!"
        reg = client.post("/auth/register", json={"email": email, "password": password, "full_name": "Watchlist Tester"})
        assert reg.status_code == 201, f"Register failed: {reg.text}"

        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, f"Login failed: {login.text}"
        token = login.json()["access_token"]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Device-Token": '{"device_fp": "mock_fp_watchlist"}',
            "X-Session-ID": "mock_sess_watchlist"
        }
        
        # 2. Add Stock
        add_res = client.post("/api/watchlist", json={"ticker": "AAPL", "name": "Apple Inc"}, headers=headers)
        assert add_res.status_code == 200, f"Add failed: {add_res.text}"
        
        # 3. Add Duplicate (Should Fail)
        dup_res = client.post("/api/watchlist", json={"ticker": "AAPL", "name": "Apple Inc"}, headers=headers)
        assert dup_res.status_code == 400
        
        # 4. Get Watchlist
        get_res = client.get("/api/watchlist", headers=headers)
        assert get_res.status_code == 200
        data = get_res.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"
        
        # 5. Remove Stock
        del_res = client.delete("/api/watchlist/AAPL", headers=headers)
        assert del_res.status_code == 200
        
        # 6. Verify Empty
        final_res = client.get("/api/watchlist", headers=headers)
        assert len(final_res.json()) == 0
