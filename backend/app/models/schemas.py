"""
Pydantic Models for Request/Response Validation
"""
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum


# ============================================================================
# Chat Models
# ============================================================================

class MessageRole(str, Enum):
    """Message role types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chat request from frontend"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_email: Optional[EmailStr] = None
    include_sources: bool = True
    
    @validator('message')
    def sanitize_message(cls, v):
        """Basic input sanitization"""
        return v.strip()


class SourceDocument(BaseModel):
    """Retrieved source document"""
    document_name: str
    chunk_text: str
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = None


class ToolCall(BaseModel):
    """Tool execution information"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    execution_time_ms: float
    success: bool
    error: Optional[str] = None


class TokenUsage(BaseModel):
    """Token usage and cost tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model: str


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str
    session_id: str
    sources: Optional[List[SourceDocument]] = None
    tool_calls: Optional[List[ToolCall]] = None
    token_usage: Optional[TokenUsage] = None
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Order Models
# ============================================================================

class OrderStatus(str, Enum):
    """Order status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderItem(BaseModel):
    """Single item in an order"""
    product_id: str
    name: str
    quantity: int = Field(ge=1)
    price: float = Field(ge=0)
    
    @property
    def subtotal(self) -> float:
        return self.quantity * self.price


class OrderTrackingRequest(BaseModel):
    """Request to track an order"""
    order_id: str = Field(..., pattern=r'^ORD-\d{6}$')
    email: EmailStr


class OrderTrackingResponse(BaseModel):
    """Order tracking information"""
    order_number: str
    status: OrderStatus
    items: List[OrderItem]
    total: float
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    created_at: datetime
    status_history: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Discount Models
# ============================================================================

class DiscountValidationRequest(BaseModel):
    """Request to validate a discount code"""
    code: str = Field(..., min_length=3, max_length=20)
    cart_total: float = Field(ge=0)
    
    @validator('code')
    def uppercase_code(cls, v):
        return v.upper().strip()


class DiscountValidationResponse(BaseModel):
    """Discount validation result"""
    code: str
    valid: bool
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    new_total: Optional[float] = None
    message: str
    expires_at: Optional[datetime] = None


# ============================================================================
# Return/Refund Models
# ============================================================================

class ReturnReason(str, Enum):
    """Return reason types"""
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    CHANGED_MIND = "changed_mind"
    NOT_AS_DESCRIBED = "not_as_described"
    DAMAGED = "damaged"


class ReturnEligibilityRequest(BaseModel):
    """Request to check return eligibility"""
    order_id: str = Field(..., pattern=r'^ORD-\d{6}$')
    email: EmailStr
    reason: ReturnReason


class ReturnEligibilityResponse(BaseModel):
    """Return eligibility information"""
    eligible: bool
    reason: str
    return_window_days: Optional[int] = None
    days_remaining: Optional[int] = None
    instructions: Optional[str] = None
    return_label_url: Optional[str] = None


# ============================================================================
# Product Search Models
# ============================================================================

class ProductSearchRequest(BaseModel):
    """Request to search products"""
    query: str = Field(..., min_length=2, max_length=200)
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    limit: int = Field(5, ge=1, le=20)


class Product(BaseModel):
    """Product information"""
    product_id: str
    name: str
    description: str
    category: str
    price: float
    in_stock: bool
    rating: Optional[float] = Field(None, ge=0, le=5)
    image_url: Optional[str] = None


class ProductSearchResponse(BaseModel):
    """Product search results"""
    products: List[Product]
    total_results: int
    query: str


# ============================================================================
# Escalation Models
# ============================================================================

class EscalationReason(str, Enum):
    """Escalation reason types"""
    COMPLEX_ISSUE = "complex_issue"
    ANGRY_CUSTOMER = "angry_customer"
    PAYMENT_DISPUTE = "payment_dispute"
    POLICY_EXCEPTION = "policy_exception"
    TECHNICAL_ISSUE = "technical_issue"
    OTHER = "other"


class EscalationRequest(BaseModel):
    """Request to escalate to human"""
    reason: EscalationReason
    context: str = Field(..., max_length=1000)
    priority: Literal["low", "medium", "high"] = "medium"


class EscalationResponse(BaseModel):
    """Escalation confirmation"""
    ticket_number: str
    estimated_wait_time_minutes: int
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Session & Analytics Models
# ============================================================================

class SessionMetadata(BaseModel):
    """Chat session metadata"""
    session_id: str
    user_email: Optional[EmailStr] = None
    started_at: datetime
    last_activity: datetime
    message_count: int
    resolved: bool
    total_tokens_used: int
    total_cost_usd: float


class AnalyticsSummary(BaseModel):
    """Analytics summary data"""
    total_sessions: int
    total_messages: int
    average_messages_per_session: float
    resolution_rate: float
    total_tokens_used: int
    total_cost_usd: float
    top_queries: List[Dict[str, Any]]
    tool_usage_stats: Dict[str, int]


# ============================================================================
# Health Check Models
# ============================================================================

class HealthCheck(BaseModel):
    """API health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    components: Dict[str, bool]  # openai, supabase, vector_store, etc.
    uptime_seconds: float


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)