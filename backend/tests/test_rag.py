import pytest
from unittest.mock import MagicMock, patch
from app.services.rag import RAGService  # Assuming this exists based on comprehensive tests

# -----------------------------------------------------------------------------
# Mocks
# -----------------------------------------------------------------------------

@pytest.fixture
def rag_service(mock_chroma, mock_openai):
    """Initialize RAG Service with mocked dependencies"""
    with patch("app.services.rag.settings") as mock_settings:
        mock_settings.CHROMA_SERVER_HOST = "localhost"
        mock_settings.CHROMA_SERVER_PORT = 8000
        return RAGService()

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_rag_initialization(rag_service):
    """Test that RAG service initializes Chroma client correctly"""
    assert rag_service.chroma_client is not None
    # We mocked get_or_create_collection in conftest
    assert rag_service.collection is not None

def test_add_analysis_to_memory(rag_service, mock_chroma):
    """Test storing an analysis in vector DB"""
    # Mock embedding function if used
    with patch("app.services.rag.embedding_functions.OpenAIEmbeddingFunction") as mock_emb:
        rag_service.add_analysis_to_memory(
            ticker="AAPL",
            analysis_text="Bullish trend on AAPL due to earnings",
            metadata={"sentiment": "bullish", "timestamp": "2024-01-01"}
        )
        
        # Verify collection.add was called
        mock_chroma.add.assert_called_once()
        call_args = mock_chroma.add.call_args[1]
        assert "documents" in call_args
        assert "metadatas" in call_args
        assert "ids" in call_args
        assert call_args["documents"][0] == "Bullish trend on AAPL due to earnings"

def test_retrieve_measurements(rag_service, mock_chroma):
    """Test retrieving similar analyses"""
    # Mock return from query
    mock_chroma.query.return_value = {
        "documents": [["Old AAPL analysis"]],
        "metadatas": [[{"sentiment": "bullish"}]]
    }
    
    results = rag_service.retrieve_context(query="AAPL trend", n_results=3)
    
    msg = "Should return list of documents"
    assert isinstance(results, list), msg
    assert results[0] == "Old AAPL analysis"
    mock_chroma.query.assert_called_with(
        query_texts=["AAPL trend"],
        n_results=3,
        include=['documents', 'metadatas', 'distances']
    )
