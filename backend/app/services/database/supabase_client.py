"""
JSON Fallback Database
Local JSON file-based data access for demo mode
"""
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from app.core.logging import get_logger
from app.core.errors import OrderNotFoundException, ProductNotFoundException, DatabaseException
from app.models.schemas import (
    OrderTrackingResponse,
    OrderItem,
    OrderStatus,
    DiscountValidationResponse,
    Product,
    ProductSearchResponse
)

logger = get_logger(__name__)


class JSONDatabase:
    """JSON file-based database for demo mode"""
    
    def __init__(self, data_dir: str = "data/fallback"):
        """
        Initialize JSON database
        
        Args:
            data_dir: Directory containing JSON files
        """
        self.data_dir = Path(data_dir)
        self._orders_cache = None
        self._discounts_cache = None
        self._products_cache = None
        
        logger.info(f"Initialized JSON database from {self.data_dir}")
    
    def _load_json_file(self, filename: str) -> dict:
        """
        Load and parse JSON file
        
        Args:
            filename: Name of JSON file
            
        Returns:
            dict: Parsed JSON data
        """
        filepath = self.data_dir / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded {filename}")
            return data
        except FileNotFoundError:
            logger.error(f"JSON file not found: {filepath}")
            raise DatabaseException(f"Data file not found: {filename}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            raise DatabaseException(f"Invalid JSON format in {filename}")
    
    def _load_orders(self) -> List[dict]:
        """Load orders from JSON"""
        if self._orders_cache is None:
            data = self._load_json_file("orders.json")
            self._orders_cache = data.get("orders", [])
        return self._orders_cache
    
    def _load_discounts(self) -> List[dict]:
        """Load discount codes from JSON"""
        if self._discounts_cache is None:
            data = self._load_json_file("discount_codes.json")
            self._discounts_cache = data.get("discount_codes", [])
        return self._discounts_cache
    
    def _load_products(self) -> List[dict]:
        """Load products from knowledge base"""
        if self._products_cache is None:
            filepath = Path("data/knowledge_base/product_catalog.json")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._products_cache = data.get("products", [])
            except Exception as e:
                logger.error(f"Failed to load products: {e}")
                self._products_cache = []
        return self._products_cache
    
    # ========================================================================
    # Order Operations
    # ========================================================================
    
    def get_order(self, order_id: str, customer_email: str) -> OrderTrackingResponse:
        """
        Get order by ID and verify customer email
        
        Args:
            order_id: Order number (e.g., ORD-123456)
            customer_email: Customer email for verification
            
        Returns:
            OrderTrackingResponse: Order details
            
        Raises:
            OrderNotFoundException: If order not found or email mismatch
        """
        orders = self._load_orders()
        
        # Find order
        order = None
        for o in orders:
            if o["order_number"] == order_id:
                order = o
                break
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise OrderNotFoundException(order_id)
        
        # Verify email
        if order["customer_email"].lower() != customer_email.lower():
            logger.warning(
                f"Email mismatch for order {order_id}",
                extra={"provided": customer_email}
            )
            raise OrderNotFoundException(order_id)
        
        # Convert to response model
        order_items = [
            OrderItem(**item) for item in order["items"]
        ]
        
        response = OrderTrackingResponse(
            order_number=order["order_number"],
            status=OrderStatus(order["status"]),
            items=order_items,
            total=order["total"],
            tracking_number=order.get("tracking_number"),
            estimated_delivery=datetime.fromisoformat(order["estimated_delivery"].replace("Z", "+00:00")) 
                if order.get("estimated_delivery") else None,
            created_at=datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")),
            status_history=order.get("status_history")
        )
        
        logger.info(f"Retrieved order {order_id}")
        return response
    
    def get_orders_by_email(self, customer_email: str) -> List[OrderTrackingResponse]:
        """
        Get all orders for a customer
        
        Args:
            customer_email: Customer email
            
        Returns:
            List of orders
        """
        orders = self._load_orders()
        
        customer_orders = [
            o for o in orders 
            if o["customer_email"].lower() == customer_email.lower()
        ]
        
        results = []
        for order in customer_orders:
            order_items = [OrderItem(**item) for item in order["items"]]
            
            results.append(OrderTrackingResponse(
                order_number=order["order_number"],
                status=OrderStatus(order["status"]),
                items=order_items,
                total=order["total"],
                tracking_number=order.get("tracking_number"),
                estimated_delivery=datetime.fromisoformat(order["estimated_delivery"].replace("Z", "+00:00"))
                    if order.get("estimated_delivery") else None,
                created_at=datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")),
                status_history=order.get("status_history")
            ))
        
        logger.info(f"Retrieved {len(results)} orders for {customer_email}")
        return results
    
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
        discounts = self._load_discounts()
        
        # Find discount code (case-insensitive)
        discount = None
        for d in discounts:
            if d["code"].upper() == code.upper():
                discount = d
                break
        
        if not discount:
            return DiscountValidationResponse(
                code=code,
                valid=False,
                message=f"Discount code '{code}' not found"
            )
        
        # Check if active
        if not discount.get("active", True):
            return DiscountValidationResponse(
                code=code,
                valid=False,
                message=f"Discount code '{code}' is no longer active"
            )
        
        # Check expiration
        valid_until = datetime.fromisoformat(discount["valid_until"].replace("Z", "+00:00"))
        if datetime.now(valid_until.tzinfo) > valid_until:
            return DiscountValidationResponse(
                code=code,
                valid=False,
                message=f"Discount code '{code}' has expired",
                expires_at=valid_until
            )
        
        # Check minimum purchase
        min_purchase = discount.get("min_purchase", 0)
        if cart_total < min_purchase:
            return DiscountValidationResponse(
                code=code,
                valid=False,
                message=f"Minimum purchase of ${min_purchase:.2f} required (current: ${cart_total:.2f})"
            )
        
        # Check usage limit
        usage_limit = discount.get("usage_limit")
        times_used = discount.get("times_used", 0)
        if usage_limit and times_used >= usage_limit:
            return DiscountValidationResponse(
                code=code,
                valid=False,
                message=f"Discount code '{code}' has reached its usage limit"
            )
        
        # Calculate discount
        if discount.get("free_shipping", False):
            # Free shipping discount
            discount_amount = 0.0
            new_total = cart_total
            message = "Free standard shipping applied!"
        else:
            # Percentage discount
            percentage = discount.get("percentage", 0)
            discount_amount = (cart_total * percentage) / 100
            
            # Apply max discount cap if exists
            max_discount = discount.get("max_discount")
            if max_discount and discount_amount > max_discount:
                discount_amount = max_discount
            
            new_total = cart_total - discount_amount
            message = f"{percentage}% discount applied! You save ${discount_amount:.2f}"
        
        logger.info(
            f"Validated discount code: {code}",
            extra={
                "valid": True,
                "discount_amount": discount_amount,
                "cart_total": cart_total
            }
        )
        
        return DiscountValidationResponse(
            code=code,
            valid=True,
            discount_percentage=discount.get("percentage"),
            discount_amount=discount_amount,
            new_total=new_total,
            message=message,
            expires_at=valid_until
        )
    
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
        products = self._load_products()
        
        # Filter products
        query_lower = query.lower()
        results = []
        
        for product in products:
            # Text search
            searchable_text = (
                f"{product['name']} {product['description']} "
                f"{product['category']} {product.get('subcategory', '')}"
            ).lower()
            
            if query_lower not in searchable_text:
                continue
            
            # Category filter
            if category and product["category"] != category:
                continue
            
            # Price filters
            price = product["price"]
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            
            # Only include in-stock items
            if not product.get("in_stock", False):
                continue
            
            results.append(Product(**product))
        
        # Sort by relevance (simple: exact name match first)
        results.sort(
            key=lambda p: (
                query_lower in p.name.lower(),
                p.rating if p.rating else 0
            ),
            reverse=True
        )
        
        # Limit results
        results = results[:limit]
        
        logger.info(
            f"Product search: '{query}' returned {len(results)} results"
        )
        
        return ProductSearchResponse(
            products=results,
            total_results=len(results),
            query=query
        )
    
    def get_product(self, product_id: str) -> Product:
        """
        Get product by ID
        
        Args:
            product_id: Product ID
            
        Returns:
            Product: Product details
            
        Raises:
            ProductNotFoundException: If product not found
        """
        products = self._load_products()
        
        for product in products:
            if product["product_id"] == product_id:
                return Product(**product)
        
        logger.warning(f"Product not found: {product_id}")
        raise ProductNotFoundException(product_id)
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def clear_cache(self):
        """Clear all cached data"""
        self._orders_cache = None
        self._discounts_cache = None
        self._products_cache = None
        logger.info("Cache cleared")


# Global instance
_db_instance = None


def get_json_db() -> JSONDatabase:
    """
    Get or create JSON database instance
    
    Returns:
        JSONDatabase: Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = JSONDatabase()
    return _db_instance


# Export
__all__ = ['JSONDatabase', 'get_json_db']