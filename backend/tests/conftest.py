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
    from app.main import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def mock_redis():
    with patch("app.core.redis_client.get_redis") as mock_get:
        mock_instance = MagicMock()
        mock_get.return_value = mock_instance
        yield mock_instance

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
