import pytest
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="module")
def client():
    # Lazy import to prevent global execution during collection
    from app.main import app as fastapi_app
    from app.core.database import get_db, Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Use SQLite for tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Reset Rate Limiter Singletons to ensure they pick up the Mock Redis
    import app.rate_limiting.guest_limiter
    import app.rate_limiting.user_limiter
    import app.rate_limiting.admin_limiter
    import app.rate_limiting.limiter
    
    app.rate_limiting.guest_limiter._guest_limiter = None
    app.rate_limiting.user_limiter._user_limiter = None
    app.rate_limiting.admin_limiter._admin_limiter = None
    app.rate_limiting.admin_limiter._admin_limiter = None
    app.rate_limiting.limiter._rate_limiter = None
    
    # Reset JWT Key Manager
    import app.core.jwt_key_manager
    app.core.jwt_key_manager._jwt_key_manager = None

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as c:
        yield c
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="session", autouse=True)
def mock_redis_global():
    """Mock Redis globally for all tests."""
    with patch("app.core.redis_client.get_redis") as mock_get, \
         patch("app.rate_limiting.base.get_redis") as mock_base_get, \
         patch("app.core.jwt_key_manager.get_redis") as mock_jwt_get:
        
        mock_instance = MagicMock()
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_instance.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1, 1, 1] # Dummy results
        
        # Mock standard operations
        mock_instance.get.return_value = None
        mock_instance.incr.return_value = 1
        
        mock_get.return_value = mock_instance
        mock_base_get.return_value = mock_instance
        mock_jwt_get.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="session", autouse=True)
def mock_device_validation():
    """Mock Device Token Validation globally to avoid 428 errors."""
    with patch("app.rate_limiting.device_token_service.get_device_token_service") as mock_get:
        mock_service = MagicMock()
        # validate_token returns (is_valid, error_msg, payload)
        mock_service.validate_token.return_value = (True, None, {"valid": True})
        mock_get.return_value = mock_service
        yield mock_service

@pytest.fixture(scope="function")
def mock_openai():
    with patch("openai.resources.chat.Completions.create") as mock_create:
        yield mock_create

@pytest.fixture(scope="function")
def mock_chroma():
    with patch("chromadb.HttpClient") as mock_client:
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        yield mock_collection
