"""
Unit tests for error handling utilities.
"""

import pytest
import time
from app.utils.error_handling import (
    retry_with_backoff, capture_error_context, GracefulDegradation,
    ErrorAggregator, PipelineError, TOCExtractionError
)


class TestRetryWithBackoff:
    """Test retry decorator."""
    
    def test_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3)
        def succeeds_immediately():
            call_count[0] += 1
            return "success"
        
        result = succeeds_immediately()
        
        assert result == "success"
        assert call_count[0] == 1
    
    def test_success_after_retries(self):
        """Test function succeeds after retries."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def succeeds_on_third_attempt():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = succeeds_on_third_attempt()
        
        assert result == "success"
        assert call_count[0] == 3
    
    def test_fails_after_max_attempts(self):
        """Test function fails after max attempts."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def always_fails():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        
        assert call_count[0] == 3
    
    def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_times = []
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1, backoff_factor=2.0)
        def fails_twice():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = fails_twice()
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Check delays are approximately correct (0.1s, 0.2s)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert 0.08 < delay1 < 0.15  # ~0.1s with tolerance
        assert 0.18 < delay2 < 0.25  # ~0.2s with tolerance


class TestCaptureErrorContext:
    """Test error context capture."""
    
    def test_captures_error_details(self):
        """Test capturing error details."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            context = {'book_id': '123', 'stage': 'toc_parsing'}
            error_details = capture_error_context(e, context)
        
        assert error_details['error_type'] == 'ValueError'
        assert error_details['error_message'] == 'Test error'
        assert 'stack_trace' in error_details
        assert error_details['context']['book_id'] == '123'
        assert 'timestamp' in error_details
    
    def test_captures_custom_exception(self):
        """Test capturing custom exception."""
        try:
            raise TOCExtractionError("TOC parsing failed")
        except TOCExtractionError as e:
            error_details = capture_error_context(e, {})
        
        assert error_details['error_type'] == 'TOCExtractionError'
        assert error_details['error_message'] == 'TOC parsing failed'


class TestGracefulDegradation:
    """Test graceful degradation context manager."""
    
    def test_suppresses_exception(self):
        """Test exception is suppressed."""
        with GracefulDegradation(fallback_value="fallback"):
            raise ValueError("This should be suppressed")
        
        # Should not raise
    
    def test_returns_fallback_value(self):
        """Test fallback value is accessible."""
        degradation = GracefulDegradation(fallback_value="fallback")
        
        with degradation:
            raise ValueError("Error")
        
        assert degradation.error is not None
        assert degradation.fallback_value == "fallback"
    
    def test_does_not_suppress_other_exceptions(self):
        """Test other exceptions are not suppressed."""
        with pytest.raises(KeyboardInterrupt):
            with GracefulDegradation(suppress_exceptions=(ValueError,)):
                raise KeyboardInterrupt()
    
    def test_no_error_when_successful(self):
        """Test no error when operation succeeds."""
        degradation = GracefulDegradation()
        
        with degradation:
            result = "success"
        
        assert degradation.error is None


class TestErrorAggregator:
    """Test error aggregator."""
    
    def test_captures_multiple_errors(self):
        """Test capturing multiple errors."""
        aggregator = ErrorAggregator()
        
        for i in range(3):
            with aggregator.capture(item_id=i):
                if i % 2 == 0:
                    raise ValueError(f"Error {i}")
        
        assert aggregator.has_errors()
        assert aggregator.error_count == 2
    
    def test_continues_after_errors(self):
        """Test processing continues after errors."""
        aggregator = ErrorAggregator()
        processed = []
        
        for i in range(5):
            with aggregator.capture(item_id=i):
                if i == 2:
                    raise ValueError("Error at 2")
                processed.append(i)
        
        assert processed == [0, 1, 3, 4]
        assert aggregator.error_count == 1
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        aggregator = ErrorAggregator()
        
        with aggregator.capture(item_id=1):
            raise ValueError("Error 1")
        
        with aggregator.capture(item_id=2):
            raise TypeError("Error 2")
        
        with aggregator.capture(item_id=3):
            raise ValueError("Error 3")
        
        summary = aggregator.get_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['error_types']['ValueError'] == 2
        assert summary['error_types']['TypeError'] == 1
    
    def test_no_errors_initially(self):
        """Test aggregator has no errors initially."""
        aggregator = ErrorAggregator()
        
        assert not aggregator.has_errors()
        assert aggregator.error_count == 0


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_pipeline_error(self):
        """Test PipelineError."""
        with pytest.raises(PipelineError, match="Test error"):
            raise PipelineError("Test error")
    
    def test_toc_extraction_error(self):
        """Test TOCExtractionError."""
        with pytest.raises(TOCExtractionError):
            raise TOCExtractionError("TOC failed")
    
    def test_exception_inheritance(self):
        """Test exception inheritance."""
        try:
            raise TOCExtractionError("Test")
        except PipelineError:
            # Should catch as PipelineError
            pass
