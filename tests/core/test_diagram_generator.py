"""Tests for diagram generation and validation."""

import json
from unittest.mock import Mock, patch

import pytest

from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.models.configs import DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.services.ollama import OllamaService
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.utils.diagram_validator import ValidationResult

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    mock = Mock(spec=OllamaService)
    mock.base_url = "http://localhost:11434"
    mock.model = "llama3.1:8b"
    return mock

@pytest.fixture
def diagram_generator(mock_llm_service):
    """Create a DiagramGenerator instance with mock LLM service."""
    return DiagramGenerator(mock_llm_service)

async def test_validate_valid_mermaid(diagram_generator):
    """Test validation of valid Mermaid diagram."""
    valid_mermaid = """
    graph TD
        A[Start] --> B[Process]
        B --> C[End]
    """
    
    with patch('diagram_generator.backend.agents.diagram_agent.DiagramAgent.validate_diagram') as mock_agent_validate:
        mock_agent_validate.return_value = {"valid": True, "errors": [], "suggestions": ["Consider adding descriptions"]}
        
        result = await diagram_generator.validate_diagram(valid_mermaid, "mermaid")
        
        assert result["valid"] is True
        assert not result["errors"]
        assert len(result["suggestions"]) == 1

async def test_validate_invalid_mermaid(diagram_generator):
    """Test validation of invalid Mermaid diagram."""
    invalid_mermaid = """
    graph TD
        A[Start --> B[Process  # Missing bracket
        B --> C[End]
    """
    
    result = await diagram_generator.validate_diagram(invalid_mermaid, "mermaid")
    
    assert result["valid"] is False
    assert any("bracket" in error.lower() for error in result["errors"])

async def test_validate_with_agent_failure(diagram_generator):
    """Test validation when agent fails but static validation passes."""
    valid_mermaid = """
    graph TD
        A[Start] --> B[End]
    """
    
    with patch('diagram_generator.backend.agents.diagram_agent.DiagramAgent.validate_diagram') as mock_agent_validate:
        mock_agent_validate.side_effect = Exception("Agent error")
        
        result = await diagram_generator.validate_diagram(valid_mermaid, "mermaid")
        
        # Should fall back to static validator result
        assert result["valid"] is True
        assert not result["errors"]

async def test_validate_plantuml(diagram_generator):
    """Test validation of PlantUML diagram."""
    valid_plantuml = """
    @startuml
    class User {
        +name: String
        +email: String
    }
    @enduml
    """
    
    with patch('diagram_generator.backend.agents.diagram_agent.DiagramAgent.validate_diagram') as mock_agent_validate:
        mock_agent_validate.return_value = {"valid": True, "errors": [], "suggestions": []}
        
        result = await diagram_generator.validate_diagram(valid_plantuml, "plantuml")
        
        assert result["valid"] is True
        assert not result["errors"]

async def test_validate_unknown_type(diagram_generator):
    """Test validation of unknown diagram type."""
    code = "some diagram code"

    result = await diagram_generator.validate_diagram(code, "unknown")

    assert result["valid"] is False
    assert any("invalid diagram type" in error.lower() for error in result["errors"])
    assert "mermaid" in result["suggestions"][0].lower() and "plantuml" in result["suggestions"][0].lower()
