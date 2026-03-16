"""
LangChain Tools
All tools for the e-commerce support agent
"""
import time
from typing import Dict, Any
from datetime import datetime
from langchain.tools import tool
from app.core.logging import get_logger, usage_logger
from app.core.errors import handle_tool_error
from app.core.security import InputValidator
from app.services.database import get_database
from app.models.schemas import (
    OrderTrackingResponse,
    DiscountValidationResponse,
    ReturnEligibilityResponse,
    ProductSearchResponse,
    EscalationResponse,
    ReturnReason
)

logger = get_logger(__name__)
validator = InputValidator()


# ============================================================================
# Tool 1: Order Tracking
# ============================================================================

@tool
def track_order(order_id: str, customer_email: str) -> Dict[str, Any]:
    """
    Track an order by order ID and customer email.
    Use this when the customer wants to know the status of their order.
    
    Args:
        order_id: The order number (format: ORD-XXXXXX)
        customer_email: Customer's email address for verification
    
    Returns:
        Dictionary with order status, tracking info, and estimated delivery
    
    Examples:
        - "Where is my order ORD-123456?"
        - "Track my package"
        - "What's the status of order ORD-789012?"
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not validator.validate_order_id(order_id):
            return {
                "success": False,
                "error": "Invalid order ID format. Should be ORD-XXXXXX"
            }
        
        if not validator.validate_email_address(customer_email):
            return {
                "success": False,
                "error": "Invalid email address"
            }
        
        # Get order from database
        db = get_database()
        order = db.get_order(order_id, customer_email)
        
        # Format response
        result = {
            "success": True,
            "order_number": order.order_number,
            "status": order.status.value,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": item.price
                }
                for item in order.items
            ],
            "total": order.total,
            "tracking_number": order.tracking_number,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "created_at": order.created_at.isoformat(),
            "status_history": order.status_history
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        usage_logger.info(
            "Order tracked successfully",
            extra={
                "tool": "track_order",
                "order_id": order_id,
                "status": order.status.value,
                "execution_time_ms": execution_time
            }
        )
        
        return result
    
    except Exception as e:
        return handle_tool_error("track_order", e)


# ============================================================================
# Tool 2: Discount Code Validation
# ============================================================================

@tool
def validate_discount_code(code: str, cart_total: float) -> Dict[str, Any]:
    """
    Validate a discount code and calculate the discount amount.
    Use this when customer wants to check if a discount code is valid.
    
    Args:
        code: The discount code to validate
        cart_total: Current cart total amount
    
    Returns:
        Dictionary with validation result, discount amount, and new total
    
    Examples:
        - "Is code SAVE20 valid?"
        - "How much will I save with WELCOME10?"
        - "Does my discount code work?"
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        code = code.upper().strip()
        
        if not validator.validate_discount_code(code):
            return {
                "success": False,
                "error": "Invalid discount code format"
            }
        
        if cart_total < 0:
            return {
                "success": False,
                "error": "Invalid cart total"
            }
        
        # Validate code
        db = get_database()
        result = db.validate_discount_code(code, cart_total)
        
        # Format response
        response = {
            "success": True,
            "code": result.code,
            "valid": result.valid,
            "message": result.message,
            "discount_percentage": result.discount_percentage,
            "discount_amount": result.discount_amount,
            "new_total": result.new_total,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        usage_logger.info(
            "Discount code validated",
            extra={
                "tool": "validate_discount_code",
                "code": code,
                "valid": result.valid,
                "execution_time_ms": execution_time
            }
        )
        
        return response
    
    except Exception as e:
        return handle_tool_error("validate_discount_code", e)


# ============================================================================
# Tool 3: Return Eligibility Checker
# ============================================================================

@tool
def check_return_eligibility(order_id: str, customer_email: str, reason: str = "changed_mind") -> Dict[str, Any]:
    """
    Check if an order is eligible for return based on return policy.
    Use this when customer wants to return an item.
    
    Args:
        order_id: The order number (format: ORD-XXXXXX)
        customer_email: Customer's email address
        reason: Return reason (defective, wrong_item, changed_mind, not_as_described, damaged)
    
    Returns:
        Dictionary with eligibility status, return window, and instructions
    
    Examples:
        - "Can I return my order?"
        - "Am I still within the return window?"
        - "How do I return this defective item?"
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not validator.validate_order_id(order_id):
            return {
                "success": False,
                "error": "Invalid order ID format"
            }
        
        if not validator.validate_email_address(customer_email):
            return {
                "success": False,
                "error": "Invalid email address"
            }
        
        # Get order
        db = get_database()
        order = db.get_order(order_id, customer_email)
        
        # Check if order is delivered
        if order.status.value not in ["delivered", "shipped"]:
            return {
                "success": True,
                "eligible": False,
                "reason": "Order must be delivered before initiating a return"
            }
        
        # Calculate days since order
        days_since_order = (datetime.now() - order.created_at.replace(tzinfo=None)).days
        
        # Determine return window based on product category
        # Check first item's category (simplified)
        return_window_days = 30  # Default
        
        # Check if any electronics (14 days)
        for item in order.items:
            # In real implementation, would check product category
            # Simplified for demo
            if "electronics" in item.name.lower() or "watch" in item.name.lower():
                return_window_days = 14
                break
        
        # Check eligibility
        days_remaining = return_window_days - days_since_order
        eligible = days_remaining > 0
        
        # Build instructions
        if eligible:
            if reason in ["defective", "wrong_item", "damaged"]:
                instructions = (
                    "1. We'll email you a prepaid return label (free return shipping)\n"
                    "2. Pack the item in its original packaging\n"
                    "3. Attach the label and drop off at any authorized location\n"
                    "4. Refund will be processed within 5-7 business days after we receive the return"
                )
            else:
                instructions = (
                    "1. Log into your account and go to 'My Orders'\n"
                    "2. Select the order and click 'Return Items'\n"
                    "3. Print the return label ($6.99 shipping fee will be deducted from refund)\n"
                    "4. Pack and ship the item\n"
                    "5. Refund will be processed within 5-7 business days"
                )
        else:
            instructions = (
                f"Unfortunately, the {return_window_days}-day return window has expired. "
                "Please contact customer support for exceptions in case of defective items."
            )
        
        result = {
            "success": True,
            "eligible": eligible,
            "reason": f"Order is within {return_window_days}-day return window" if eligible else f"Return window ({return_window_days} days) has expired",
            "return_window_days": return_window_days,
            "days_remaining": max(0, days_remaining),
            "days_since_order": days_since_order,
            "instructions": instructions,
            "free_return_shipping": reason in ["defective", "wrong_item", "damaged"]
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        usage_logger.info(
            "Return eligibility checked",
            extra={
                "tool": "check_return_eligibility",
                "order_id": order_id,
                "eligible": eligible,
                "reason": reason,
                "execution_time_ms": execution_time
            }
        )
        
        return result
    
    except Exception as e:
        return handle_tool_error("check_return_eligibility", e)


# ============================================================================
# Tool 4: Product Search
# ============================================================================

@tool
def search_products(query: str, category: str = None, max_price: float = None) -> Dict[str, Any]:
    """
    Search for products in the catalog.
    Use this when customer is looking for products to buy.
    
    Args:
        query: Search query (product name, description keywords)
        category: Optional category filter (electronics, clothing, home, etc.)
        max_price: Optional maximum price filter
    
    Returns:
        Dictionary with matching products and their details
    
    Examples:
        - "Show me wireless headphones"
        - "Do you have coffee makers under $100?"
        - "I'm looking for yoga mats"
    """
    start_time = time.time()
    
    try:
        # Validate inputs
        if not validator.validate_product_search_query(query):
            return {
                "success": False,
                "error": "Invalid search query"
            }
        
        # Search products
        db = get_database()
        results = db.search_products(
            query=query,
            category=category,
            max_price=max_price,
            limit=5
        )
        
        # Format response
        products = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "price": p.price,
                "in_stock": p.in_stock,
                "rating": p.rating,
                "image_url": p.image_url
            }
            for p in results.products
        ]
        
        result = {
            "success": True,
            "products": products,
            "total_results": results.total_results,
            "query": results.query
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        usage_logger.info(
            "Product search completed",
            extra={
                "tool": "search_products",
                "query": query,
                "results_count": len(products),
                "execution_time_ms": execution_time
            }
        )
        
        return result
    
    except Exception as e:
        return handle_tool_error("search_products", e)


# ============================================================================
# Tool 5: Escalate to Human Agent
# ============================================================================

@tool
def escalate_to_human(reason: str, context: str) -> Dict[str, Any]:
    """
    Escalate the conversation to a human customer support agent.
    Use this ONLY when you cannot resolve the issue or when the customer explicitly requests human support.
    
    Args:
        reason: Reason for escalation (complex_issue, angry_customer, payment_dispute, policy_exception, technical_issue, other)
        context: Brief summary of the conversation and issue
    
    Returns:
        Dictionary with ticket number and estimated wait time
    
    Examples:
        - Customer asks: "I want to speak to a manager"
        - Complex refund dispute that requires manual intervention
        - Technical issue beyond standard troubleshooting
        - Customer is very frustrated or angry
    """
    start_time = time.time()
    
    try:
        # Generate ticket number
        import uuid
        ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine priority and wait time based on reason
        priority_map = {
            "angry_customer": ("high", 5),
            "payment_dispute": ("high", 10),
            "policy_exception": ("medium", 15),
            "complex_issue": ("medium", 20),
            "technical_issue": ("low", 30),
            "other": ("low", 30)
        }
        
        priority, wait_time = priority_map.get(reason.lower(), ("medium", 20))
        
        result = {
            "success": True,
            "ticket_number": ticket_number,
            "priority": priority,
            "estimated_wait_time_minutes": wait_time,
            "message": (
                f"I've created support ticket {ticket_number} and escalated your case to our team. "
                f"A human agent will contact you within {wait_time} minutes. "
                "You'll receive an email confirmation shortly."
            ),
            "created_at": datetime.utcnow().isoformat()
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        usage_logger.info(
            "Escalated to human agent",
            extra={
                "tool": "escalate_to_human",
                "reason": reason,
                "priority": priority,
                "ticket_number": ticket_number,
                "execution_time_ms": execution_time
            }
        )
        
        # In production, this would create an actual support ticket
        logger.warning(
            f"Human escalation requested",
            extra={
                "ticket_number": ticket_number,
                "reason": reason,
                "context_preview": context[:200]
            }
        )
        
        return result
    
    except Exception as e:
        return handle_tool_error("escalate_to_human", e)


# ============================================================================
# Export all tools
# ============================================================================

ALL_TOOLS = [
    track_order,
    validate_discount_code,
    check_return_eligibility,
    search_products,
    escalate_to_human
]

__all__ = [
    'track_order',
    'validate_discount_code',
    'check_return_eligibility',
    'search_products',
    'escalate_to_human',
    'ALL_TOOLS'
]