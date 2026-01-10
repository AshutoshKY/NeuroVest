import pytest
from unittest.mock import MagicMock, patch
from app.services.rate_limiter import RateLimiter
from app.core.config import settings

@pytest.fixture
def rate_limiter():
    # Mock Redis is already patched in conftest
    return RateLimiter()

@pytest.mark.asyncio
async def test_check_rate_limit_allowed(rate_limiter, mock_redis_global):
    """Test allowing request under limit"""
    # Setup Redis mock: current count = 5
    mock_redis_global.get.return_value = b"5"
    
    # Mock Request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"
    
    # Arg: request, limit_type, max_requests, window_seconds
    allowed, count, retry = await rate_limiter.check_rate_limit(
        mock_request,
        limit_type="test",
        max_requests=10,
        window_seconds=60
    )
    
    assert allowed is True
    assert count == 6
    mock_redis_global.incr.assert_called()

@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(rate_limiter, mock_redis_global):
    """Test blocking request over limit"""
    mock_redis_global.get.return_value = b"11"
    
    # Mock Request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    allowed, count, retry = await rate_limiter.check_rate_limit(
        mock_request,
        limit_type="test",
        max_requests=10,
        window_seconds=60
    )
    
    assert allowed is False
