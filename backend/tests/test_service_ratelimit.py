import pytest
from unittest.mock import MagicMock, patch
from app.services.rate_limiter import RateLimiter
from app.core.config import settings

@pytest.fixture
def rate_limiter(mock_redis):
    # Mock Redis is already patched in conftest
    return RateLimiter()

@pytest.mark.asyncio
async def test_check_rate_limit_allowed(rate_limiter, mock_redis):
    """Test allowing request under limit"""
    # Setup Redis mock: current count = 5
    mock_redis.get.return_value = "5"
    
    # Arg: key, limit, window
    allowed = await rate_limiter.check_rate_limit("user:123", 10, 60)
    
    assert allowed is True
    mock_redis.incr.assert_called()

@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(rate_limiter, mock_redis):
    """Test blocking request over limit"""
    mock_redis.get.return_value = "11"
    
    allowed = await rate_limiter.check_rate_limit("user:123", 10, 60)
    
    assert allowed is False
