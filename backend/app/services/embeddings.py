import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings using sentence-transformers."""
    
    def __init__(self):
        """Initialize ChromaDB. Model loads lazily on first use."""
        # Use local embedding model (free, no API needed)
        self.model = None  # Lazy load on first use
        logger.info("Embedding service initialized (model will load on first use)")
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DB_PATH)
        )
        
        # Initialize collections
        self.news_collection = self.chroma_client.get_or_create_collection(
            name="stock_news",
            metadata={"description": "Stock market news articles"}
        )
        
        self.analysis_collection = self.chroma_client.get_or_create_collection(
            name="stock_analysis",
            metadata={"description": "Historical stock analyses"}
        )
     
    def _get_collection(self, collection_type: str):
        """Get the appropriate collection based on type."""
        if collection_type == "analysis":
            return self.analysis_collection
        return self.news_collection
    
    def _ensure_model_loaded(self):
        """Load model lazily on first use to avoid blocking startup."""
        if self.model is None:
            logger.info("🔄 Loading sentence-transformers model...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Loaded local embedding model: all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                raise
    
    def get_collection_count(self, collection_type: str = "news") -> int:
        """Get number of documents in the collection."""
        try:
            return self._get_collection(collection_type).count()
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            return 0
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using local model."""
        try:
            self._ensure_model_loaded()
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            self._ensure_model_loaded()
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        collection_type: str = "news"
    ):
        """Add documents to ChromaDB with embeddings."""
        try:
            logger.debug("🗄️  Adding documents to ChromaDB", extra={
                "operation": "chromadb_add",
                "collection": collection_type,
                "document_count": len(documents),
                "tickers": list(set([m.get('ticker', '') for m in metadatas if m.get('ticker')]))
            })
            
            # Generate embeddings
            embeddings = self.generate_embeddings(documents)
            
            logger.debug("🔢 Generated embeddings", extra={
                "operation": "generate_embeddings",
                "embedding_count": len(embeddings),
                "embedding_dim": len(embeddings[0]) if embeddings else 0
            })
            
            # Add to ChromaDB
            collection = self._get_collection(collection_type)
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # FORCE INDEXING TO COMPLETE: Verify documents are retrievable
            # This ensures ChromaDB has finished indexing before we return
            if ids:
                try:
                    # Attempt to retrieve the first document we just added
                    verify_result = collection.get(ids=[ids[0]], limit=1)
                    
                    # If retrieval fails, wait briefly and try once more
                    if not verify_result.get('documents'):
                        import time
                        time.sleep(0.05)  # 50ms wait
                        verify_result = collection.get(ids=[ids[0]], limit=1)
                    
                    if verify_result.get('documents'):
                        logger.debug(f"✅ Verified indexing complete for {len(ids)} documents")
                    else:
                        logger.warning(f"⚠️  Indexing verification returned empty, but proceeding")
                except Exception as verify_err:
                    logger.warning(f"⚠️  Indexing verification failed: {verify_err}, but documents were added")
            
            logger.info("✅ Documents added to ChromaDB", extra={
                "operation": "chromadb_add",
                "collection": collection_type,
                "document_count": len(documents),
                "status": "success"
            })
        except Exception as e:
            logger.error("❌ Error adding documents to ChromaDB", extra={
                "operation": "chromadb_add",
                "collection": collection_type,
                "status": "failure",
                "error": str(e)
            })
            raise
    
    def query_similar(
        self,
        query_text: str,
        n_results: int = 10,
        filter_metadata: Dict[str, Any] = None,
        collection_type: str = "news"
    ) -> Dict[str, Any]:
        """Query similar documents from ChromaDB."""
        try:
            logger.debug("🔍 Querying ChromaDB for similar documents", extra={
                "operation": "chromadb_query",
                "collection": collection_type,
                "query_length": len(query_text),
                "n_results": n_results,
                "filter": str(filter_metadata) if filter_metadata else "none"
            })
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)
            
            # Query ChromaDB
            results = self._get_collection(collection_type).query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            result_count = len(results["documents"][0]) if results["documents"] else 0
            
            logger.info("✅ ChromaDB query complete", extra={
                "operation": "chromadb_query",
                "collection": collection_type,
                "results_found": result_count,
                "requested": n_results,
                "status": "success"
            })
            
            # Log details of what was retrieved
            if result_count > 0 and filter_metadata and 'ticker' in str(filter_metadata):
                logger.debug("📊 Retrieved documents from ChromaDB", extra={
                    "operation": "chromadb_query",
                    "data_type": "current_news" if collection_type == "news" else "historical_analysis",
                    "document_count": result_count,
                    "ticker": filter_metadata.get('ticker', 'unknown')
                })
            
            return {
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0],
                "ids": results["ids"][0]
            }
        except Exception as e:
            logger.error("❌ Error querying ChromaDB", extra={
                "operation": "chromadb_query",
                "collection": collection_type,
                "status": "failure",
                "error": str(e)
            })
            raise

    def get_documents(
        self,
        where: Dict[str, Any],
        limit: int = 10,
        collection_type: str = "news"
    ) -> Dict[str, Any]:
        """Get documents matching specific metadata filters."""
        try:
            logger.debug("🗂️  Retrieving documents from ChromaDB", extra={
                "operation": "chromadb_get",
                "collection": collection_type,
                "filter": str(where),
                "limit": limit
            })
            
            results = self._get_collection(collection_type).get(
                where=where,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            result_count = len(results.get("ids", [])) if results else 0
            
            # Determine data type
            data_type = "unknown"
            if where and "$and" in str(where) and "historical_analysis" in str(where):
                data_type = "historical_analysis"
            elif collection_type == "news":
                data_type = "current_news"
            
            logger.info("✅ Retrieved documents from ChromaDB", extra={
                "operation": "chromadb_get",
                "collection": collection_type,
                "data_type": data_type,
                "documents_found": result_count,
                "requested_limit": limit,
                "status": "success"
            })
            
            if not result_count:
                logger.warning("⚠️  No historical analyses found in ChromaDB (expected for first-time analysis)", extra={
                    "operation": "chromadb_get",
                    "collection": collection_type,
                    "status": "empty_result_expected",
                    "context": "historical_analyses"
                })
            
            return results
        except Exception as e:
            logger.error("❌ Error retrieving documents from ChromaDB", extra={
                "operation": "chromadb_get",
                "collection": collection_type,
                "status": "failure",
                "error": str(e)
            })
            raise


# Global instance
embedding_service = EmbeddingService()
