"""Tests for retry utilities."""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from diagram_generator.backend.utils.retry import (
    RetryConfig,
    CircuitBreaker,
    with_retries,
    with_sync_retries,
    with_circuit_breaker
)

@pytest.fixture
def retry_config():
    """Create a retry configuration."""
    return RetryConfig(
        max_attempts=3,
        base_delay=0.1,  # Small delays for testing
        max_delay=0.3,
        exponential_backoff=True
    )

@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker."""
    return CircuitBreaker(
        failure_threshold=3,
        reset_timeout=1.0,
        half_open_timeout=0.5
    )

class TestRetryConfig:
    """Tests for RetryConfig."""
    
    def test_init_defaults(self):
        """Test default configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.exponential_backoff is True
        assert config.exceptions == (Exception,)
        
    def test_get_delay_no_backoff(self):
        """Test delay calculation without backoff."""
        config = RetryConfig(base_delay=1.0, exponential_backoff=False)
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 1.0
        assert config.get_delay(3) == 1.0
        
    def test_get_delay_with_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, max_delay=4.0, exponential_backoff=True)
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0  # Capped at max_delay
        assert config.get_delay(4) == 4.0  # Capped at max_delay

@pytest.mark.asyncio
class TestWithRetries:
    """Tests for with_retries decorator."""
    
    async def test_successful_execution(self, retry_config):
        """Test successful function execution without retries."""
        mock_func = AsyncMock(return_value="success")
        decorated = with_retries(retry_config)(mock_func)
        
        result = await decorated()
        
        assert result == "success"
        mock_func.assert_called_once()
        
    async def test_retry_on_failure(self, retry_config):
        """Test retrying on failure."""
        mock_func = AsyncMock(
            side_effect=[ValueError("fail"), ValueError("fail"), "success"]
        )
        decorated = with_retries(retry_config)(mock_func)
        
        result = await decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3
        
    async def test_max_retries_exceeded(self, retry_config):
        """Test maximum retries exceeded."""
        mock_func = AsyncMock(side_effect=ValueError("fail"))
        decorated = with_retries(retry_config)(mock_func)
        
        with pytest.raises(ValueError, match="fail"):
            await decorated()
            
        assert mock_func.call_count == retry_config.max_attempts

class TestWithSyncRetries:
    """Tests for with_sync_retries decorator."""
    
    def test_successful_execution(self, retry_config):
        """Test successful synchronous function execution."""
        mock_func = Mock(return_value="success")
        decorated = with_sync_retries(retry_config)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        mock_func.assert_called_once()
        
    def test_retry_on_failure(self, retry_config):
        """Test retrying synchronous function on failure."""
        mock_func = Mock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
        decorated = with_sync_retries(retry_config)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3

@pytest.mark.asyncio
class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    async def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state."""
        assert circuit_breaker.state == "CLOSED"
        assert circuit_breaker.can_execute()
        
    async def test_open_on_failures(self, circuit_breaker):
        """Test circuit opens after failures."""
        for _ in range(circuit_breaker.failure_threshold):
            circuit_breaker.record_failure()
            
        assert circuit_breaker.state == "OPEN"
        assert not circuit_breaker.can_execute()
        
    async def test_half_open_after_timeout(self, circuit_breaker):
        """Test transition to half-open state."""
        # Open the circuit
        for _ in range(circuit_breaker.failure_threshold):
            circuit_breaker.record_failure()
            
        assert circuit_breaker.state == "OPEN"
        
        # Move time forward
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.return_value = (
                circuit_breaker.last_failure_time + circuit_breaker.half_open_timeout + 0.1
            )
            assert circuit_breaker.can_execute()
            assert circuit_breaker.state == "HALF_OPEN"
            
    async def test_close_on_success(self, circuit_breaker):
        """Test circuit closes after success."""
        # Start in half-open state
        circuit_breaker.state = "HALF_OPEN"
        
        circuit_breaker.record_success()
        
        assert circuit_breaker.state == "CLOSED"
        assert circuit_breaker.failures == 0
        assert circuit_breaker.can_execute()
        
    async def test_with_circuit_breaker_decorator(self, circuit_breaker):
        """Test circuit breaker decorator."""
        mock_func = AsyncMock(side_effect=[
            ValueError("fail"),  # First call fails
            ValueError("fail"),  # Second call fails
            ValueError("fail"),  # Third call fails - opens circuit
            "success"           # Fourth call shouldn't execute
        ])
        
        decorated = with_circuit_breaker(circuit_breaker)(mock_func)
        
        # First three calls fail but are allowed
        for _ in range(3):
            with pytest.raises(ValueError):
                await decorated()
                
        # Circuit should now be open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await decorated()
            
        assert mock_func.call_count == 3  # Fourth call was prevented
        
    async def test_reset_after_timeout(self, circuit_breaker):
        """Test failure count reset after timeout."""
        # Record some failures
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        
        initial_failures = circuit_breaker.failures
        
        # Move time forward past reset timeout
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.time.return_value = (
                circuit_breaker.last_failure_time + circuit_breaker.reset_timeout + 0.1
            )
            circuit_breaker.record_failure()
            
            # Failure count should have reset
            assert circuit_breaker.failures == 1
            assert circuit_breaker.failures < initial_failures

@pytest.mark.asyncio
class TestRetryEdgeCases:
    """Tests for retry edge cases and advanced features."""
    
    async def test_custom_exceptions(self):
        """Test retrying only on specified exceptions."""
        config = RetryConfig(max_attempts=3, exceptions=(ValueError,))
        mock_func = AsyncMock(side_effect=[
            ValueError("retry"),     # Should retry
            KeyError("no retry"),    # Should not retry
            "success"
        ])
        
        decorated = with_retries(config)(mock_func)
        
        with pytest.raises(KeyError):
            await decorated()
            
        assert mock_func.call_count == 2  # Only retried on ValueError
        
    async def test_retry_with_jitter(self):
        """Test retry delays with jitter."""
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=0.3,
            jitter=0.05
        )
        
        delays = []
        mock_func = AsyncMock(side_effect=[ValueError, ValueError, "success"])
        
        async def mock_sleep(delay):
            delays.append(delay)
            
        with patch('asyncio.sleep', new=mock_sleep):
            decorated = with_retries(config)(mock_func)
            await decorated()
            
        # Check that delays are different due to jitter
        assert len(delays) == 2  # Two retries
        assert len(set(delays)) == 2  # Delays should be different
        assert all(0.05 <= d <= 0.35 for d in delays)  # Within jitter range
