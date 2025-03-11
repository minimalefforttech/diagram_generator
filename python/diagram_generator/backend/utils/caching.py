"""Caching utilities for diagram generation."""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with value and metadata."""
    value: T
    timestamp: float
    ttl: Optional[float] = None
    metadata: Dict[str, Any] = None

    def is_valid(self) -> bool:
        """Check if the cache entry is still valid.
        
        Returns:
            bool: Whether the entry is valid
        """
        if self.ttl is None:
            return True
            
        return time.time() < (self.timestamp + self.ttl)

    def to_dict(self) -> Dict:
        """Convert entry to dictionary format.
        
        Returns:
            Dict: Dictionary representation of the entry
        """
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry[T]':
        """Create entry from dictionary format.
        
        Args:
            data: Dictionary data
            
        Returns:
            CacheEntry: New cache entry
        """
        return cls(
            value=data["value"],
            timestamp=data["timestamp"],
            ttl=data.get("ttl"),
            metadata=data.get("metadata", {})
        )

class DiagramCache:
    """Cache for diagram generation results."""
    
    def __init__(self, cache_dir: str = ".cache/diagrams"):
        """Initialize diagram cache.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(
        self,
        description: str,
        diagram_type: str,
        rag_context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate cache key from inputs.
        
        Args:
            description: Diagram description
            diagram_type: Type of diagram
            rag_context: Optional RAG context
            **kwargs: Additional parameters affecting generation
            
        Returns:
            str: Cache key
        """
        # Create deterministic string from inputs
        key_parts = [
            description.strip(),
            diagram_type.lower(),
            rag_context.strip() if rag_context else "",
            json.dumps(kwargs, sort_keys=True)
        ]
        key_string = "|".join(key_parts)
        
        # Generate hash
        return hashlib.sha256(key_string.encode()).hexdigest()
        
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path: Cache file path
        """
        return self.cache_dir / f"{key}.json"
        
    def get(
        self,
        description: str,
        diagram_type: str,
        rag_context: Optional[str] = None,
        **kwargs
    ) -> Optional[CacheEntry[str]]:
        """Get cached diagram if available.
        
        Args:
            description: Diagram description
            diagram_type: Type of diagram
            rag_context: Optional RAG context
            **kwargs: Additional parameters affecting generation
            
        Returns:
            CacheEntry or None: Cached entry if valid, None otherwise
        """
        key = self._get_cache_key(description, diagram_type, rag_context, **kwargs)
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
            
        try:
            data = json.loads(cache_path.read_text())
            entry = CacheEntry.from_dict(data)
            
            if entry.is_valid():
                return entry
                
            # Invalid entry, clean up
            cache_path.unlink(missing_ok=True)
            return None
            
        except (json.JSONDecodeError, KeyError):
            # Invalid cache file, clean up
            cache_path.unlink(missing_ok=True)
            return None
            
    def set(
        self,
        description: str,
        diagram_type: str,
        value: str,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        rag_context: Optional[str] = None,
        **kwargs
    ) -> None:
        """Cache diagram generation result.
        
        Args:
            description: Diagram description
            diagram_type: Type of diagram
            value: Generated diagram code
            ttl: Optional time-to-live in seconds
            metadata: Optional metadata
            rag_context: Optional RAG context
            **kwargs: Additional parameters affecting generation
        """
        key = self._get_cache_key(description, diagram_type, rag_context, **kwargs)
        cache_path = self._get_cache_path(key)
        
        entry = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl=ttl,
            metadata=metadata
        )
        
        cache_path.write_text(json.dumps(entry.to_dict(), indent=2))
        
    def invalidate(
        self,
        description: str,
        diagram_type: str,
        rag_context: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Invalidate cached diagram.
        
        Args:
            description: Diagram description
            diagram_type: Type of diagram
            rag_context: Optional RAG context
            **kwargs: Additional parameters affecting generation
            
        Returns:
            bool: Whether a cache entry was removed
        """
        key = self._get_cache_key(description, diagram_type, rag_context, **kwargs)
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            cache_path.unlink()
            return True
            
        return False
        
    def clear(self) -> int:
        """Clear all cached diagrams.
        
        Returns:
            int: Number of cache entries removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
            
        return count
