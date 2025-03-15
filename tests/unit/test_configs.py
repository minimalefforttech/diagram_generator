"""Unit tests for configuration models."""

import pytest
from diagram_generator.backend.models.configs import (
    AgentConfig,
    DiagramGenerationOptions,
    DiagramRAGConfig,
    RetrySettings,
    CircuitBreakerSettings
)

def test_agent_config_validation():
    """Test agent configuration validation."""
    # Valid config
    config = AgentConfig(
        enabled=True,
        model_name="llama3.1:8b",
        temperature=0.2,
        max_iterations=3
    )
    assert config.model_name == "llama3.1:8b"
    assert config.temperature == 0.2
    
    # Invalid temperature
    with pytest.raises(ValueError):
        AgentConfig(
            enabled=True,
            model_name="llama3.1:8b",
            temperature=2.0,  # Too high
            max_iterations=3
        )
    
    # Invalid max_iterations
    with pytest.raises(ValueError):
        AgentConfig(
            enabled=True,
            model_name="llama3.1:8b",
            temperature=0.2,
            max_iterations=0  # Must be > 0
        )
    
    # Empty model name is allowed (will use default)
    config = AgentConfig(
        enabled=True,
        model_name=None,
        temperature=0.2,
        max_iterations=3
    )
    assert config.model_name is None

def test_rag_config_validation():
    """Test RAG configuration validation."""
    # Valid config
    config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir="/path/to/docs",
        similarity_threshold=0.7
    )
    assert config.similarity_threshold == 0.7
    
    # Test chunk size validation
    config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir="/path/to/docs",
        chunk_size=1000,
        chunk_overlap=200
    )
    assert config.chunk_size == 1000
    assert config.chunk_overlap == 200
    
    # Invalid chunk overlap
    with pytest.raises(ValueError):
        DiagramRAGConfig(
            enabled=True,
            api_doc_dir="/path/to/docs",
            chunk_size=1000,
            chunk_overlap=1000  # Must be less than chunk_size
        )
    
    # Invalid top_k_results
    with pytest.raises(ValueError):
        DiagramRAGConfig(
            enabled=True,
            api_doc_dir="/path/to/docs",
            top_k_results=0  # Must be positive
        )

def test_retry_settings():
    """Test retry settings validation."""
    # Valid settings
    settings = RetrySettings(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        exponential_backoff=True,
        jitter=0.1
    )
    assert settings.max_attempts == 3
    assert settings.base_delay == 1.0
    
    # Invalid max_attempts
    with pytest.raises(ValueError):
        RetrySettings(max_attempts=0)
    
    # Invalid delays
    with pytest.raises(ValueError):
        RetrySettings(base_delay=-1.0)
    
    with pytest.raises(ValueError):
        RetrySettings(max_delay=0.0)
    
    # Invalid jitter
    with pytest.raises(ValueError):
        RetrySettings(jitter=-0.1)

def test_circuit_breaker_settings():
    """Test circuit breaker settings validation."""
    # Valid settings
    settings = CircuitBreakerSettings(
        enabled=True,
        failure_threshold=5,
        reset_timeout=60.0,
        half_open_timeout=30.0
    )
    assert settings.failure_threshold == 5
    assert settings.reset_timeout == 60.0
    
    # Invalid failure threshold
    with pytest.raises(ValueError):
        CircuitBreakerSettings(failure_threshold=0)
    
    # Invalid timeouts
    with pytest.raises(ValueError):
        CircuitBreakerSettings(reset_timeout=-1.0)
    
    with pytest.raises(ValueError):
        CircuitBreakerSettings(half_open_timeout=0.0)

def test_generation_options():
    """Test generation options composition."""
    # Test with all options enabled
    agent_config = AgentConfig(
        enabled=True,
        model_name="llama3.1:8b",
        temperature=0.2,
        max_iterations=3
    )
    
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir="/path/to/docs",
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    assert options.agent.model_name == "llama3.1:8b"
    assert options.rag.enabled
    assert options.rag.api_doc_dir == "/path/to/docs"
    
    # Test custom parameters
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config,
        custom_params={"key": "value"}
    )
    assert options.custom_params["key"] == "value"

def test_config_defaults():
    """Test configuration default values."""
    # Test RetrySettings defaults
    retry = RetrySettings()
    assert retry.max_attempts == 3
    assert retry.base_delay == 1.0
    assert retry.max_delay == 10.0
    assert retry.exponential_backoff is True
    assert retry.jitter == 0.1
    
    # Test CircuitBreakerSettings defaults
    cb = CircuitBreakerSettings()
    assert cb.enabled is True
    assert cb.failure_threshold == 5
    assert cb.reset_timeout == 60.0
    assert cb.half_open_timeout == 30.0
    
    # Test DiagramRAGConfig defaults
    rag = DiagramRAGConfig()
    assert rag.enabled is False
    assert rag.embedding_model == "nomic-embed-text"
    assert rag.max_documents == 5
    assert rag.similarity_threshold == 0.2
    assert rag.chunk_size == 1000
    assert rag.chunk_overlap == 200

def test_config_copy():
    """Test configuration copying."""
    original = AgentConfig(
        enabled=True,
        model_name="llama3.1:8b",
        temperature=0.2,
        max_iterations=3
    )
    
    # Make a copy
    copy = original.model_copy()
    
    # Verify copy has same values
    assert copy.enabled == original.enabled
    assert copy.model_name == original.model_name
    assert copy.temperature == original.temperature
    assert copy.max_iterations == original.max_iterations
    
    # Verify copy is independent
    copy_dict = copy.model_dump()
    copy_dict["model_name"] = "different_model"
    new_copy = AgentConfig(**copy_dict)
    
    assert new_copy.model_name != original.model_name
    assert original.model_name == "llama3.1:8b"
