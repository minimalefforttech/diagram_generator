"""Tests for storage integration in DiagramAgent."""

import json
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.ollama import OllamaAPI, OllamaResponse
from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions
from diagram_generator.backend.storage.database import Storage, DiagramRecord, ConversationRecord
from diagram_generator.backend.utils.rag import RAGProvider

@pytest.fixture
def mock_storage():
    """Create a mock storage instance."""
    storage = MagicMock(spec=Storage)
    return storage

@pytest.fixture
def mock_ollama_api():
    """Create a mock OllamaAPI instance."""
    mock = MagicMock(spec=OllamaAPI)
    mock.generate = AsyncMock()
    return mock

@pytest.fixture
def agent(mock_storage, mock_ollama_api):
    """Create a DiagramAgent instance with mock storage."""
    with patch('diagram_generator.backend.agents.diagram_agent.OllamaAPI', return_value=mock_ollama_api):
        agent = DiagramAgent(
            storage=mock_storage,
            cache_ttl=0  # Disable caching for these tests
        )
        return agent

@pytest.mark.asyncio
class TestDiagramGeneration:
    """Tests for diagram generation with storage."""
    
    async def test_stores_generated_diagram(self, agent, mock_storage, mock_ollama_api):
        """Test storing a generated diagram."""
        description = "Test diagram"
        mock_code = "graph TD;\nA-->B;"
        
        # Mock Ollama response
        mock_ollama_api.generate.return_value = OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response=mock_code,
            done=True
        )
        
        result, _ = await agent.generate_diagram(
            description,
            "mermaid",
            DiagramGenerationOptions(agent=AgentConfig(enabled=False))
        )
        
        assert result == mock_code
        
        # Verify diagram was stored
        assert mock_storage.save_diagram.called
        saved_diagram = mock_storage.save_diagram.call_args[0][0]
        assert isinstance(saved_diagram, DiagramRecord)
        assert saved_diagram.description == description
        assert saved_diagram.diagram_type == "mermaid"
        assert saved_diagram.code == mock_code
        
        # Verify conversation was stored
        assert mock_storage.save_conversation.called
        saved_conv = mock_storage.save_conversation.call_args[0][0]
        assert isinstance(saved_conv, ConversationRecord)
        assert saved_conv.diagram_id == saved_diagram.id
        assert len(saved_conv.messages) == 2  # User request + Assistant response
        
    async def test_stores_validation_and_fixes(self, agent, mock_storage, mock_ollama_api):
        """Test storing validation and fix attempts."""
        # Mock diagram validation to fail once then succeed
        validation_responses = [
            json.dumps({
                "valid": False,
                "errors": ["Invalid arrow syntax"],
                "suggestions": ["Use --> instead of ->"]
            }),
            json.dumps({
                "valid": True,
                "errors": [],
                "suggestions": []
            })
        ]
        
        mock_codes = [
            "graph TD;\nA->B;",  # Initial (invalid)
            "graph TD;\nA-->B;",  # Fixed
        ]
        
        # Clear cache to ensure we don't get a cached result
        agent.cache.clear()
        
        # Mock Ollama responses
        mock_ollama_api.generate.side_effect = [
            OllamaResponse(model="test-model", created_at="2025-03-11T23:05:39Z", response=mock_codes[0], done=True),
            OllamaResponse(model="test-model", created_at="2025-03-11T23:05:39Z", response=validation_responses[0], done=True),
            OllamaResponse(model="test-model", created_at="2025-03-11T23:05:39Z", response=mock_codes[1], done=True),
            OllamaResponse(model="test-model", created_at="2025-03-11T23:05:39Z", response=validation_responses[1], done=True)
        ]
        
        options = DiagramGenerationOptions(agent=AgentConfig(enabled=True))
        result, notes = await agent.generate_diagram(
            "Test diagram",
            "mermaid",
            options
        )
        
        assert result == mock_codes[1]  # Should be the fixed version
        
        # Verify conversation updates
        assert mock_storage.save_conversation.call_count >= 2  # Initial + at least one update
        final_conv = mock_storage.save_conversation.call_args[0][0]
        assert len(final_conv.messages) >= 3  # At least Request + Initial + Fixed
        
        # Check message types
        messages = final_conv.messages
        assert messages[0].metadata["type"] == "initial_request"
        assert messages[1].metadata["type"] == "generation"
        assert messages[2].metadata["type"] == "fix"
        assert messages[2].metadata["iteration"] == 1
        assert "Invalid arrow syntax" in messages[2].metadata["errors"]
        
    async def test_stores_with_rag_context(self, agent, mock_storage, mock_ollama_api):
        """Test storing diagram with RAG context."""
        mock_rag = MagicMock(spec=RAGProvider)
        mock_rag.get_relevant_context.return_value = "API Context"
        
        mock_ollama_api.generate.return_value = OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response="graph TD;\nA-->B;",
            done=True
        )
        
        options = DiagramGenerationOptions(agent=AgentConfig(enabled=False))
        options.rag.enabled = True
        
        await agent.generate_diagram(
            "Test diagram",
            "mermaid",
            options,
            mock_rag
        )
        
        # Verify RAG context was stored
        saved_conv = mock_storage.save_conversation.call_args[0][0]
        assert "rag_context" in saved_conv.metadata
        assert "API Context" in saved_conv.metadata["rag_context"]
        
    async def test_stores_metadata(self, agent, mock_storage, mock_ollama_api):
        """Test storing diagram and conversation metadata."""
        mock_code = "graph TD;\nA-->B;"
        
        mock_ollama_api.generate.return_value = OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response=mock_code,
            done=True
        )
        
        options = DiagramGenerationOptions()
        options.agent.enabled = True
        options.agent.model_name = "test-model"
        
        await agent.generate_diagram(
            "Test diagram",
            "mermaid",
            options
        )
        
        # Verify diagram metadata
        saved_diagram = mock_storage.save_diagram.call_args[0][0]
        assert saved_diagram.metadata["agent_enabled"] is True
        assert saved_diagram.metadata["model"] == "test-model"
        
        # Verify conversation metadata was timestamped
        saved_conv = mock_storage.save_conversation.call_args[0][0]
        assert isinstance(saved_conv.created_at, datetime)
        assert isinstance(saved_conv.updated_at, datetime)
        
    async def test_stores_failing_attempts(self, agent, mock_storage, mock_ollama_api):
        """Test storing failed generation attempts."""
        mock_ollama_api.generate.side_effect = Exception("Generation failed")
        
        with pytest.raises(Exception):
            await agent.generate_diagram(
                "Test diagram",
                "mermaid"
            )
        
        # Should not have saved anything on failure
        mock_storage.save_diagram.assert_not_called()
        mock_storage.save_conversation.assert_not_called()
