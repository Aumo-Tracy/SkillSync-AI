"""
RAG Retrieval Service
Retrieves relevant context from vector store and assembles it for LLM
"""
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from app.config import settings
from app.core.logging import get_logger
from app.services.rag.vector_store import get_vector_store
from app.models.schemas import SourceDocument

logger = get_logger(__name__)


class RAGRetriever:
    """Retrieves and processes relevant context for queries"""
    
    def __init__(self, top_k: int = None):
        """
        Initialize RAG retriever
        
        Args:
            top_k: Number of documents to retrieve
        """
        self.vector_store = get_vector_store()
        self.top_k = top_k or settings.SIMILARITY_TOP_K
        
        logger.info(f"Initialized RAGRetriever with top_k={self.top_k}")
    
    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        min_score: float = 0.7
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            category: Filter by category
            source: Filter by source (faq, policy, sop, product)
            min_score: Minimum relevance score
            
        Returns:
            List of relevant Documents
        """
        # Build metadata filter
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if source:
            filter_dict["source"] = source
        
        logger.info(
            f"Retrieving documents for query: '{query[:50]}...'",
            extra={"filter": filter_dict, "min_score": min_score}
        )
        
        try:
            # Get documents with scores
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=self.top_k * 2,  # Get more, then filter
                filter_dict=filter_dict if filter_dict else None,
                score_threshold=min_score
            )
            
            # Sort by score (higher is better)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Take top k
            documents = [doc for doc, score in results[:self.top_k]]
            
            logger.info(f"Retrieved {len(documents)} documents")
            
            return documents
        
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def retrieve_with_metadata(
        self,
        query: str,
        category: Optional[str] = None,
        source: Optional[str] = None,
        min_score: float = 0.7
    ) -> List[tuple[Document, float]]:
        """
        Retrieve documents with scores and metadata
        
        Args:
            query: User query
            category: Filter by category
            source: Filter by source
            min_score: Minimum relevance score
            
        Returns:
            List of (Document, score) tuples
        """
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if source:
            filter_dict["source"] = source
        
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=self.top_k,
                filter_dict=filter_dict if filter_dict else None,
                score_threshold=min_score
            )
            
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to retrieve documents with metadata: {e}")
            return []
    
    def assemble_context(
        self,
        query: str,
        category: Optional[str] = None,
        source: Optional[str] = None
    ) -> tuple[str, List[SourceDocument]]:
        """
        Retrieve documents and assemble into context string
        
        Args:
            query: User query
            category: Filter by category
            source: Filter by source
            
        Returns:
            tuple: (context_string, source_documents)
        """
        # Retrieve documents with scores
        results = self.retrieve_with_metadata(
            query=query,
            category=category,
            source=source
        )
        
        if not results:
            logger.warning(f"No relevant documents found for query: '{query}'")
            return "", []
        
        # Build context string
        context_parts = ["Here is relevant information from our knowledge base:\n"]
        source_documents = []
        
        for i, (doc, score) in enumerate(results, 1):
            # Add document content
            context_parts.append(f"\n[Source {i}]")
            
            # Add metadata context
            metadata = doc.metadata
            if metadata.get("source") == "faq":
                context_parts.append(f"FAQ - {metadata.get('category', 'General')}")
            elif metadata.get("source") == "policy":
                policy = metadata.get("policy", "Policy")
                section = metadata.get("section", "")
                context_parts.append(f"Policy: {policy} - {section}")
            elif metadata.get("source") == "sop":
                procedure = metadata.get("procedure", "Procedure")
                context_parts.append(f"SOP: {procedure}")
            elif metadata.get("source") == "product":
                context_parts.append(f"Product Information")
            
            context_parts.append(f"{doc.page_content}\n")
            
            # Create source document for response
            source_doc = SourceDocument(
                document_name=self._get_document_name(metadata),
                chunk_text=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                relevance_score=float(score),
                metadata=metadata
            )
            source_documents.append(source_doc)
        
        context = "\n".join(context_parts)
        
        logger.info(
            f"Assembled context from {len(results)} sources",
            extra={"context_length": len(context)}
        )
        
        return context, source_documents
    
    def _get_document_name(self, metadata: Dict[str, Any]) -> str:
        """
        Generate a readable document name from metadata
        
        Args:
            metadata: Document metadata
            
        Returns:
            str: Document name
        """
        source = metadata.get("source", "Unknown")
        
        if source == "faq":
            category = metadata.get("category", "General")
            return f"FAQ - {category.title()}"
        
        elif source == "policy":
            policy = metadata.get("policy", "Policy")
            section = metadata.get("section", "")
            if section:
                return f"{policy.replace('_', ' ').title()} - {section.replace('_', ' ').title()}"
            return policy.replace('_', ' ').title()
        
        elif source == "sop":
            category = metadata.get("category", "")
            procedure = metadata.get("procedure", "Procedure")
            if category:
                return f"SOP: {category.replace('_', ' ').title()} - {procedure.replace('_', ' ').title()}"
            return f"SOP: {procedure.replace('_', ' ').title()}"
        
        elif source == "product":
            product_id = metadata.get("product_id", "Unknown")
            return f"Product Catalog - {product_id}"
        
        return f"{source.title()} Document"
    
    def get_category_suggestions(self, query: str) -> List[str]:
        """
        Suggest relevant categories based on query
        
        Args:
            query: User query
            
        Returns:
            List of category suggestions
        """
        # Simple keyword-based category detection
        query_lower = query.lower()
        
        categories = []
        
        # Shipping keywords
        if any(word in query_lower for word in ["ship", "deliver", "track", "freight", "carrier"]):
            categories.append("shipping")
        
        # Return keywords
        if any(word in query_lower for word in ["return", "refund", "exchange"]):
            categories.append("returns")
        
        # Payment keywords
        if any(word in query_lower for word in ["payment", "pay", "card", "billing", "charge"]):
            categories.append("payment")
        
        # Order keywords
        if any(word in query_lower for word in ["order", "purchase", "cancel", "modify"]):
            categories.append("orders")
        
        # Account keywords
        if any(word in query_lower for word in ["account", "password", "login", "sign"]):
            categories.append("account")
        
        # Discount keywords
        if any(word in query_lower for word in ["discount", "coupon", "promo", "code", "sale"]):
            categories.append("discounts")
        
        # Product keywords
        if any(word in query_lower for word in ["product", "item", "buy", "purchase", "price"]):
            categories.append("products")
        
        return categories
    
    def smart_retrieve(
        self,
        query: str,
        auto_categorize: bool = True
    ) -> tuple[str, List[SourceDocument]]:
        """
        Intelligently retrieve context with automatic categorization
        
        Args:
            query: User query
            auto_categorize: Whether to auto-detect categories
            
        Returns:
            tuple: (context_string, source_documents)
        """
        if auto_categorize:
            # Try category-specific search first
            categories = self.get_category_suggestions(query)
            
            if categories:
                logger.info(f"Auto-detected categories: {categories}")
                
                # Try each category
                for category in categories:
                    context, sources = self.assemble_context(
                        query=query,
                        category=category
                    )
                    
                    if sources:
                        return context, sources
        
        # Fallback to general search
        return self.assemble_context(query=query)


# Global instance
_retriever = None


def get_rag_retriever() -> RAGRetriever:
    """
    Get or create RAG retriever instance
    
    Returns:
        RAGRetriever: Retriever instance
    """
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever


# Export
__all__ = ['RAGRetriever', 'get_rag_retriever']