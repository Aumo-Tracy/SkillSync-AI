"""
Custom Logging Configuration
Structured JSON logging for production monitoring
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        
        # Lazy import to avoid circular dependency
        try:
            from app.config import settings
            log_record['app_name'] = settings.APP_NAME
            log_record['environment'] = settings.ENVIRONMENT
        except ImportError:
            log_record['app_name'] = 'ECommerce Support AI'
            log_record['environment'] = 'development'
        
        # Add context if available
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        if hasattr(record, 'user_email'):
            log_record['user_email'] = record.user_email
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id


def setup_logging() -> None:
    """Configure application logging"""
    
    # Lazy import to avoid circular dependency
    try:
        from app.config import settings
        log_level = settings.LOG_LEVEL.upper()
        is_production = settings.is_production
        use_local_mode = settings.USE_LOCAL_MODE
    except ImportError:
        log_level = "INFO"
        is_production = False
        use_local_mode = True
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if is_production:
        # JSON logging for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable logging for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log configuration
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "environment": "production" if is_production else "development",
            "use_local_mode": use_local_mode
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module"""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding context to log records"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


# Usage tracking logger
usage_logger = get_logger('usage')
error_logger = get_logger('error')
security_logger = get_logger('security')
performance_logger = get_logger('performance')


# Export all public functions and loggers
__all__ = [
    'setup_logging',
    'get_logger',
    'LogContext',
    'usage_logger',
    'error_logger',
    'security_logger',
    'performance_logger',
    'CustomJsonFormatter'
]