"""Integration tests for RAG functionality."""

import pytest
from pathlib import Path
from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.configs import (
    DiagramGenerationOptions,
    DiagramRAGConfig
)
from diagram_generator.backend.utils.rag import RAGProvider

pytestmark = pytest.mark.asyncio

async def test_rag_with_python_code(agent_config, test_code_dir):
    """Test RAG with Python source code."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Configure RAG
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_code_dir),
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    result = await agent.generate_diagram(
        description="Create a class diagram showing the User class implementation",
        diagram_type="mermaid",
        options=options
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Should detect and include User class from test files
    code_lower = result.code.lower()
    assert "class user" in code_lower
    assert "username" in code_lower
    assert "login" in code_lower
    
    # Verify RAG was used
    assert result.notes is not None
    assert any("context" in note.lower() for note in result.notes)

async def test_rag_with_typescript_code(agent_config, test_code_dir):
    """Test RAG with TypeScript source code."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_code_dir),
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    result = await agent.generate_diagram(
        description="Create a sequence diagram showing the authentication flow",
        diagram_type="mermaid",
        options=options
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Should include AuthService from test files
    code_lower = result.code.lower()
    assert "authservice" in code_lower
    assert any(method in code_lower for method in ["validateuser", "validate_user", "validate user"])
    
    # Sequence diagram elements
    assert any(decl in code_lower for decl in ["sequencediagram", "graph td"])
    assert "->" in code_lower or "->>" in code_lower

async def test_rag_combined_sources(agent_config, test_code_dir):
    """Test RAG with multiple file types."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_code_dir),
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    result = await agent.generate_diagram(
        description="Create a component diagram showing the entire authentication system",
        diagram_type="mermaid",
        options=options
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Should include components from both files
    code_lower = result.code.lower()
    assert "user" in code_lower
    assert "auth" in code_lower
    assert any(word in code_lower for word in ["component", "service", "class"])

async def test_rag_with_empty_directory(agent_config, tmp_path):
    """Test RAG behavior with empty directory."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(empty_dir),
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    # Should still generate diagram without RAG context
    result = await agent.generate_diagram(
        description="Create a sequence diagram for login",
        diagram_type="mermaid",
        options=options
    )
    
    assert result.code is not None
    assert len(result.code) > 0
    code_lower = result.code.lower()
    # Accept either sequence diagram or graph declarations
    assert any(decl in code_lower for decl in ["sequencediagram", "graph td"])
    assert "->" in code_lower or "->>" in code_lower

async def test_rag_with_invalid_files(agent_config, tmp_path):
    """Test RAG handling of invalid file types."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Create test files
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Create some invalid files
    (test_dir / "test.txt").write_text("This is a text file")
    (test_dir / "test.json").write_text('{"key": "value"}')
    (test_dir / "test.csv").write_text("column1,column2\nvalue1,value2")
    
    rag_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_dir),
        similarity_threshold=0.7
    )
    
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=rag_config
    )
    
    # Should still work without valid code files
    result = await agent.generate_diagram(
        description="Create a class diagram",
        diagram_type="mermaid",
        options=options
    )
    
    assert result.code is not None
    assert len(result.code) > 0
    code_lower = result.code.lower()
    assert "class" in code_lower

async def test_rag_similarity_threshold(agent_config, test_code_dir):
    """Test different similarity thresholds."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    description = "Create a class diagram for the authentication system"
    
    # Test with high threshold
    high_threshold_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_code_dir),
        similarity_threshold=0.9  # Very strict
    )
    
    high_result = await agent.generate_diagram(
        description=description,
        diagram_type="mermaid",
        options=DiagramGenerationOptions(
            agent=agent_config,
            rag=high_threshold_config
        )
    )
    
    # Test with low threshold
    low_threshold_config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=str(test_code_dir),
        similarity_threshold=0.3  # Very lenient
    )
    
    low_result = await agent.generate_diagram(
        description=description,
        diagram_type="mermaid",
        options=DiagramGenerationOptions(
            agent=agent_config,
            rag=low_threshold_config
        )
    )
    
    # Both should produce valid diagrams
    assert high_result.code is not None
    assert low_result.code is not None
    
    # Low threshold might include more context
    assert len(low_result.notes) >= len(high_result.notes)
