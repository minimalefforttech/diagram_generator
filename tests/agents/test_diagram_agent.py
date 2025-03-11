"""Tests for Diagram Agent."""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from langchain_ollama import ChatOllama
from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.utils.rag import RAGProvider


@pytest.fixture
def mock_ollama_chat():
    """Create a mock ChatOllama model."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    return mock


@pytest.fixture
def diagram_agent():
    """Create a DiagramAgent instance."""
    with patch('diagram_generator.backend.agents.diagram_agent.ChatOllama') as mock_chat_cls:
        mock_chat = MagicMock()
        mock_chat_cls.return_value = mock_chat
        mock_chat.ainvoke = AsyncMock()
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
async def test_generate_diagram_basic(diagram_agent):
    """Test basic diagram generation without agent or RAG."""
    # Mock responses
    diagram_agent._create_ollama_chat().ainvoke.return_value = {"response": "graph TD;\nA[Start] --> B[End];"}
    
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
    call_args = diagram_agent._create_ollama_chat().ainvoke.call_args[0][0]
    assert "Create a simple flowchart" in call_args[0].content
    assert "mermaid" in call_args[0].content


@pytest.mark.asyncio
async def test_generate_diagram_with_rag(diagram_agent, mock_rag_provider):
    """Test diagram generation with RAG context."""
    # Mock responses
    diagram_agent._create_ollama_chat().ainvoke.return_value = {"response": "graph TD;\nA[API] --> B[Database];"}
    
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
    call_args = diagram_agent._create_ollama_chat().ainvoke.call_args[0][0]
    assert "API Documentation Context" in call_args[0].content
    mock_rag_provider.get_relevant_context.assert_called_once_with("Create an API diagram")


@pytest.mark.asyncio
async def test_validate_diagram(diagram_agent):
    """Test diagram validation."""
    # Mock validation response
    validation_json = json.dumps({
        "valid": True,
        "errors": [],
        "suggestions": ["Consider adding more detail"]
    })
    diagram_agent._create_ollama_chat().ainvoke.return_value = {"response": validation_json}
    
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
async def test_fix_diagram(diagram_agent):
    """Test fixing diagram with errors."""
    # Mock fix response
    diagram_agent._create_ollama_chat().ainvoke.return_value = {"response": "graph TD;\nA[Start] --> B[End];"}
    
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
async def test_generate_diagram_with_validation_loop(diagram_agent):
    """Test diagram generation with validation and fix loop."""
    # Clear cache to ensure we don't get a cached result
    diagram_agent.cache.clear()
    
    # Mock responses for generation, validation and fix
    diagram_agent._create_ollama_chat().ainvoke.side_effect = [
        # Initial generation
        {"response": "graph TD;\nA[Start] -> B[End];"},
        # First validation - invalid
        {"response": json.dumps({
            "valid": False,
            "errors": ["Invalid arrow syntax, use --> instead of ->"],
            "suggestions": ["Replace -> with -->"]
        })},
        # First fix
        {"response": "graph TD;\nA[Start] --> B[End];"},
        # Second validation - valid
        {"response": json.dumps({
            "valid": True,
            "errors": [],
            "suggestions": []
        })}
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
