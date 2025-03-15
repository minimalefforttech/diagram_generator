"""Unit tests for utility functions."""

import pytest
import time
from pathlib import Path
import json
from diagram_generator.backend.utils.caching import Cache
from diagram_generator.backend.utils.retry import retry_async
from diagram_generator.backend.utils.diagram_validator import strip_comments

def test_cache_operations():
    """Test cache operations."""
    cache = Cache()
    
    # Test basic set/get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Test expiration
    cache.set("key2", "value2", ttl=1)
    assert cache.get("key2") == "value2"
    time.sleep(1.1)  # Wait for expiration
    assert cache.get("key2") is None
    
    # Test update
    cache.set("key3", "value3")
    assert cache.get("key3") == "value3"
    cache.set("key3", "updated")
    assert cache.get("key3") == "updated"
    
    # Test delete
    cache.set("key4", "value4")
    assert cache.get("key4") == "value4"
    cache.delete("key4")
    assert cache.get("key4") is None
    
    # Test clear
    cache.set("key5", "value5")
    cache.set("key6", "value6")
    cache.clear()
    assert cache.get("key5") is None
    assert cache.get("key6") is None

@pytest.mark.asyncio
async def test_retry_decorator():
    """Test retry decorator for async functions."""
    attempt_count = 0
    
    @retry_async(max_attempts=3, delay=0.1)
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("Test error")
    
    @retry_async(max_attempts=3, delay=0.1)
    async def succeeding_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise ValueError("Test error")
        return "success"
    
    # Test function that always fails
    with pytest.raises(ValueError):
        await failing_function()
    assert attempt_count == 3  # Should have tried 3 times
    
    # Reset counter and test function that succeeds on second try
    attempt_count = 0
    result = await succeeding_function()
    assert result == "success"
    assert attempt_count == 2  # Should have succeeded on second try

def test_strip_comments():
    """Test comment stripping from diagram code."""
    # Test Mermaid comments
    mermaid_code = """
    %% This is a comment
    sequenceDiagram %% Diagram type
        participant A %% Actor A
        participant B %% Actor B
        A->>B: Message %% Send
        B-->>A: Reply %% Receive
    """
    
    clean_mermaid = strip_comments(mermaid_code)
    assert "%%" not in clean_mermaid
    assert "This is a comment" not in clean_mermaid
    assert "sequenceDiagram" in clean_mermaid
    assert "A->>B: Message" in clean_mermaid
    
    # Test PlantUML comments
    plantuml_code = """
    @startuml
    ' This is a comment
    class User {
        ' Properties
        +username: string
        +email: string
        /' Block
           comment '/
        +login(): boolean
    }
    @enduml
    """
    
    clean_plantuml = strip_comments(plantuml_code)
    assert "' This is a comment" not in clean_plantuml
    assert "Properties" not in clean_plantuml
    assert "Block\n           comment" not in clean_plantuml
    assert "@startuml" in clean_plantuml
    assert "class User" in clean_plantuml

def test_cache_with_complex_data():
    """Test cache with complex data structures."""
    cache = Cache()
    
    # Test with dictionary
    data_dict = {
        "name": "test",
        "values": [1, 2, 3],
        "nested": {"key": "value"}
    }
    cache.set("dict_key", data_dict)
    retrieved = cache.get("dict_key")
    assert retrieved == data_dict
    assert retrieved["nested"]["key"] == "value"
    
    # Test with list
    data_list = [1, "two", {"three": 3}, [4, 5, 6]]
    cache.set("list_key", data_list)
    assert cache.get("list_key") == data_list
    
    # Test with None
    cache.set("none_key", None)
    assert cache.get("none_key") is None
    
    # Test with large data
    large_data = {"data": "x" * 1000000}  # 1MB of data
    cache.set("large_key", large_data)
    assert cache.get("large_key") == large_data

def test_cache_concurrent_access():
    """Test cache behavior with concurrent access patterns."""
    cache = Cache()
    
    # Multiple sets for same key
    cache.set("key", "value1")
    cache.set("key", "value2")
    cache.set("key", "value3")
    assert cache.get("key") == "value3"
    
    # Set while getting
    cache.set("test_key", "initial")
    value = cache.get("test_key")
    cache.set("test_key", "updated")
    assert value == "initial"
    assert cache.get("test_key") == "updated"
    
    # Delete while getting
    cache.set("del_key", "value")
    value = cache.get("del_key")
    cache.delete("del_key")
    assert value == "value"
    assert cache.get("del_key") is None

@pytest.mark.asyncio
async def test_retry_with_custom_exceptions():
    """Test retry decorator with specific exceptions."""
    
    @retry_async(max_attempts=3, delay=0.1, exceptions=(ValueError,))
    async def value_error_function():
        raise ValueError("Expected error")
    
    @retry_async(max_attempts=3, delay=0.1, exceptions=(ValueError,))
    async def type_error_function():
        raise TypeError("Unexpected error")
    
    # Should retry on ValueError
    with pytest.raises(ValueError):
        await value_error_function()
    
    # Should not retry on TypeError
    with pytest.raises(TypeError):
        await type_error_function()

def test_strip_comments_edge_cases():
    """Test comment stripping with edge cases."""
    # Empty input
    assert strip_comments("") == ""
    assert strip_comments("   \n  ") == ""
    
    # No comments
    code = "sequenceDiagram\nA->B: Message"
    assert strip_comments(code) == code
    
    # Only comments
    assert strip_comments("%% Comment\n%% Another comment") == ""
    
    # Mixed indentation
    code = """
        %% Comment
    sequenceDiagram
        %% Indented comment
            A->B: Message
    """
    clean = strip_comments(code)
    assert "Comment" not in clean
    assert "sequenceDiagram" in clean
    assert "A->B: Message" in clean
