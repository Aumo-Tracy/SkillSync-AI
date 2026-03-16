import time
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def call_succeeded(self):
        self.failure_count = 0
        self.is_open = False
    
    def call_failed(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                f"Circuit breaker opened after "
                f"{self.failure_count} failures"
            )
    
    def can_proceed(self) -> bool:
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if time.time() - self.last_failure_time > self.recovery_timeout:
            self.is_open = False
            self.failure_count = 0
            logger.info("Circuit breaker reset — attempting recovery")
            return True
        
        return False