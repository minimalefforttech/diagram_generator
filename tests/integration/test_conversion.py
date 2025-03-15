"""Integration tests for diagram type and format conversions."""

import pytest
from diagram_generator.backend.agents.diagram_agent import DiagramAgent
from diagram_generator.backend.models.configs import DiagramGenerationOptions

pytestmark = pytest.mark.asyncio

async def test_mermaid_to_plantuml(agent_config):
    """Test converting Mermaid to PlantUML."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate initial Mermaid diagram
    initial_result = await agent.generate_diagram(
        description="Create a sequence diagram showing login flow",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify initial diagram
    assert initial_result.code is not None
    assert "sequenceDiagram" in initial_result.code
    
    # Convert to PlantUML
    converted_result = await agent.convert_diagram(
        code=initial_result.code,
        source_type="mermaid",
        target_type="plantuml",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify PlantUML syntax
    assert "@startuml" in converted_result.code
    assert "@enduml" in converted_result.code
    
    # Basic content checks
    lower_code = converted_result.code.lower()
    assert "participant" in lower_code
    assert "->" in lower_code

async def test_plantuml_to_mermaid(agent_config):
    """Test converting PlantUML to Mermaid."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate initial PlantUML diagram
    initial_result = await agent.generate_diagram(
        description="Create a class diagram showing basic user management",
        diagram_type="plantuml",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify initial diagram
    assert initial_result.code is not None
    assert "@startuml" in initial_result.code
    
    # Convert to Mermaid
    converted_result = await agent.convert_diagram(
        code=initial_result.code,
        source_type="plantuml",
        target_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify Mermaid syntax
    assert "classDiagram" in converted_result.code
    
    # Should not contain PlantUML syntax
    assert "@startuml" not in converted_result.code
    assert "@enduml" not in converted_result.code

async def test_diagram_type_conversion(agent_config):
    """Test converting between diagram types within same syntax."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate sequence diagram
    sequence_result = await agent.generate_diagram(
        description="Create a sequence diagram for user authentication",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Convert to class diagram
    converted_result = await agent.convert_diagram(
        code=sequence_result.code,
        source_type="mermaid-sequence",
        target_type="mermaid-class",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Verify conversion
    assert "classDiagram" in converted_result.code
    assert "class" in converted_result.code.lower()
    
    # Should contain similar entities
    assert any(word in converted_result.code.lower() 
              for word in ["user", "auth", "authenticate"])

async def test_complex_diagram_conversion(agent_config):
    """Test converting complex diagrams with nested elements."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Generate complex Mermaid flowchart
    initial_result = await agent.generate_diagram(
        description="""Create a flowchart showing a complex user registration process 
        with email verification, input validation, and error handling""",
        diagram_type="mermaid",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Convert to PlantUML
    converted_result = await agent.convert_diagram(
        code=initial_result.code,
        source_type="mermaid",
        target_type="plantuml",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Basic syntax checks
    assert "@startuml" in converted_result.code
    assert "@enduml" in converted_result.code
    
    # Content should be preserved
    lower_code = converted_result.code.lower()
    assert "email" in lower_code
    assert "valid" in lower_code
    assert "error" in lower_code

async def test_conversion_with_rag(agent_config, test_code_dir):
    """Test conversion with RAG context."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Configure RAG
    options = DiagramGenerationOptions(
        agent=agent_config,
        rag=RAGConfig(
            enabled=True,
            api_doc_dir=str(test_code_dir),
            similarity_threshold=0.7
        )
    )
    
    # Generate initial Mermaid class diagram
    initial_result = await agent.generate_diagram(
        description="Create a class diagram for the authentication system",
        diagram_type="mermaid",
        options=options
    )
    
    # Convert to PlantUML
    converted_result = await agent.convert_diagram(
        code=initial_result.code,
        source_type="mermaid",
        target_type="plantuml",
        options=options
    )
    
    # Verify code entities are preserved
    assert "User" in converted_result.code
    assert "AuthService" in converted_result.code
    assert "validateUser" in converted_result.code.lower()

async def test_conversion_error_handling(agent_config):
    """Test error handling in conversion process."""
    agent = DiagramAgent(default_model="llama3.1:8b")
    
    # Test with empty code
    with pytest.raises(ValueError):
        await agent.convert_diagram(
            code="",
            source_type="mermaid",
            target_type="plantuml",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Test with invalid source type
    with pytest.raises(ValueError):
        await agent.convert_diagram(
            code="some diagram code",
            source_type="invalid",
            target_type="plantuml",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Test with invalid target type
    with pytest.raises(ValueError):
        await agent.convert_diagram(
            code="some diagram code",
            source_type="mermaid",
            target_type="invalid",
            options=DiagramGenerationOptions(agent=agent_config)
        )
    
    # Test with malformed diagram code
    result = await agent.convert_diagram(
        code="malformed diagram code",
        source_type="mermaid",
        target_type="plantuml",
        options=DiagramGenerationOptions(agent=agent_config)
    )
    
    # Should still produce valid PlantUML
    assert result.code is not None
    assert "@startuml" in result.code
    assert "@enduml" in result.code
