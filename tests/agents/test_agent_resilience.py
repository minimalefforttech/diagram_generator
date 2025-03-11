"""Tests for diagram agent resilience features (retry, circuit breaker, caching)."""

import json
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions
from diagram_generator.backend.utils.caching import CacheEntry
from diagram_generator.backend.utils.retry import CircuitBreaker
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama


@pytest.fixture
def agent():
    """Create a DiagramAgent instance with test configuration."""
    agent = DiagramAgent(
        cache_dir=".cache/test_diagrams",
        cache_ttl=60,  # Short TTL for testing
    )

    # Clear cache to ensure tests start fresh
    agent.cache.clear()

    return agent


@pytest.mark.asyncio
class TestAgentResilience:
    """Tests for DiagramAgent resilience features."""

    async def test_cache_hit(self, agent):
        """Test using cached diagram."""
        description = "test diagram"
        diagram_type = "mermaid"
        mock_code = "graph TD;\nA-->B;"

        # Pre-cache the diagram
        agent.cache.set(
            description=description,
            diagram_type=diagram_type,
            value=mock_code
        )

        mock_llm = AsyncMock()

        with patch("langchain_ollama.ChatOllama") as mock_chat_cls:
            mock_chat_cls.return_value = mock_llm

            result, notes = await agent.generate_diagram(description, diagram_type)

            assert result == mock_code
            assert "Using cached diagram" in notes
            mock_llm.ainvoke.assert_not_called()
