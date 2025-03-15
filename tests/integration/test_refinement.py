"""Integration tests for diagram generation and updates."""

import pytest
from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.configs import (
    DiagramGenerationOptions
)

pytestmark = pytest.mark.asyncio

async def test_diagram_update_adding_departments(agent_config):
    """Test updating a diagram by adding a department."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate initial VFX department flowchart
    initial_result = await agent.generate_diagram(
        description="Create a flowchart showing VFX department workflow with modeling, animation, and rendering departments",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify initial diagram has core departments
    assert initial_result.code is not None
    initial_code_lower = initial_result.code.lower()
    for dept in ["modeling", "animation", "rendering"]:
        assert dept in initial_code_lower
    
    # Update diagram to add compositing department
    update_result = await agent.update_diagram(
        diagram_code=initial_result.code,
        update_notes="Update diagram to add compositing department between rendering and final output",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify updates
    assert update_result.code is not None
    update_code_lower = update_result.code.lower()
    
    # Check original departments still exist
    for dept in ["modeling", "animation", "rendering"]:
        assert dept in update_code_lower
        
    # Check new department was added
    assert "compositing" in update_code_lower
    
    # Basic structural checks
    assert "graph" in update_code_lower
    assert "-->" in update_result.code  # Verify flow connections
    
    # Verify its not just a completely new diagram (should maintain similar structure)
    assert len(update_result.code) > len(initial_result.code)
    
    # Basic check that compositing is connected after rendering
    rendered_first = update_code_lower.find("rendering")
    compositing_pos = update_code_lower.find("compositing") 
    assert rendered_first < compositing_pos

async def test_diagram_update_removing_departments(agent_config):
    """Test updating a diagram by removing a department."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate initial diagram with multiple departments
    initial_result = await agent.generate_diagram(
        description="Create a VFX workflow with concept, modeling, rigging, animation, lighting, and rendering departments",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify initial diagram has all departments
    assert initial_result.code is not None
    initial_code_lower = initial_result.code.lower()
    initial_depts = ["concept", "modeling", "rigging", "animation", "lighting", "rendering"]
    for dept in initial_depts:
        assert dept in initial_code_lower
        
    # Remove rigging department
    update_result = await agent.update_diagram(
        diagram_code=initial_result.code,
        update_notes="Update diagram to remove the rigging department and connect modeling directly to animation",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify updates
    assert update_result.code is not None
    update_code_lower = update_result.code.lower()
    
    # Check rigging was removed
    assert "rigging" not in update_code_lower
    
    # Check other departments still exist
    remaining_depts = ["concept", "modeling", "animation", "lighting", "rendering"]
    for dept in remaining_depts:
        assert dept in update_code_lower
    
    # Verify structure maintained
    assert "graph" in update_code_lower
    assert "-->" in update_result.code
    
    # Basic check that modeling and animation are still in correct order
    modeling_pos = update_code_lower.find("modeling")
    animation_pos = update_code_lower.find("animation")
    assert modeling_pos < animation_pos

async def test_diagram_update_error_handling(agent_config):
    """Test error handling in diagram update process."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate a diagram to test with
    initial_result = await agent.generate_diagram(
        description="Create a simple VFX workflow",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Try updating with empty code
    with pytest.raises(ValueError):
        await agent.update_diagram(
            diagram_code="",
            update_notes="Add a department",
            diagram_type="mermaid",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Try empty update notes
    with pytest.raises(ValueError):
        await agent.update_diagram(
            diagram_code=initial_result.code,
            update_notes="",
            diagram_type="mermaid",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Try invalid diagram type
    with pytest.raises(ValueError):
        await agent.update_diagram(
            diagram_code=initial_result.code,
            update_notes="Add a department",
            diagram_type="invalid_type",
            options=DiagramGenerationOptions(agent=agent_config)
        )

async def test_diagram_type_preservation(agent_config):
    """Test that diagram type is preserved during updates."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    diagram_types = ["mermaid", "plantuml"]
    
    for diagram_type in diagram_types:
        # Generate initial diagram
        initial_result = await agent.generate_diagram(
            description=f"Create a VFX workflow diagram in {diagram_type}",
            diagram_type=diagram_type,
            options=DiagramGenerationOptions(agent=agent_config)
        )
        
        # Update it
        update_result = await agent.update_diagram(
            diagram_code=initial_result.code,
            update_notes="Add effects department",
            diagram_type=diagram_type,
            options=DiagramGenerationOptions(agent=agent_config)
        )
        
        # Check type-specific syntax is preserved
        code_lower = update_result.code.lower()
        if diagram_type == "plantuml":
            assert "@startuml" in code_lower
            assert "@enduml" in code_lower
        else:  # mermaid
            assert "graph" in code_lower
            assert "-->" in update_result.code
