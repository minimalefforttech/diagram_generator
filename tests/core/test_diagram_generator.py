"""Tests for diagram generation and validation."""

import pytest
from unittest.mock import Mock, patch

from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.models.configs import DiagramGenerationOptions
from diagram_generator.backend.services.ollama import OllamaService, OllamaResponse
from diagram_generator.backend.utils.rag import RAGProvider

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

@pytest.mark.asyncio
async def test_convert_mermaid_to_plantuml(diagram_generator, mock_llm_service):
    """Test conversion from Mermaid to PlantUML."""
    mermaid_code = """
    sequenceDiagram
        Alice->>John: Hello John
        John-->>Alice: Hello Alice
    """
    
    expected_plantuml = """
    @startuml
    Alice -> John: Hello John
    John --> Alice: Hello Alice
    @enduml
    """
    
    mock_llm_service.generate_completion.return_value = {
        "response": expected_plantuml
    }
    
    converted, notes = await diagram_generator.convert_diagram(
        mermaid_code,
        source_type="mermaid",
        target_type="plantuml"
    )
    
    assert "@startuml" in converted
    assert "@enduml" in converted
    assert "Alice" in converted and "John" in converted
    assert not notes  # No warnings expected

@pytest.mark.asyncio
async def test_convert_plantuml_to_mermaid(diagram_generator, mock_llm_service):
    """Test conversion from PlantUML to Mermaid."""
    plantuml_code = """
    @startuml
    class Car {
        -brand: String
        +start(): void
        +stop(): void
    }
    @enduml
    """
    
    expected_mermaid = """
    classDiagram
        class Car {
            -brand: String
            +start() void
            +stop() void
        }
    """
    
    mock_llm_service.generate_completion.return_value = {
        "response": expected_mermaid
    }
    
    converted, notes = await diagram_generator.convert_diagram(
        plantuml_code,
        source_type="plantuml",
        target_type="mermaid"
    )
    
    assert "classDiagram" in converted
    assert "class Car" in converted
    assert not notes  # No warnings expected

@pytest.mark.asyncio
async def test_convert_plantuml_subtypes(diagram_generator, mock_llm_service):
    """Test conversion between different PlantUML diagram subtypes."""
    class_diagram = """
    @startuml
    class User {
        +username: String
    }
    @enduml
    """
    
    expected_sequence = """
    @startuml
    actor User
    User -> System: login(username)
    @enduml
    """
    
    mock_llm_service.generate_completion.return_value = {
        "response": expected_sequence
    }
    
    converted, notes = await diagram_generator.convert_diagram(
        class_diagram,
        source_type="plantuml_class",
        target_type="plantuml_sequence"
    )
    
    assert "@startuml" in converted
    assert "actor User" in converted
    assert not notes  # No warnings expected

@pytest.mark.asyncio
async def test_convert_with_invalid_types(diagram_generator, mock_llm_service):
    """Test conversion with invalid diagram types."""
    mermaid_code = "graph TD\nA-->B"
    
    with pytest.raises(ValueError, match="Invalid source type"):
        await diagram_generator.convert_diagram(
            mermaid_code,
            source_type="invalid",
            target_type="plantuml"
        )
    
    with pytest.raises(ValueError, match="Invalid target type"):
        await diagram_generator.convert_diagram(
            mermaid_code,
            source_type="mermaid",
            target_type="invalid"
        )

@pytest.mark.asyncio
async def test_convert_with_validation_error(diagram_generator, mock_llm_service):
    """Test conversion that results in invalid target syntax."""
    mermaid_code = "graph TD\nA-->B"
    
    # Mock an invalid PlantUML response
    mock_llm_service.generate_completion.return_value = {
        "response": "invalid plantuml code"
    }
    
    converted, notes = await diagram_generator.convert_diagram(
        mermaid_code,
        source_type="mermaid",
        target_type="plantuml"
    )
    
    assert converted  # Should still return the conversion
    assert len(notes) > 0  # Should have validation warnings
