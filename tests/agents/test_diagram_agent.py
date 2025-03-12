"""Tests for Diagram Agent."""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.ollama import OllamaAPI, OllamaResponse, ErrorResponse
from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.utils.rag import RAGProvider

@pytest.fixture
def mock_ollama_api():
    """Create a mock OllamaAPI instance."""
    mock = MagicMock(spec=OllamaAPI)
    mock.generate = AsyncMock()
    return mock

@pytest.fixture
def diagram_agent(mock_ollama_api):
    """Create a DiagramAgent instance."""
    with patch('diagram_generator.backend.agents.diagram_agent.OllamaAPI', return_value=mock_ollama_api):
        agent = DiagramAgent(cache_ttl=0)  # Disable caching for tests
        # Clear cache
        agent.cache.clear()
        yield agent

@pytest.fixture
def mock_rag_provider():
    """Create a mock RAG provider."""
    mock = MagicMock(spec=RAGProvider)
    mock.get_relevant_context = MagicMock(return_value="API Documentation Context")
    return mock

@pytest.mark.asyncio
async def test_generate_diagram_basic(diagram_agent, mock_ollama_api):
    """Test basic diagram generation without agent or RAG."""
    # Mock response
    mock_ollama_api.generate.return_value = OllamaResponse(
        model="test-model",
        created_at="2025-03-11T23:05:39Z",
        response="graph TD;\nA[Start] --> B[End];",
        done=True
    )
    
    # Generate diagram
    options = DiagramGenerationOptions(agent=AgentConfig(enabled=False))
    code, notes = await diagram_agent.generate_diagram(
        "Create a simple flowchart",
        "mermaid",
        options
    )
    
    # Verify results
    assert "graph TD" in code
    assert len(notes) == 0 or notes == ["Using cached diagram"]
    
    # Verify correct parameters were passed
    mock_ollama_api.generate.assert_called_once()
    call_args = mock_ollama_api.generate.call_args[1]
    assert "Create a simple flowchart" in call_args["prompt"]
    assert "mermaid" in call_args["prompt"]

@pytest.mark.asyncio
async def test_generate_diagram_with_rag(diagram_agent, mock_ollama_api, mock_rag_provider):
    """Test diagram generation with RAG context."""
    # Mock response
    mock_ollama_api.generate.return_value = OllamaResponse(
        model="test-model",
        created_at="2025-03-11T23:05:39Z",
        response="graph TD;\nA[API] --> B[Database];",
        done=True
    )
    
    # Configure RAG
    rag_config = DiagramRAGConfig(enabled=True, api_doc_dir="/test/docs")
    options = DiagramGenerationOptions(
        agent=AgentConfig(enabled=False),
        rag=rag_config
    )
    
    # Generate diagram with RAG
    code, notes = await diagram_agent.generate_diagram(
        "Create an API diagram",
        "mermaid",
        options,
        mock_rag_provider
    )
    
    # Verify results
    assert "graph TD" in code
    assert len(notes) == 0 or notes == ["Using cached diagram"]
    
    # Verify RAG context was included
    mock_ollama_api.generate.assert_called_once()
    call_args = mock_ollama_api.generate.call_args[1]
    assert "API Documentation Context" in call_args["prompt"]
    mock_rag_provider.get_relevant_context.assert_called_once_with("Create an API diagram")

@pytest.mark.asyncio
async def test_validate_diagram(diagram_agent, mock_ollama_api):
    """Test diagram validation."""
    # Mock validation response
    validation_json = json.dumps({
        "valid": True,
        "errors": [],
        "suggestions": ["Consider adding more detail"]
    })
    mock_ollama_api.generate.return_value = OllamaResponse(
        model="test-model",
        created_at="2025-03-11T23:05:39Z",
        response=validation_json,
        done=True
    )
    
    # Validate diagram
    result = await diagram_agent.validate_diagram(
        "graph TD;\nA[Start] --> B[End];", 
        "mermaid"
    )
    
    # Verify results
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert len(result["suggestions"]) == 1

@pytest.mark.asyncio
async def test_validation_with_error_response(diagram_agent, mock_ollama_api):
    """Test validation handling when API returns an error."""
    # Mock error response
    mock_ollama_api.generate.return_value = ErrorResponse(
        error="API connection failed",
        code=500
    )
    
    # Validate diagram
    result = await diagram_agent.validate_diagram(
        "graph TD;\nA[Start] --> B[End];", 
        "mermaid"
    )
    
    # Verify error handling
    assert result["valid"] is False
    assert len(result["errors"]) == 1
    assert "Validation failed" in result["errors"][0]

@pytest.mark.asyncio
async def test_fix_diagram(diagram_agent, mock_ollama_api):
    """Test fixing diagram with errors."""
    # Mock fix response
    mock_ollama_api.generate.return_value = OllamaResponse(
        model="test-model",
        created_at="2025-03-11T23:05:39Z",
        response="graph TD;\nA[Start] --> B[End];",
        done=True
    )
    
    # Fix diagram
    fixed_code = await diagram_agent.fix_diagram(
        "graph TD;\nA[Start] -> B[End];",  # Invalid arrow syntax
        "mermaid",
        ["Invalid arrow syntax, use --> instead of ->"]
    )
    
    # Verify results
    assert "graph TD" in fixed_code
    assert "-->" in fixed_code

@pytest.mark.asyncio
async def test_fix_diagram_with_error(diagram_agent, mock_ollama_api):
    """Test error handling during diagram fixing."""
    # Mock error response
    mock_ollama_api.generate.return_value = ErrorResponse(
        error="Failed to fix diagram",
        code=500
    )
    
    # Attempt to fix diagram
    with pytest.raises(Exception) as excinfo:
        await diagram_agent.fix_diagram(
            "graph TD;\nA[Start] -> B[End];",
            "mermaid",
            ["Invalid syntax"]
        )
    
    # Verify error handling
    assert "Failed to fix diagram" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_diagram_with_validation_loop(diagram_agent, mock_ollama_api):
    """Test diagram generation with validation and fix loop."""
    # Clear cache to ensure we don't get a cached result
    diagram_agent.cache.clear()
    
    # Mock responses for generation, validation and fix
    mock_ollama_api.generate.side_effect = [
        # Initial generation
        OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response="graph TD;\nA[Start] -> B[End];",
            done=True
        ),
        # First validation - invalid
        OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response=json.dumps({
                "valid": False,
                "errors": ["Invalid arrow syntax, use --> instead of ->"],
                "suggestions": ["Replace -> with -->"]
            }),
            done=True
        ),
        # First fix
        OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response="graph TD;\nA[Start] --> B[End];",
            done=True
        ),
        # Second validation - valid
        OllamaResponse(
            model="test-model",
            created_at="2025-03-11T23:05:39Z",
            response=json.dumps({
                "valid": True,
                "errors": [],
                "suggestions": []
            }),
            done=True
        )
    ]
    
    # Generate diagram with agent enabled
    options = DiagramGenerationOptions(agent=AgentConfig(enabled=True, max_iterations=3))
    code, notes = await diagram_agent.generate_diagram(
        "Create a simple flowchart",
        "mermaid",
        options
    )
    
    # Verify results
    assert "graph TD" in code
    assert "-->" in code
    assert len(notes) > 0
    assert any("Invalid arrow syntax" in note for note in notes)
    assert any("Attempt 1: Applied fixes" in note for note in notes)
    assert any("fixed after" in note for note in notes)
