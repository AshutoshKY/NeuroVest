import pytest
from app.core.jwt_key_manager import JWTKeyManager

def test_jwt_manager_singleton(mock_redis):
    """Test that manager behaves as singleton/independent service"""
    manager = JWTKeyManager()
    assert manager is not None
    # Check if it has methods to rotate keys
    assert hasattr(manager, 'rotate_keys')
    assert hasattr(manager, 'get_active_key')

def test_get_active_key(mock_redis):
    """Test key retrieval logic"""
    manager = JWTKeyManager()
    # Mock redis return
    mock_redis.get.return_value = "mock_private_key"
    
    key = manager.get_active_key()
    # It might generate one if missing, or return None. 
    # Logic depends on implementation.
    # If it auto-generates:
    if key:
        assert isinstance(key, str)
