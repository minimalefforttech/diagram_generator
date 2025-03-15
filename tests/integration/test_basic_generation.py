"""Integration tests for basic diagram generation."""

import pytest
from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.configs import DiagramGenerationOptions

pytestmark = pytest.mark.asyncio

async def test_mermaid_sequence_generation(agent_config):
    """Test generating a Mermaid sequence diagram."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    result = await agent.generate_diagram(
        description="Create a sequence diagram showing login flow between user, frontend, and backend",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Check for expected elements
    assert "sequenceDiagram" in result.code
    assert "participant" in result.code
    assert "->" in result.code or "->>" in result.code
    
    # Verify response metadata
    assert result.iterations > 0
    assert result.diagram_type == "mermaid"
    assert result.diagram_id is not None

async def test_mermaid_flowchart_generation(agent_config):
    """Test generating a Mermaid flowchart."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    result = await agent.generate_diagram(
        description="Create a flowchart showing the user registration process",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Check for flowchart elements
    assert any(keyword in result.code for keyword in ["flowchart", "graph"])
    assert "[" in result.code and "]" in result.code  # Node definitions
    assert "-->" in result.code  # Connections
    
    # Verify diagram type detection worked
    assert "flowchart" in result.code.lower() or "graph" in result.code.lower()

async def test_plantuml_generation(agent_config):
    """Test generating a PlantUML diagram."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    result = await agent.generate_diagram(
        description="Create a component diagram showing the system architecture",
        diagram_type="plantuml",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Basic validity checks
    assert result.code is not None
    assert len(result.code) > 0
    
    # Check for PlantUML syntax
    assert "@startuml" in result.code
    assert "@enduml" in result.code
    assert "[" in result.code and "]" in result.code  # Component definitions
    
    # Verify it's describing architecture
    lower_code = result.code.lower()
    assert any(word in lower_code for word in ["component", "package", "node"])

async def test_multiple_diagrams_unique(agent_config):
    """Test that multiple diagram generations produce unique results."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    description = "Create a sequence diagram for user login"
    
    # Generate two diagrams with the same description
    result1 = await agent.generate_diagram(
        description=description,
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    result2 = await agent.generate_diagram(
        description=description,
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify they have unique IDs
    assert result1.diagram_id != result2.diagram_id
    
    # Both should be valid sequence diagrams
    assert "sequenceDiagram" in result1.code
    assert "sequenceDiagram" in result2.code
    
    # They should be different (LLMs should produce variations)
    assert result1.code != result2.code

async def test_error_cases(agent_config):
    """Test handling of potential error cases."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Invalid diagram type
    with pytest.raises(ValueError):
        await agent.generate_diagram(
            description="Create a diagram",
            diagram_type="invalid",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Very short description should still work
    result = await agent.generate_diagram(
        description="diagram",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    assert result.code is not None  # Should still produce something
    
    # Very long description should still work
    long_desc = "Create a diagram " * 100
    result = await agent.generate_diagram(
        description=long_desc,
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    assert result.code is not None  # Should handle long input
