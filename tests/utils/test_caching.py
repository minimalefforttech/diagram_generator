"""Tests for caching utilities."""

import json
import os
import time
from pathlib import Path

import pytest

from diagram_generator.backend.utils.caching import CacheEntry, DiagramCache

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary directory for cache files."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)

@pytest.fixture
def diagram_cache(temp_cache_dir):
    """Create a DiagramCache instance."""
    return DiagramCache(cache_dir=temp_cache_dir)

class TestCacheEntry:
    """Tests for CacheEntry class."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        entry = CacheEntry(value="test", timestamp=123.45)
        assert entry.value == "test"
        assert entry.timestamp == 123.45
        assert entry.ttl is None
        assert entry.metadata is None
        
    def test_is_valid_no_ttl(self):
        """Test validity check with no TTL."""
        entry = CacheEntry(value="test", timestamp=0)  # Old timestamp
        assert entry.is_valid()  # Should be valid indefinitely
        
    def test_is_valid_with_ttl(self):
        """Test validity check with TTL."""
        current_time = time.time()
        
        # Valid entry (future expiration)
        entry = CacheEntry(
            value="test",
            timestamp=current_time,
            ttl=3600  # 1 hour
        )
        assert entry.is_valid()
        
        # Expired entry
        entry = CacheEntry(
            value="test",
            timestamp=current_time - 3600,
            ttl=1800  # 30 minutes
        )
        assert not entry.is_valid()
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = CacheEntry(
            value="test",
            timestamp=123.45,
            ttl=3600,
            metadata={"version": "1.0"}
        )
        
        data = entry.to_dict()
        assert data["value"] == "test"
        assert data["timestamp"] == 123.45
        assert data["ttl"] == 3600
        assert data["metadata"] == {"version": "1.0"}
        
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "value": "test",
            "timestamp": 123.45,
            "ttl": 3600,
            "metadata": {"version": "1.0"}
        }
        
        entry = CacheEntry.from_dict(data)
        assert entry.value == "test"
        assert entry.timestamp == 123.45
        assert entry.ttl == 3600
        assert entry.metadata == {"version": "1.0"}

class TestDiagramCache:
    """Tests for DiagramCache class."""
    
    def test_init_creates_directory(self, temp_cache_dir):
        """Test cache directory creation."""
        cache_path = Path(temp_cache_dir) / "subdir"
        DiagramCache(cache_dir=str(cache_path))
        assert cache_path.exists()
        assert cache_path.is_dir()
        
    def test_cache_key_generation(self, diagram_cache):
        """Test cache key generation."""
        # Same inputs should generate same key
        key1 = diagram_cache._get_cache_key(
            "test diagram",
            "mermaid",
            rag_context="context"
        )
        key2 = diagram_cache._get_cache_key(
            "test diagram",
            "mermaid",
            rag_context="context"
        )
        assert key1 == key2
        
        # Different inputs should generate different keys
        key3 = diagram_cache._get_cache_key(
            "different diagram",
            "mermaid",
            rag_context="context"
        )
        assert key1 != key3
        
    def test_set_and_get(self, diagram_cache):
        """Test setting and getting cache entries."""
        diagram_cache.set(
            description="test diagram",
            diagram_type="mermaid",
            value="graph TD;A-->B;",
            metadata={"version": "1.0"}
        )
        
        entry = diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid"
        )
        
        assert entry is not None
        assert entry.value == "graph TD;A-->B;"
        assert entry.metadata == {"version": "1.0"}
        
    def test_get_nonexistent(self, diagram_cache):
        """Test getting nonexistent cache entry."""
        entry = diagram_cache.get(
            description="nonexistent",
            diagram_type="mermaid"
        )
        assert entry is None
        
    def test_get_expired(self, diagram_cache):
        """Test getting expired cache entry."""
        # Add expired entry
        diagram_cache.set(
            description="test diagram",
            diagram_type="mermaid",
            value="graph TD;A-->B;",
            ttl=0  # Immediate expiration
        )
        
        time.sleep(0.1)  # Ensure expiration
        
        entry = diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid"
        )
        assert entry is None
        
    def test_invalidate(self, diagram_cache):
        """Test cache entry invalidation."""
        diagram_cache.set(
            description="test diagram",
            diagram_type="mermaid",
            value="graph TD;A-->B;"
        )
        
        # Verify entry exists
        assert diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid"
        ) is not None
        
        # Invalidate entry
        result = diagram_cache.invalidate(
            description="test diagram",
            diagram_type="mermaid"
        )
        assert result is True
        
        # Verify entry is gone
        assert diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid"
        ) is None
        
    def test_clear(self, diagram_cache):
        """Test clearing all cache entries."""
        # Add multiple entries
        for i in range(3):
            diagram_cache.set(
                description=f"diagram_{i}",
                diagram_type="mermaid",
                value=f"graph_{i}"
            )
            
        # Clear cache
        count = diagram_cache.clear()
        assert count == 3
        
        # Verify all entries are gone
        for i in range(3):
            assert diagram_cache.get(
                description=f"diagram_{i}",
                diagram_type="mermaid"
            ) is None
            
    def test_invalid_cache_file(self, diagram_cache):
        """Test handling of invalid cache file."""
        # Create invalid cache file
        key = diagram_cache._get_cache_key("test", "mermaid")
        cache_path = diagram_cache._get_cache_path(key)
        cache_path.write_text("invalid json")
        
        # Attempt to read cache
        entry = diagram_cache.get("test", "mermaid")
        assert entry is None
        
        # File should be cleaned up
        assert not cache_path.exists()
        
    def test_cache_with_rag_context(self, diagram_cache):
        """Test caching with RAG context."""
        # Same description but different RAG contexts
        diagram_cache.set(
            description="test diagram",
            diagram_type="mermaid",
            value="version 1",
            rag_context="context 1"
        )
        
        diagram_cache.set(
            description="test diagram",
            diagram_type="mermaid",
            value="version 2",
            rag_context="context 2"
        )
        
        # Should get different results
        entry1 = diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid",
            rag_context="context 1"
        )
        entry2 = diagram_cache.get(
            description="test diagram",
            diagram_type="mermaid",
            rag_context="context 2"
        )
        
        assert entry1.value == "version 1"
        assert entry2.value == "version 2"
