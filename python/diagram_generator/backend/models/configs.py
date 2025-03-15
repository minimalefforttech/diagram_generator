"""Configuration models for diagram generation agents and RAG."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

class RetrySettings(BaseModel):
    """Configuration for retry behavior."""
    max_attempts: int = Field(3, description="Maximum number of retry attempts")
    base_delay: float = Field(1.0, description="Base delay between retries in seconds")
    max_delay: float = Field(10.0, description="Maximum delay between retries in seconds")
    exponential_backoff: bool = Field(True, description="Whether to use exponential backoff")
    jitter: float = Field(0.1, description="Amount of random jitter to add to delays")

    @field_validator('max_attempts', 'base_delay', 'max_delay', 'jitter')
    @classmethod
    def validate_positive(cls, v: float, info):
        if v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v

class CircuitBreakerSettings(BaseModel):
    """Configuration for circuit breaker."""
    enabled: bool = Field(True, description="Whether circuit breaker is enabled")
    failure_threshold: int = Field(5, description="Number of failures before opening circuit")
    reset_timeout: float = Field(60.0, description="Time before resetting failure count")
    half_open_timeout: float = Field(30.0, description="Time before allowing test request")

    @field_validator('failure_threshold')
    @classmethod
    def validate_failure_threshold(cls, v: int):
        if v < 1:
            raise ValueError("failure_threshold must be at least 1")
        return v

    @field_validator('reset_timeout', 'half_open_timeout')
    @classmethod
    def validate_timeouts(cls, v: float):
        if v <= 0:
            raise ValueError("Timeouts must be positive")
        return v

class DiagramRAGConfig(BaseModel):
    """Configuration for RAG (Retrieval-Augmented Generation) in diagram generation."""
    enabled: bool = Field(False, description="Whether RAG is enabled")
    api_doc_dir: Optional[str] = Field(None, description="Directory with API docs")
    embedding_model: str = Field("nomic-embed-text", description="Embedding model to use")
    max_documents: int = Field(5, description="Maximum documents to retrieve")
    similarity_threshold: float = Field(0.2, description="Minimum similarity score")
    top_k_results: int = Field(5, description="Number of top results to retrieve")
    chunk_size: int = Field(1000, description="Size of text chunks")
    chunk_overlap: int = Field(200, description="Overlap between text chunks")

    @field_validator('top_k_results', 'chunk_size')
    @classmethod
    def validate_positive_int(cls, v: int):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v

    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v: int, info):
        if 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return v

class AgentConfig(BaseModel):
    """Configuration for the diagram agent."""
    
    enabled: bool = Field(True, description="Whether the agent is enabled")
    max_iterations: int = Field(3, description="Maximum iterations for fix attempts")
    temperature: float = Field(0.2, description="Temperature for generation")
    model_name: Optional[str] = Field(None, description="Model to use")
    system_prompt: Optional[str] = Field(None, description="System prompt override")
    retry: RetrySettings = Field(default_factory=RetrySettings)
    circuit_breaker: CircuitBreakerSettings = Field(default_factory=CircuitBreakerSettings)

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float):
        if not 0 <= v <= 1:
            raise ValueError("temperature must be between 0 and 1")
        return v

    @field_validator('max_iterations')
    @classmethod
    def validate_max_iterations(cls, v: int):
        if v < 1:
            raise ValueError("max_iterations must be at least 1")
        return v

class DiagramGenerationOptions(BaseModel):
    """Options for diagram generation."""
    
    agent: AgentConfig = Field(default_factory=AgentConfig)
    rag: DiagramRAGConfig = Field(default_factory=DiagramRAGConfig)
    custom_params: Dict = Field(default_factory=dict, description="Custom parameters for diagram generation")
