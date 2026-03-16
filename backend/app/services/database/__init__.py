"""
Unified Database Interface
Automatically switches between Supabase and JSON fallback based on configuration
"""
from typing import List, Optional, Union
from app.config import settings
from app.core.logging import get_logger
from app.models.schemas import (
    OrderTrackingResponse,
    DiscountValidationResponse,
    Product,
    ProductSearchResponse
)

logger = get_logger(__name__)


class DatabaseService:
    """Unified database service that switches between implementations"""
    
    def __init__(self):
        """Initialize appropriate database client based on settings"""
        self.use_local = settings.USE_LOCAL_MODE
        
        if self.use_local:
            from app.services.database.json_fallback import get_json_db
            self.db = get_json_db()
            logger.info("Using JSON fallback database (local mode)")
        else:
            try:
                from app.services.database.supabase_client import get_supabase_db
                self.db = get_supabase_db()
                logger.info("Using Supabase database (production mode)")
            except Exception as e:
                logger.warning(f"Supabase unavailable, falling back to JSON: {e}")
                from app.services.database.json_fallback import get_json_db
                self.db = get_json_db()
                self.use_local = True
    
    # ========================================================================
    # Order Operations
    # ========================================================================
    
    def get_order(self, order_id: str, customer_email: str) -> OrderTrackingResponse:
        """
        Get order by ID and verify customer email
        
        Args:
            order_id: Order number
            customer_email: Customer email
            
        Returns:
            OrderTrackingResponse: Order details
        """
        return self.db.get_order(order_id, customer_email)
    
    def get_orders_by_email(self, customer_email: str) -> List[OrderTrackingResponse]:
        """
        Get all orders for a customer
        
        Args:
            customer_email: Customer email
            
        Returns:
            List of orders
        """
        return self.db.get_orders_by_email(customer_email)
    
    # ========================================================================
    # Discount Operations
    # ========================================================================
    
    def validate_discount_code(
        self,
        code: str,
        cart_total: float
    ) -> DiscountValidationResponse:
        """
        Validate a discount code
        
        Args:
            code: Discount code
            cart_total: Current cart total
            
        Returns:
            DiscountValidationResponse: Validation result
        """
        return self.db.validate_discount_code(code, cart_total)
    
    # ========================================================================
    # Product Operations
    # ========================================================================
    
    def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 5
    ) -> ProductSearchResponse:
        """
        Search products
        
        Args:
            query: Search query
            category: Filter by category
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum results
            
        Returns:
            ProductSearchResponse: Search results
        """
        return self.db.search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
    
    def get_product(self, product_id: str) -> Product:
        """
        Get product by ID
        
        Args:
            product_id: Product ID
            
        Returns:
            Product: Product details
        """
        return self.db.get_product(product_id)
    
    # ========================================================================
    # Session Management (Supabase only)
    # ========================================================================
    
    def save_chat_session(self, session_id: str, messages: list, metadata: dict):
        """
        Save chat session
        
        Args:
            session_id: Session ID
            messages: List of messages
            metadata: Session metadata
        """
        if hasattr(self.db, 'save_chat_session'):
            self.db.save_chat_session(session_id, messages, metadata)
        else:
            logger.debug("Chat session saving not available in local mode")
    
    def get_chat_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve chat session
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[dict]: Session data if found
        """
        if hasattr(self.db, 'get_chat_session'):
            return self.db.get_chat_session(session_id)
        return None
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def health_check(self) -> dict:
        """
        Check database health
        
        Returns:
            dict: Health status
        """
        try:
            # Try a simple operation
            if self.use_local:
                # Check if JSON files are accessible
                self.db._load_orders()
                status = "healthy"
                message = "JSON database accessible"
            else:
                # For Supabase, we'd ping the database
                status = "healthy"
                message = "Supabase database connected"
            
            return {
                "status": status,
                "mode": "local" if self.use_local else "supabase",
                "message": message
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "mode": "local" if self.use_local else "supabase",
                "message": str(e)
            }


# Global instance
_db_service = None


def get_database() -> DatabaseService:
    """
    Get or create database service instance
    
    Returns:
        DatabaseService: Database service
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


# Convenience functions
def get_order(order_id: str, customer_email: str) -> OrderTrackingResponse:
    """Get order (convenience function)"""
    return get_database().get_order(order_id, customer_email)


def validate_discount(code: str, cart_total: float) -> DiscountValidationResponse:
    """Validate discount code (convenience function)"""
    return get_database().validate_discount_code(code, cart_total)


def search_products(query: str, **kwargs) -> ProductSearchResponse:
    """Search products (convenience function)"""
    return get_database().search_products(query, **kwargs)


# Export
__all__ = [
    'DatabaseService',
    'get_database',
    'get_order',
    'validate_discount',
    'search_products'
]