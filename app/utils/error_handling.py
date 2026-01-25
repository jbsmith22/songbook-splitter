"""
Error handling utilities for robust pipeline execution.

This module provides:
- Retry decorator with exponential backoff
- Error context capture
- Graceful degradation patterns
- Custom exception classes
"""

import time
import traceback
import functools
from typing import Callable, Any, Optional, Dict, Type, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Custom exception classes
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class TOCExtractionError(PipelineError):
    """Error during TOC extraction."""
    pass


class PageMappingError(PipelineError):
    """Error during page mapping."""
    pass


class VerificationError(PipelineError):
    """Error during song verification."""
    pass


class SplittingError(PipelineError):
    """Error during PDF splitting."""
    pass


class QualityGateError(PipelineError):
    """Error when quality gates fail."""
    pass


# Retry decorator
def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry
    
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def capture_error_context(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture detailed error context for debugging.
    
    Args:
        error: Exception that occurred
        context: Additional context information
    
    Returns:
        Dictionary with error details
    """
    error_details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'stack_trace': traceback.format_exc(),
        'timestamp': datetime.utcnow().isoformat(),
        'context': context
    }
    
    logger.error(f"Error captured: {error_details['error_type']} - {error_details['error_message']}")
    
    return error_details


class GracefulDegradation:
    """
    Context manager for graceful degradation.
    
    Allows operations to fail gracefully with fallback behavior.
    
    Example:
        with GracefulDegradation(fallback_value=[], log_errors=True):
            result = risky_operation()
    """
    
    def __init__(self, fallback_value: Any = None, log_errors: bool = True,
                 suppress_exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        """
        Initialize graceful degradation context.
        
        Args:
            fallback_value: Value to return if operation fails
            log_errors: Whether to log errors
            suppress_exceptions: Tuple of exception types to suppress
        """
        self.fallback_value = fallback_value
        self.log_errors = log_errors
        self.suppress_exceptions = suppress_exceptions
        self.error = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, self.suppress_exceptions):
            if self.log_errors:
                logger.warning(f"Operation failed gracefully: {exc_type.__name__}: {exc_val}")
            
            self.error = exc_val
            return True  # Suppress exception
        
        return False  # Don't suppress other exceptions


def with_fallback(primary_func: Callable, fallback_func: Callable,
                 exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    """
    Decorator that provides fallback function if primary fails.
    
    Args:
        primary_func: Primary function to try
        fallback_func: Fallback function if primary fails
        exceptions: Exceptions to catch
    
    Example:
        def primary():
            return expensive_operation()
        
        def fallback():
            return cheap_operation()
        
        result = with_fallback(primary, fallback)()
    """
    @functools.wraps(primary_func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return primary_func(*args, **kwargs)
        except exceptions as e:
            logger.warning(f"Primary function {primary_func.__name__} failed: {e}. Using fallback.")
            return fallback_func(*args, **kwargs)
    
    return wrapper


class ErrorAggregator:
    """
    Aggregates errors during batch processing.
    
    Allows processing to continue even when individual items fail.
    
    Example:
        aggregator = ErrorAggregator()
        
        for item in items:
            with aggregator.capture(item_id=item.id):
                process_item(item)
        
        if aggregator.has_errors():
            print(f"Failed: {aggregator.error_count}")
    """
    
    def __init__(self):
        """Initialize error aggregator."""
        self.errors: list[Dict[str, Any]] = []
    
    def capture(self, **context):
        """
        Context manager to capture errors with context.
        
        Args:
            **context: Context information to attach to error
        """
        return _ErrorCaptureContext(self, context)
    
    def add_error(self, error: Exception, context: Dict[str, Any]):
        """Add an error to the aggregator."""
        error_details = capture_error_context(error, context)
        self.errors.append(error_details)
    
    def has_errors(self) -> bool:
        """Check if any errors were captured."""
        return len(self.errors) > 0
    
    @property
    def error_count(self) -> int:
        """Get number of errors captured."""
        return len(self.errors)
    
    def get_errors(self) -> list[Dict[str, Any]]:
        """Get all captured errors."""
        return self.errors
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors."""
        error_types = {}
        for error in self.errors:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'error_types': error_types,
            'errors': self.errors
        }


class _ErrorCaptureContext:
    """Internal context manager for ErrorAggregator."""
    
    def __init__(self, aggregator: ErrorAggregator, context: Dict[str, Any]):
        self.aggregator = aggregator
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.aggregator.add_error(exc_val, self.context)
            return True  # Suppress exception
        return False


# Utility functions for common error scenarios
def handle_aws_throttling(func: Callable) -> Callable:
    """
    Decorator specifically for handling AWS throttling errors.
    
    Retries with exponential backoff on throttling exceptions.
    """
    return retry_with_backoff(
        max_attempts=5,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=30.0,
        exceptions=(Exception,)  # Would be specific AWS exceptions in real implementation
    )(func)


def log_and_continue(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error and continue processing.
    
    Args:
        error: Exception that occurred
        context: Optional context information
    """
    error_details = capture_error_context(error, context or {})
    logger.warning(f"Error logged, continuing: {error_details['error_type']}")


def fail_fast(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error and raise immediately.
    
    Args:
        error: Exception that occurred
        context: Optional context information
    """
    error_details = capture_error_context(error, context or {})
    logger.error(f"Critical error, failing fast: {error_details['error_type']}")
    raise error
