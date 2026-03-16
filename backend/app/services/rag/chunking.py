"""
Document Chunking Service
Load and chunk knowledge base documents for vector storage
"""
import json
from typing import List, Dict, Any
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores.utils import filter_complex_metadata


def get_logger(name: str):
    """Get logger - lazy import to avoid circular dependency"""
    from app.core.logging import get_logger as _get_logger
    return _get_logger(name)


def get_settings():
    """Get settings - lazy import to avoid circular dependency"""
    from app.config import settings
    return settings


logger = get_logger(__name__)


def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean metadata to only include simple types (str, int, float, bool)
    ChromaDB doesn't support lists, dicts, or complex types
    
    Args:
        metadata: Original metadata dictionary
        
    Returns:
        Cleaned metadata with only simple types
    """
    cleaned = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, list):
            # Convert list to comma-separated string
            cleaned[key] = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            # Skip nested dicts or convert to JSON string
            continue
        elif value is None:
            # Skip None values
            continue
        else:
            # Convert other types to string
            cleaned[key] = str(value)
    
    return cleaned


class DocumentChunker:
    """Chunks documents from knowledge base"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize document chunker
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(
            f"Initialized DocumentChunker: chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )
    
    def load_json_file(self, filepath: Path) -> dict:
        """Load JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return {}
    
    def chunk_faqs(self) -> List[Document]:
        """
        Chunk FAQ documents
        Each FAQ is a single chunk with metadata
        
        Returns:
            List of Document objects
        """
        filepath = Path("data/knowledge_base/faqs.json")
        data = self.load_json_file(filepath)
        
        documents = []
        for faq in data.get("faqs", []):
            # Combine question and answer
            content = f"Question: {faq['question']}\n\nAnswer: {faq['answer']}"
            
            # Clean metadata - only simple types
            metadata = {
                "source": "faq",
                "category": faq.get("category", "general"),
                "faq_id": faq.get("id"),
                "priority": faq.get("metadata", {}).get("priority", "medium"),
            }
            
            # Convert tags list to string if present
            if "metadata" in faq and "tags" in faq["metadata"]:
                metadata["tags"] = ", ".join(faq["metadata"]["tags"])
            
            # Clean metadata
            metadata = clean_metadata(metadata)
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
        
        logger.info(f"Loaded {len(documents)} FAQ documents")
        return documents
    
    def chunk_policies(self) -> List[Document]:
        """
        Chunk policy documents
        Uses semantic chunking for long policies
        
        Returns:
            List of Document objects
        """
        filepath = Path("data/knowledge_base/policies.json")
        data = self.load_json_file(filepath)
        
        documents = []
        
        # Process each policy section
        for policy_name, policy_data in data.items():
            if isinstance(policy_data, dict):
                # Handle nested policy structure
                for section_name, section_content in policy_data.items():
                    if isinstance(section_content, str):
                        # Simple string content
                        content = f"{policy_name} - {section_name}:\n\n{section_content}"
                        
                        metadata = clean_metadata({
                            "source": "policy",
                            "policy": policy_name,
                            "section": section_name,
                            "category": "policy"
                        })
                        
                        # Chunk if too long
                        if len(content) > self.chunk_size:
                            chunks = self.text_splitter.split_text(content)
                            for i, chunk in enumerate(chunks):
                                chunk_metadata = metadata.copy()
                                chunk_metadata["chunk_index"] = i
                                doc = Document(
                                    page_content=chunk,
                                    metadata=chunk_metadata
                                )
                                documents.append(doc)
                        else:
                            doc = Document(
                                page_content=content,
                                metadata=metadata
                            )
                            documents.append(doc)
                    
                    elif isinstance(section_content, dict):
                        # Nested dict (e.g., shipping methods, category-specific rules)
                        for subsection_name, subsection_content in section_content.items():
                            if isinstance(subsection_content, str):
                                content = (
                                    f"{policy_name} - {section_name} - {subsection_name}:\n\n"
                                    f"{subsection_content}"
                                )
                            elif isinstance(subsection_content, dict):
                                # Convert dict to readable text
                                content_parts = [
                                    f"{policy_name} - {section_name} - {subsection_name}:\n"
                                ]
                                for key, value in subsection_content.items():
                                    if isinstance(value, list):
                                        value = ", ".join(str(v) for v in value)
                                    content_parts.append(f"{key}: {value}")
                                content = "\n".join(content_parts)
                            else:
                                continue
                            
                            metadata = clean_metadata({
                                "source": "policy",
                                "policy": policy_name,
                                "section": section_name,
                                "subsection": subsection_name,
                                "category": "policy"
                            })
                            
                            doc = Document(
                                page_content=content,
                                metadata=metadata
                            )
                            documents.append(doc)
                    
                    elif isinstance(section_content, list):
                        # List content
                        content = (
                            f"{policy_name} - {section_name}:\n\n"
                            + "\n".join(f"- {item}" for item in section_content)
                        )
                        
                        metadata = clean_metadata({
                            "source": "policy",
                            "policy": policy_name,
                            "section": section_name,
                            "category": "policy"
                        })
                        
                        doc = Document(
                            page_content=content,
                            metadata=metadata
                        )
                        documents.append(doc)
        
        logger.info(f"Loaded {len(documents)} policy documents")
        return documents
    
    def chunk_sops(self) -> List[Document]:
        """
        Chunk SOP documents
        Procedure-based chunking
        
        Returns:
            List of Document objects
        """
        filepath = Path("data/knowledge_base/sops.json")
        data = self.load_json_file(filepath)
        
        documents = []
        
        # Process SOP sections
        for sop_category, sop_data in data.items():
            if isinstance(sop_data, dict):
                for procedure_name, procedure_data in sop_data.items():
                    if isinstance(procedure_data, dict):
                        # Handle structured procedures (with steps)
                        content_parts = [f"{sop_category} - {procedure_name}:\n"]
                        
                        for key, value in procedure_data.items():
                            if isinstance(value, dict):
                                # Step-by-step procedure
                                content_parts.append(f"\n{key}:")
                                if "action" in value:
                                    content_parts.append(f"Action: {value['action']}")
                                if "details" in value:
                                    content_parts.append(f"Details: {value['details']}")
                            elif isinstance(value, list):
                                content_parts.append(f"\n{key}:")
                                for item in value:
                                    content_parts.append(f"- {item}")
                            elif isinstance(value, str):
                                content_parts.append(f"\n{key}: {value}")
                        
                        content = "\n".join(content_parts)
                        
                        metadata = clean_metadata({
                            "source": "sop",
                            "category": sop_category,
                            "procedure": procedure_name,
                            "type": "procedure"
                        })
                        
                        # Chunk if too long
                        if len(content) > self.chunk_size:
                            chunks = self.text_splitter.split_text(content)
                            for i, chunk in enumerate(chunks):
                                chunk_metadata = metadata.copy()
                                chunk_metadata["chunk_index"] = i
                                doc = Document(
                                    page_content=chunk,
                                    metadata=chunk_metadata
                                )
                                documents.append(doc)
                        else:
                            doc = Document(
                                page_content=content,
                                metadata=metadata
                            )
                            documents.append(doc)
                    
                    elif isinstance(procedure_data, str):
                        # Simple string procedure
                        content = f"{sop_category} - {procedure_name}:\n\n{procedure_data}"
                        
                        metadata = clean_metadata({
                            "source": "sop",
                            "category": sop_category,
                            "procedure": procedure_name,
                            "type": "procedure"
                        })
                        
                        doc = Document(
                            page_content=content,
                            metadata=metadata
                        )
                        documents.append(doc)
        
        logger.info(f"Loaded {len(documents)} SOP documents")
        return documents
    
    def chunk_products(self) -> List[Document]:
        """
        Chunk product catalog
        Each product is a single document
        
        Returns:
            List of Document objects
        """
        filepath = Path("data/knowledge_base/product_catalog.json")
        data = self.load_json_file(filepath)
        
        documents = []
        for product in data.get("products", []):
            # Create searchable content
            content = (
                f"Product: {product['name']}\n"
                f"Category: {product['category']}\n"
                f"Price: ${product['price']}\n"
                f"Description: {product['description']}\n"
            )
            
            if product.get("subcategory"):
                content += f"Subcategory: {product['subcategory']}\n"
            
            if product.get("in_stock"):
                content += f"Stock: In stock ({product.get('stock_quantity', 0)} available)\n"
            else:
                content += "Stock: Out of stock\n"
            
            if product.get("rating"):
                content += f"Rating: {product['rating']}/5 ({product.get('reviews_count', 0)} reviews)\n"
            
            metadata = clean_metadata({
                "source": "product",
                "product_id": product["product_id"],
                "category": product["category"],
                "subcategory": product.get("subcategory", ""),
                "price": float(product["price"]),
                "in_stock": bool(product.get("in_stock", False)),
                "type": "product"
            })
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
        
        logger.info(f"Loaded {len(documents)} product documents")
        return documents
    
    def load_all_documents(self) -> List[Document]:
        """
        Load and chunk all knowledge base documents
        
        Returns:
            List of all Document objects with cleaned metadata
        """
        logger.info("Loading all knowledge base documents...")
        
        all_documents = []
        
        # Load each document type
        all_documents.extend(self.chunk_faqs())
        all_documents.extend(self.chunk_policies())
        all_documents.extend(self.chunk_sops())
        all_documents.extend(self.chunk_products())
        
        # Apply LangChain's metadata filter as extra safety
        all_documents = filter_complex_metadata(all_documents)
        
        logger.info(f"Total documents loaded: {len(all_documents)}")
        
        # Log distribution
        sources = {}
        for doc in all_documents:
            source = doc.metadata.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        logger.info(f"Document distribution: {sources}")
        
        return all_documents


# Global instance
_chunker = None


def get_document_chunker() -> DocumentChunker:
    """Get or create document chunker instance"""
    global _chunker
    if _chunker is None:
        _chunker = DocumentChunker()
    return _chunker


# Export
__all__ = ['DocumentChunker', 'get_document_chunker', 'clean_metadata']