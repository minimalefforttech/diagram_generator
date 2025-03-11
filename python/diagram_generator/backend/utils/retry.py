"""Retry utilities for handling service disruptions."""

import asyncio
import functools
from typing import Any, Callable, Optional, Type, TypeVar

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_backoff: bool = True,
        exceptions: tuple[Type[Exception], ...] = (Exception,),
        jitter: float = 0.0
    ):
        """Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_backoff: Whether to use exponential backoff
            exceptions: Tuple of exceptions to retry on
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.exceptions = exceptions
        self.jitter = jitter
        
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate base delay
        if not self.exponential_backoff:
            delay = self.base_delay
        else:
            delay = self.base_delay * (2 ** (attempt - 1))
            delay = min(delay, self.max_delay)
        
        # Add jitter if configured
        if self.jitter > 0:
            import random
            jitter_amount = random.uniform(-self.jitter, self.jitter)
            delay = max(0.0, delay + jitter_amount)
        
        return delay

def with_retries(config: RetryConfig = None) -> Callable:
    """Decorator for retrying functions on failure.
    
    Args:
        config: Retry configuration (uses defaults if None)
        
    Returns:
        Decorated function
    """
    if not config:
        config = RetryConfig()
        
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_error = e
                    
                    if attempt < config.max_attempts:
                        delay = config.get_delay(attempt)
                        await asyncio.sleep(delay)
                    
            raise last_error or Exception("Maximum retry attempts exceeded")
            
        return wrapper
    return decorator

def with_sync_retries(config: RetryConfig = None) -> Callable:
    """Decorator for retrying synchronous functions on failure.
    
    Args:
        config: Retry configuration (uses defaults if None)
        
    Returns:
        Decorated function
    """
    if not config:
        config = RetryConfig()
        
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_error = e
                    
                    if attempt < config.max_attempts:
                        from time import sleep
                        sleep(config.get_delay(attempt))
                    
            raise last_error or Exception("Maximum retry attempts exceeded")
            
        return wrapper
    return decorator

class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_timeout: float = 30.0
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Time in seconds before resetting failure count
            half_open_timeout: Time in seconds before allowing a test request
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
        
    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        current_time = asyncio.get_event_loop().time()
        
        # Reset failure count if enough time has passed
        if current_time - self.last_failure_time > self.reset_timeout:
            self.failures = 0
            
        self.failures += 1
        self.last_failure_time = current_time
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            
    def record_success(self) -> None:
        """Record a success and close the circuit."""
        self.failures = 0
        self.state = "CLOSED"
        
    def can_execute(self) -> bool:
        """Check if execution is allowed.
        
        Returns:
            Whether execution is allowed
        """
        if self.state == "CLOSED":
            return True
            
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_failure_time > self.half_open_timeout:
            self.state = "HALF_OPEN"
            return True
            
        return False

def with_circuit_breaker(breaker: CircuitBreaker) -> Callable:
    """Decorator for applying circuit breaker pattern.
    
    Args:
        breaker: Circuit breaker instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if not breaker.can_execute():
                raise Exception("Circuit breaker is open")
                
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
                
        return wrapper
    return decorator
