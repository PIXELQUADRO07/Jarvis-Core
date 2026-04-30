#!/usr/bin/env python3
"""
Retry handler with circuit breaker pattern.
Handles transient failures in LLM service.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any
from logger import debug, warning, error


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing, reject requests
    HALF_OPEN = "half_open"     # Testing recovery


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open - service unavailable"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for service protection.
    
    States:
    - CLOSED: Normal, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 3, timeout: int = 60, name: str = "service"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    debug(f"CircuitBreaker {self.name}: HALF_OPEN (testing recovery)")
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker {self.name} is OPEN (retry in {self.timeout}s)"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset on successful call"""
        with self.lock:
            self.failures = 0
            if self.state != CircuitState.CLOSED:
                debug(f"CircuitBreaker {self.name}: CLOSED (recovered)")
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Track failure"""
        with self.lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                warning(f"CircuitBreaker {self.name}: OPEN after {self.failures} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout expired for HALF_OPEN attempt"""
        if self.last_failure_time is None:
            return False
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout
    
    def status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "threshold": self.failure_threshold,
            "timeout": self.timeout,
            "last_failure": self.last_failure_time
        }


class RetryHandler:
    """
    Retry logic with exponential backoff.
    
    Strategy:
    - Max 3 attempts
    - Base delay: 1 second
    - Backoff multiplier: 1.5x
    - Retries on: ConnectionError, TimeoutError, URLError
    - Does NOT retry on: ValueError, JSON decode errors
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, backoff: float = 1.5):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff = backoff
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Callable to retry
            *args, **kwargs: Arguments to pass
        
        Returns:
            Result from func
        
        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                debug(f"Retry attempt {attempt + 1}/{self.max_retries}")
                result = func(*args, **kwargs)
                if attempt > 0:
                    debug(f"Succeeded on attempt {attempt + 1}")
                return result
            
            except (ConnectionError, TimeoutError, OSError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (self.backoff ** attempt)
                    warning(f"Attempt {attempt + 1} failed: {e}. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    error(f"All {self.max_retries} attempts failed: {e}")
                    raise
            
            except Exception as e:
                # Don't retry on application errors
                error(f"Non-retryable error: {e}")
                raise
        
        # Fallback (shouldn't reach here)
        raise last_exception or Exception("Unknown error after retries")
    
    def get_backoff_time(self, attempt: int) -> float:
        """Calculate backoff time for attempt number"""
        return self.base_delay * (self.backoff ** attempt)


# Module-level singleton instances
_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60, name="ollama")
_retry_handler = RetryHandler(max_retries=3, base_delay=1.0, backoff=1.5)


def get_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker singleton"""
    return _circuit_breaker


def get_retry_handler() -> RetryHandler:
    """Get retry handler singleton"""
    return _retry_handler


def ollama_call(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper for Ollama API calls with retry + circuit breaker.
    
    Usage:
        result = ollama_call(requests.get, url, timeout=5)
    """
    retry_handler = get_retry_handler()
    circuit_breaker = get_circuit_breaker()
    
    def protected_call():
        return circuit_breaker.call(func, *args, **kwargs)
    
    return retry_handler.execute(protected_call)


if __name__ == "__main__":
    # Simple test
    print("🧪 Retry Handler Test")
    print("=" * 50)
    
    # Test 1: Successful call
    def successful_func():
        return "Success!"
    
    handler = RetryHandler()
    result = handler.execute(successful_func)
    print(f"✅ Successful call: {result}")
    
    # Test 2: Backoff calculation
    print(f"\n⏱️  Backoff times (base=1.0, multiplier=1.5):")
    for attempt in range(3):
        wait = handler.get_backoff_time(attempt)
        print(f"  Attempt {attempt}: {wait:.2f}s")
    
    # Test 3: Circuit breaker status
    print(f"\n🔌 Circuit breaker status:")
    cb = get_circuit_breaker()
    print(f"  {cb.status()}")
    
    print("\n✅ Retry handler tests PASSED!")
