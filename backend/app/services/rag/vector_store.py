"""
Vector Store Manager
Handles vector storage and similarity search using Pinecone or Chroma
"""

import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any

# Disable telemetry and warnings
os.environ["PINECONE_TELEMETRY_DISABLED"] = "true"
warnings.filterwarnings("ignore", category=UserWarning)

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.config import settings
from app.core.logging import get_logger
from app.core.errors import VectorStoreException

logger = get_logger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval"""

    def __init__(self, use_local: Optional[bool] = None):
        self.use_local = use_local if use_local is not None else settings.USE_LOCAL_VECTORS

        # Initialize embeddings
        try:
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise VectorStoreException(f"Embeddings initialization failed: {e}")

        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        if self.use_local:
            self._initialize_chroma()
        else:
            self._initialize_pinecone()

    def _initialize_chroma(self):
        try:
            persist_directory = "data/embeddings"
            Path(persist_directory).mkdir(parents=True, exist_ok=True)

            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
                collection_name="ecommerce_kb"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            raise VectorStoreException(f"Chroma initialization failed: {e}")

    def _initialize_pinecone(self):
        try:
            import pinecone
            from langchain_community.vectorstores import Pinecone

            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )

            index_name = settings.PINECONE_INDEX_NAME
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=1536,
                    metric="cosine"
                )

            self.vector_store = Pinecone.from_existing_index(
                index_name=index_name,
                embedding=self.embeddings
            )
        except Exception:
            # Fallback to local Chroma silently
            self.use_local = True
            self._initialize_chroma()

    def add_documents(self, documents: List[Document], batch_size: int = 100) -> bool:
        if not documents:
            return False

        try:
            total = len(documents)
            for i in range(0, total, batch_size):
                batch = documents[i:i + batch_size]
                self.vector_store.add_documents(batch)

            if self.use_local and hasattr(self.vector_store, "persist"):
                self.vector_store.persist()

            return True
        except Exception as e:
            raise VectorStoreException(f"Failed to add documents: {e}")

    def similarity_search(self, query: str, k: Optional[int] = None, filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        k = k or settings.SIMILARITY_TOP_K
        try:
            if filter_dict:
                results = self.vector_store.similarity_search(query, k=k, filter=filter_dict)
            else:
                results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            raise VectorStoreException(f"Similarity search failed: {e}")

    def similarity_search_with_score(self, query: str, k: Optional[int] = None, filter_dict: Optional[Dict[str, Any]] = None, score_threshold: float = 0.7) -> List[tuple[Document, float]]:
        k = k or settings.SIMILARITY_TOP_K
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k, filter=filter_dict)
            return [(doc, score) for doc, score in results if score >= score_threshold]
        except Exception as e:
            raise VectorStoreException(f"Similarity search with score failed: {e}")

    def delete_collection(self):
        try:
            if self.use_local:
                if hasattr(self.vector_store, "delete_collection"):
                    self.vector_store.delete_collection()
            else:
                import pinecone
                pinecone.delete_index(settings.PINECONE_INDEX_NAME)
        except Exception as e:
            raise VectorStoreException(f"Failed to delete collection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "type": "chroma" if self.use_local else "pinecone",
            "embedding_model": settings.EMBEDDING_MODEL,
            "initialized": self.vector_store is not None
        }
        if self.use_local and hasattr(self.vector_store, "_collection"):
            try:
                stats["document_count"] = self.vector_store._collection.count()
            except:
                stats["document_count"] = "unknown"
        return stats

    def initialize_from_documents(self, documents: List[Document]) -> bool:
        try:
            try:
                self.delete_collection()
            except:
                pass
            self._initialize_vector_store()
            return self.add_documents(documents)
        except Exception as e:
            raise VectorStoreException(f"Initialization failed: {e}")

    def is_initialized(self) -> bool:
        """Check if vector store has documents"""
        try:
            test_results = self.vector_store.similarity_search("test", k=1)
            return len(test_results) > 0
        except:
            return False


# Global instance
_vector_store: Optional[VectorStoreManager] = None


def get_vector_store() -> VectorStoreManager:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreManager()
    return _vector_store


def initialize_vector_store_if_needed():
    vector_store = get_vector_store()
    if not vector_store.is_initialized():
        from app.services.rag.chunking import get_document_chunker
        chunker = get_document_chunker()
        documents = chunker.load_all_documents()
        vector_store.initialize_from_documents(documents)


__all__ = ['VectorStoreManager', 'get_vector_store', 'initialize_vector_store_if_needed']

