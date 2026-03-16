from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def get_qdrant_client() -> QdrantClient:
    client = QdrantClient(
        url=f"https://{settings.qdrant_host}",
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )
    logger.info("Qdrant cloud client initialized")
    return client

def ensure_collections(client: QdrantClient):
    existing = [c.name for c in client.get_collections().collections]
    
    for collection_name in [
        settings.qdrant_collection_resumes,
        settings.qdrant_collection_jobs
    ]:
        if collection_name not in existing:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimensions
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
        else:
            logger.info(f"Collection already exists: {collection_name}")