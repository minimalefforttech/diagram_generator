"""Tests for diagram validation utilities."""

import pytest
from datetime import datetime

from diagram_generator.backend.utils.diagram_validator import (
    DiagramType,
    DiagramValidator,
    ValidationResult
)

def test_validation_result():
    """Test ValidationResult model."""
    result = ValidationResult(valid=True)
    assert result.valid
    assert not result.errors
    assert not result.suggestions

    result = ValidationResult(
        valid=False,
        errors=["Error 1", "Error 2"],
        suggestions=["Fix 1"]
    )
    assert not result.valid
    assert len(result.errors) == 2
    assert len(result.suggestions) == 1

def test_validation_result_to_dict():
    """Test ValidationResult to_dict conversion."""
    result = ValidationResult(
        valid=False,
        errors=["Error 1", "Error 2"],
        suggestions=["Fix 1"]
    )
    
    dict_result = result.to_dict()
    assert isinstance(dict_result, dict)
    assert dict_result["valid"] is False
    assert len(dict_result["errors"]) == 2
    assert len(dict_result["suggestions"]) == 1

@pytest.mark.parametrize("code,expected_type", [
    ("graph TD\nA-->B", DiagramType.MERMAID),
    ("sequenceDiagram\nAlice->>John: Hi", DiagramType.MERMAID),
    ("classDiagram\nClass01 <|-- Class02", DiagramType.MERMAID),
    ("@startuml\nBob->Alice\n@enduml", DiagramType.PLANTUML),
    ("@startmindmap\n* Root\n@endmindmap", DiagramType.PLANTUML),
    ("invalid diagram", None),
])
def test_detect_type(code: str, expected_type: DiagramType):
    """Test diagram type detection."""
    assert DiagramValidator.detect_type(code) == expected_type

def test_validate_mermaid_valid():
    """Test validation of valid Mermaid diagrams."""
    valid_diagrams = [
        "graph TD\nA[Start] --> B[Process]\nB --> C[End]",
        "sequenceDiagram\nAlice->>John: Hello\nJohn-->>Alice: Hi",
        "flowchart LR\nA-->B"
    ]
    
    for diagram in valid_diagrams:
        result = DiagramValidator.validate_mermaid(diagram)
        assert result.valid, f"Failed to validate: {diagram}"
        assert not result.errors

def test_validate_mermaid_invalid():
    """Test validation of invalid Mermaid diagrams."""
    invalid_diagrams = [
        # Empty diagram
        "",
        # Missing bracket
        "graph TD\nA[Start --> B[Process]\nB --> C[End]",
        # Invalid arrow syntax
        "graph TD\nA[Start] -> B[Process\nB >-> C[End]",
        # Invalid characters
        "graph TD\nA[Start] --> B!!!"
    ]
    
    for diagram in invalid_diagrams:
        result = DiagramValidator.validate_mermaid(diagram)
        assert not result.valid
        assert result.errors

def test_validate_plantuml_valid():
    """Test validation of valid PlantUML diagrams."""
    valid_diagrams = [
        "@startuml\nBob -> Alice : hello\n@enduml",
        "@startuml\nclass User {\n  +name: String\n  +email: String\n}\n@enduml",
        "@startmindmap\n* Root\n** Child 1\n** Child 2\n@endmindmap"
    ]
    
    for diagram in valid_diagrams:
        result = DiagramValidator.validate_plantuml(diagram)
        assert result.valid, f"Failed to validate: {diagram}"
        assert not result.errors

def test_validate_plantuml_invalid():
    """Test validation of invalid PlantUML diagrams."""
    invalid_diagrams = [
        # Empty diagram
        "",
        # Missing @start/@end tags
        "Bob -> Alice : hello",
        # Invalid arrow syntax
        "@startuml\nBob >-> Alice\n@enduml",
        # Mismatched tags
        "@startuml\nBob -> Alice\n@endmindmap",
        # Invalid characters
        "@startuml\nBob -> Alice : hello!!!\n@enduml"
    ]
    
    for diagram in invalid_diagrams:
        result = DiagramValidator.validate_plantuml(diagram)
        assert not result.valid
        assert result.errors

def test_validate_with_explicit_type():
    """Test validation with explicitly specified type."""
    mermaid = "graph TD\nA-->B"
    plantuml = "@startuml\nBob->Alice\n@enduml"
    
    # Test valid type specifications
    result = DiagramValidator.validate(mermaid, DiagramType.MERMAID)
    assert result.valid
    
    result = DiagramValidator.validate(plantuml, DiagramType.PLANTUML)
    assert result.valid
    
    # Test invalid type specifications
    result = DiagramValidator.validate(mermaid, DiagramType.PLANTUML)
    assert not result.valid
    
    result = DiagramValidator.validate(plantuml, DiagramType.MERMAID)
    assert not result.valid

def test_validate_with_auto_detection():
    """Test validation with automatic type detection."""
    mermaid = "graph TD\nA-->B"
    plantuml = "@startuml\nBob->Alice\n@enduml"
    invalid = "not a diagram"
    
    # Test valid diagrams
    result = DiagramValidator.validate(mermaid)
    assert result.valid
    
    result = DiagramValidator.validate(plantuml)
    assert result.valid
    
    # Test invalid diagram
    result = DiagramValidator.validate(invalid)
    assert not result.valid
    assert "Unable to determine diagram type" in result.errors[0]

def test_validate_with_string_type():
    """Test validation with string type specification."""
    mermaid = "graph TD\nA-->B"
    
    # Test valid string type
    result = DiagramValidator.validate(mermaid, "mermaid")
    assert result.valid
    
    # Test invalid string type
    result = DiagramValidator.validate(mermaid, "unknown")
    assert not result.valid
    assert "Invalid diagram type" in result.errors[0]
