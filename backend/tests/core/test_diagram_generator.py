"""Tests for diagram generation and validation."""

import json
from unittest.mock import Mock, patch

import pytest

from backend.core.diagram_generator import DiagramGenerator
from backend.services.ollama import OllamaService

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    return Mock(spec=OllamaService)

@pytest.fixture
def diagram_generator(mock_llm_service):
    """Create a DiagramGenerator instance with mock LLM service."""
    return DiagramGenerator(mock_llm_service)

@pytest.mark.asyncio
async def test_generate_diagram_success(diagram_generator, mock_llm_service):
    """Test successful diagram generation."""
    test_mermaid = """
    graph TD
        A[Start] --> B[Process]
        B --> C[End]
    """
    
    # Mock responses
    mock_llm_service.generate_completion.side_effect = [
        {"response": test_mermaid},  # For generation
        {"response": json.dumps({    # For validation
            "valid": True,
            "errors": [],
            "suggestions": []
        })}
    ]
    
    # Mock validation result
    mock_llm_service.validate_response.return_value = {
        "valid": True,
        "errors": [],
        "suggestions": []
    }
    
    code, notes = await diagram_generator.generate_diagram(
        "Create a simple flowchart with three nodes"
    )
    
    assert code == test_mermaid
    assert not notes
    assert mock_llm_service.generate_completion.call_count == 2

@pytest.mark.asyncio
async def test_generate_diagram_with_validation_errors(diagram_generator, mock_llm_service):
    """Test diagram generation with validation errors."""
    invalid_mermaid = "graph TD A-->B[Invalid"
    
    # Mock responses
    mock_llm_service.generate_completion.side_effect = [
        {"response": invalid_mermaid},  # For generation
        {"response": json.dumps({       # For validation
            "valid": False,
            "errors": ["Missing closing bracket"],
            "suggestions": ["Add closing bracket after B"]
        })}
    ]
    
    # Mock validation result
    mock_llm_service.validate_response.return_value = {
        "valid": False,
        "errors": ["Missing closing bracket"],
        "suggestions": ["Add closing bracket after B"]
    }
    
    code, notes = await diagram_generator.generate_diagram(
        "Create a simple flowchart"
    )
    
    assert code == invalid_mermaid
    assert len(notes) == 1
    assert "Missing closing bracket" in notes[0]

@pytest.mark.asyncio
async def test_validate_diagram_valid(diagram_generator, mock_llm_service):
    """Test diagram validation with valid input."""
    valid_mermaid = """
    graph TD
        A[Start] --> B[End]
    """
    
    validation_result = {
        "valid": True,
        "errors": [],
        "suggestions": ["Consider adding more detail"]
    }
    
    mock_llm_service.generate_completion.return_value = {
        "response": json.dumps(validation_result)
    }
    mock_llm_service.validate_response.return_value = validation_result
    
    result = await diagram_generator.validate_diagram(valid_mermaid)
    
    assert result["valid"]
    assert not result["errors"]
    assert len(result["suggestions"]) == 1

@pytest.mark.asyncio
async def test_validate_diagram_invalid(diagram_generator, mock_llm_service):
    """Test diagram validation with invalid input."""
    invalid_mermaid = "graph TD A-->B[Missing bracket"
    
    validation_result = {
        "valid": False,
        "errors": ["Syntax error: Missing closing bracket"],
        "suggestions": ["Add closing bracket"]
    }
    
    mock_llm_service.generate_completion.return_value = {
        "response": json.dumps(validation_result)
    }
    mock_llm_service.validate_response.return_value = validation_result
    
    result = await diagram_generator.validate_diagram(invalid_mermaid)
    
    assert not result["valid"]
    assert len(result["errors"]) == 1
    assert "Missing closing bracket" in result["errors"][0]

@pytest.mark.asyncio
async def test_convert_diagram_success(diagram_generator, mock_llm_service):
    """Test successful diagram conversion."""
    mermaid_diagram = """
    graph TD
        A[Start] --> B[End]
    """
    
    plantuml_diagram = """
    @startuml
    [Start] --> [End]
    @enduml
    """
    
    # Mock conversion response
    mock_llm_service.generate_completion.side_effect = [
        {"response": plantuml_diagram},  # For conversion
        {"response": json.dumps({        # For validation
            "valid": True,
            "errors": [],
            "suggestions": []
        })}
    ]
    
    # Mock validation result
    mock_llm_service.validate_response.return_value = {
        "valid": True,
        "errors": [],
        "suggestions": []
    }
    
    code, notes = await diagram_generator.convert_diagram(
        mermaid_diagram,
        "mermaid",
        "plantuml"
    )
    
    assert code == plantuml_diagram
    assert not notes
    assert mock_llm_service.generate_completion.call_count == 2

@pytest.mark.asyncio
async def test_convert_diagram_with_validation_error(diagram_generator, mock_llm_service):
    """Test diagram conversion with validation errors."""
    mermaid_diagram = """
    graph TD
        A[Start] --> B[End]
    """
    
    invalid_plantuml = "@startuml\n[Start] ->"
    
    # Mock responses
    mock_llm_service.generate_completion.side_effect = [
        {"response": invalid_plantuml},  # For conversion
        {"response": json.dumps({        # For validation
            "valid": False,
            "errors": ["Incomplete arrow syntax"],
            "suggestions": ["Complete the arrow connection"]
        })}
    ]
    
    # Mock validation result
    mock_llm_service.validate_response.return_value = {
        "valid": False,
        "errors": ["Incomplete arrow syntax"],
        "suggestions": ["Complete the arrow connection"]
    }
    
    code, notes = await diagram_generator.convert_diagram(
        mermaid_diagram,
        "mermaid",
        "plantuml"
    )
    
    assert code == invalid_plantuml
    assert len(notes) == 1
    assert "Incomplete arrow syntax" in notes[0]
