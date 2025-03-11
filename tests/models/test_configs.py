"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from diagram_generator.backend.models.configs import (
    AgentConfig,
    CircuitBreakerSettings,
    DiagramGenerationOptions,
    DiagramRAGConfig,
    RetrySettings,
)

def test_retry_settings_defaults():
    """Test RetrySettings with default values."""
    settings = RetrySettings()
    assert settings.max_attempts == 3
    assert settings.base_delay == 1.0
    assert settings.max_delay == 10.0
    assert settings.exponential_backoff is True
    assert settings.jitter == 0.1

def test_retry_settings_custom():
    """Test RetrySettings with custom values."""
    settings = RetrySettings(
        max_attempts=5,
        base_delay=0.5,
        max_delay=5.0,
        exponential_backoff=False,
        jitter=0.2
    )
    assert settings.max_attempts == 5
    assert settings.base_delay == 0.5
    assert settings.max_delay == 5.0
    assert settings.exponential_backoff is False
    assert settings.jitter == 0.2

def test_retry_settings_validation():
    """Test RetrySettings validation."""
    # Test all fields must be positive
    for field in ['max_attempts', 'base_delay', 'max_delay', 'jitter']:
        with pytest.raises(ValidationError, match=f"{field} must be positive"):
            kwargs = {field: 0}
            RetrySettings(**kwargs)
        with pytest.raises(ValidationError, match=f"{field} must be positive"):
            kwargs = {field: -1}
            RetrySettings(**kwargs)

def test_circuit_breaker_settings_defaults():
    """Test CircuitBreakerSettings with default values."""
    settings = CircuitBreakerSettings()
    assert settings.enabled is True
    assert settings.failure_threshold == 5
    assert settings.reset_timeout == 60.0
    assert settings.half_open_timeout == 30.0

def test_circuit_breaker_settings_validation():
    """Test CircuitBreakerSettings validation."""
    # Test failure threshold
    with pytest.raises(ValidationError, match="failure_threshold must be at least 1"):
        CircuitBreakerSettings(failure_threshold=0)
    
    # Test timeouts
    with pytest.raises(ValidationError, match="Timeouts must be positive"):
        CircuitBreakerSettings(reset_timeout=0)
    with pytest.raises(ValidationError, match="Timeouts must be positive"):
        CircuitBreakerSettings(half_open_timeout=0)
        
def test_circuit_breaker_settings_custom():
    """Test CircuitBreakerSettings with custom values."""
    settings = CircuitBreakerSettings(
        enabled=False,
        failure_threshold=3,
        reset_timeout=30.0,
        half_open_timeout=15.0
    )
    assert settings.enabled is False
    assert settings.failure_threshold == 3
    assert settings.reset_timeout == 30.0
    assert settings.half_open_timeout == 15.0

def test_agent_config_with_resilience_settings():
    """Test AgentConfig with retry and circuit breaker settings."""
    config = AgentConfig(
        enabled=True,
        max_iterations=5,
        temperature=0.3,
        model_name="test-model",
        retry=RetrySettings(max_attempts=4),
        circuit_breaker=CircuitBreakerSettings(failure_threshold=3)
    )
    
    assert config.enabled is True
    assert config.max_iterations == 5
    assert config.temperature == 0.3
    assert config.model_name == "test-model"
    assert config.retry.max_attempts == 4
    assert config.circuit_breaker.failure_threshold == 3

def test_agent_config_validation():
    """Test AgentConfig validation."""
    # Test temperature range
    with pytest.raises(ValidationError, match="temperature must be between 0 and 1"):
        AgentConfig(temperature=-0.1)
    with pytest.raises(ValidationError, match="temperature must be between 0 and 1"):
        AgentConfig(temperature=1.1)
    
    # Test max iterations
    with pytest.raises(ValidationError, match="max_iterations must be at least 1"):
        AgentConfig(max_iterations=0)
        
def test_rag_config_validation():
    """Test DiagramRAGConfig validation."""
    # Test positive values
    with pytest.raises(ValidationError, match="Value must be positive"):
        DiagramRAGConfig(top_k_results=0)
    with pytest.raises(ValidationError, match="Value must be positive"):
        DiagramRAGConfig(chunk_size=0)
    
    # Test overlap validation
    with pytest.raises(ValidationError, match="chunk_overlap must be smaller than chunk_size"):
        DiagramRAGConfig(chunk_size=500, chunk_overlap=500)
    with pytest.raises(ValidationError, match="chunk_overlap must be smaller than chunk_size"):
        DiagramRAGConfig(chunk_size=500, chunk_overlap=600)

def test_diagram_generation_options():
    """Test DiagramGenerationOptions composition."""
    options = DiagramGenerationOptions(
        agent=AgentConfig(
            enabled=True,
            max_iterations=5,
            retry=RetrySettings(max_attempts=4),
            circuit_breaker=CircuitBreakerSettings(enabled=False)
        ),
        rag=DiagramRAGConfig(
            enabled=True,
            api_doc_dir="/test/docs"
        ),
        custom_params={"key": "value"}
    )
    
    assert options.agent.enabled is True
    assert options.agent.max_iterations == 5
    assert options.agent.retry.max_attempts == 4
    assert options.agent.circuit_breaker.enabled is False
    assert options.rag.enabled is True
    assert options.rag.api_doc_dir == "/test/docs"
    assert options.custom_params == {"key": "value"}
