"""
Error Handling Module
Custom exceptions and FastAPI exception handlers
"""
from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime


# ============================================================================
# Custom Exceptions
# ============================================================================

class BaseAPIException(Exception):
    """Base exception for API errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.detail = detail
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            detail=detail
        )


class AuthenticationException(BaseAPIException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            detail=detail
        )


class AuthorizationException(BaseAPIException):
    """Raised when user lacks permissions"""
    
    def __init__(self, message: str = "Insufficient permissions", detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            detail=detail
        )


class NotFoundException(BaseAPIException):
    """Raised when resource is not found"""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            detail=f"The requested {resource.lower()} does not exist"
        )


class OrderNotFoundException(NotFoundException):
    """Raised when order is not found"""
    
    def __init__(self, order_id: str):
        super().__init__("Order", order_id)


class ProductNotFoundException(NotFoundException):
    """Raised when product is not found"""
    
    def __init__(self, product_id: str):
        super().__init__("Product", product_id)


class DiscountCodeException(BaseAPIException):
    """Raised for discount code errors"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="DISCOUNT_CODE_ERROR",
            detail=detail
        )


class RateLimitException(BaseAPIException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        detail = f"Retry after {retry_after} seconds" if retry_after else None
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            detail=detail
        )


class ExternalAPIException(BaseAPIException):
    """Raised when external API call fails"""
    
    def __init__(self, service: str, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"{service} API error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_API_ERROR",
            detail=detail
        )


class OpenAIException(ExternalAPIException):
    """Raised when OpenAI API fails"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__("OpenAI", message, detail)


class VectorStoreException(BaseAPIException):
    """Raised when vector store operations fail"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Vector store error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="VECTOR_STORE_ERROR",
            detail=detail
        )


class DatabaseException(BaseAPIException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            detail=detail
        )


class ToolExecutionException(BaseAPIException):
    """Raised when tool execution fails"""
    
    def __init__(self, tool_name: str, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="TOOL_EXECUTION_ERROR",
            detail=detail
        )


# ============================================================================
# Exception Handlers
# ============================================================================

def _create_error_dict(error: str, detail: Optional[str] = None, error_code: Optional[str] = None) -> dict:
    """Create error response dictionary"""
    return {
        "error": error,
        "detail": detail,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat()
    }


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handler for BaseAPIException and subclasses
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with error details
    """
    # Lazy import to avoid circular dependency
    from app.core.logging import error_logger
    
    error_logger.error(
        exc.message,
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail
        }
    )
    
    error_response = _create_error_dict(
        error=exc.message,
        detail=exc.detail,
        error_code=exc.error_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for Pydantic validation errors
    
    Args:
        request: FastAPI request
        exc: Validation exception
        
    Returns:
        JSONResponse with validation errors
    """
    from app.core.logging import error_logger
    
    errors = exc.errors()
    error_details = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error['loc'])
        error_details.append(f"{field}: {error['msg']}")
    
    error_logger.warning(
        "Validation error",
        extra={
            "path": request.url.path,
            "errors": errors
        }
    )
    
    error_response = _create_error_dict(
        error="Validation error",
        detail="; ".join(error_details),
        error_code="VALIDATION_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions
    
    Args:
        request: FastAPI request
        exc: Exception instance
        
    Returns:
        JSONResponse with generic error
    """
    from app.core.logging import error_logger
    from app.config import settings
    
    error_logger.error(
        "Unexpected error",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Don't expose internal errors in production
    if settings.is_production:
        message = "An unexpected error occurred"
        detail = "Please try again later"
    else:
        message = f"Unexpected error: {type(exc).__name__}"
        detail = str(exc)
    
    error_response = _create_error_dict(
        error=message,
        detail=detail,
        error_code="INTERNAL_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    
    # Custom exceptions
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")


# ============================================================================
# Error Response Helpers
# ============================================================================

def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    detail: Optional[str] = None
) -> JSONResponse:
    """
    Create a standard error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Application error code
        detail: Additional details
        
    Returns:
        JSONResponse with error
    """
    error_response = _create_error_dict(
        error=message,
        detail=detail,
        error_code=error_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def handle_tool_error(tool_name: str, error: Exception) -> dict:
    """
    Handle errors during tool execution
    
    Args:
        tool_name: Name of the tool
        error: Exception that occurred
        
    Returns:
        dict: Error information for response
    """
    from app.core.logging import error_logger
    
    error_logger.error(
        f"Tool execution failed: {tool_name}",
        extra={
            "tool_name": tool_name,
            "error_type": type(error).__name__,
            "error_message": str(error)
        },
        exc_info=True
    )
    
    return {
        "success": False,
        "error": str(error),
        "tool_name": tool_name
    }


# Export all exception classes and handlers
__all__ = [
    # Base exception
    'BaseAPIException',
    
    # Specific exceptions
    'ValidationException',
    'AuthenticationException',
    'AuthorizationException',
    'NotFoundException',
    'OrderNotFoundException',
    'ProductNotFoundException',
    'DiscountCodeException',
    'RateLimitException',
    'ExternalAPIException',
    'OpenAIException',
    'VectorStoreException',
    'DatabaseException',
    'ToolExecutionException',
    
    # Handlers
    'base_api_exception_handler',
    'validation_exception_handler',
    'generic_exception_handler',
    'register_exception_handlers',
    
    # Helpers
    'create_error_response',
    'handle_tool_error'
]