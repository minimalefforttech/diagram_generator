"""Unit tests for diagram validation."""

import pytest
from diagram_generator.backend.utils.diagram_validator import (
    DiagramValidator, 
    DiagramType,
    ValidationResult
)

def test_diagram_type_enum():
    """Test diagram type enumeration."""
    # Valid types
    assert DiagramType.from_string("mermaid") == DiagramType.MERMAID
    assert DiagramType.from_string("plantuml") == DiagramType.PLANTUML
    
    # Case insensitive
    assert DiagramType.from_string("MERMAID") == DiagramType.MERMAID
    assert DiagramType.from_string("Plantuml") == DiagramType.PLANTUML
    
    # Invalid types
    assert DiagramType.from_string("invalid") is None
    assert DiagramType.from_string("") is None

def test_mermaid_sequence_validation():
    """Test Mermaid sequence diagram validation."""
    validator = DiagramValidator()
    
    # Valid sequence diagram
    valid_code = """graph TD
sequenceDiagram
participant User
participant System
User->>System: Login request
System-->>User: Success response"""
    result = validator.validate(valid_code, DiagramType.MERMAID)
    assert result.valid, f"Validation failed with errors: {result.errors}"
    assert not result.errors
    
    # Missing participant
    invalid_code = """sequenceDiagram
A->>B: Message"""
    result = validator.validate(invalid_code, DiagramType.MERMAID)
    assert not result.valid
    assert result.errors
    assert any(error.lower().count("diagram") > 0 for error in result.errors)

def test_mermaid_flowchart_validation():
    """Test Mermaid flowchart validation."""
    validator = DiagramValidator()
    
    # Valid flowchart
    valid_code = """graph TD
A[Start] --> B{Decision}
B -->|Yes| C[Action]
B -->|No| D[End]"""
    result = validator.validate(valid_code, DiagramType.MERMAID)
    assert result.valid
    assert not result.errors
    
    # Empty flowchart
    empty_code = "flowchart TD"
    result = validator.validate(empty_code, DiagramType.MERMAID)
    assert not result.valid
    assert result.errors

def test_plantuml_validation():
    """Test PlantUML validation."""
    validator = DiagramValidator()
    
    # Valid sequence diagram
    valid_code = """@startuml
participant "API" as api
participant "Database" as db
api -> db : Read data
db --> api : Data response
@enduml"""
    result = validator.validate(valid_code, DiagramType.PLANTUML)
    assert result.valid, f"Validation failed with errors: {result.errors}"
    assert not result.errors
    
    # Missing end tag
    invalid_code = """@startuml
participant "Component A"
"""
    result = validator.validate(invalid_code, DiagramType.PLANTUML)
    assert not result.valid
    assert any("enduml" in error.lower() for error in result.errors)

def test_empty_validation():
    """Test validation of empty or whitespace input."""
    validator = DiagramValidator()
    
    # Empty string
    result = validator.validate("", DiagramType.MERMAID)
    assert not result.valid
    assert result.errors
    assert any("empty" in error.lower() for error in result.errors)
    
    # Only whitespace
    result = validator.validate("   \n\t   ", DiagramType.MERMAID)
    assert not result.valid
    assert result.errors
    assert any("empty" in error.lower() for error in result.errors)

def test_invalid_type_validation():
    """Test validation with invalid diagram type."""
    validator = DiagramValidator()
    
    code = """graph TD\nA->B: Message"""
    result = validator.validate(code, "invalid_type")
    assert not result.valid
    assert any("type" in error.lower() for error in result.errors)

def test_plantuml_start_tags():
    """Test PlantUML start tag validation."""
    validator = DiagramValidator()
    
    # Test different start tags
    start_tags = {
        'mindmap': """@startmindmap
* root
** First
** Second
@enduml""",
        'gantt': """@startgantt
project starts 2024-01-01
[Task1] lasts 10 days
then [Task2] lasts 4 days
@enduml""",
        'class': """@startuml
class User {
  +name: String
  +login(): void
}
class Admin extends User
@enduml""",
        'sequence': """@startuml
participant "Alice" as A
participant "Bob" as B
A -> B : Request
B --> A : Response
@enduml""",
        'component': """@startuml
actor User
participant "Web UI" as ui
participant "API" as api
User -> ui : Login
ui -> api : Authenticate
api --> ui : Success
ui --> User : Welcome
@enduml"""
    }
    
    for diagram_type, code in start_tags.items():
        result = validator.validate(code, DiagramType.PLANTUML)
        assert result.valid, f"Failed for {diagram_type} diagram: {result.errors}"

def test_mermaid_comments():
    """Test Mermaid comment handling."""
    validator = DiagramValidator()
    
    code_with_comments = """graph TD
%% Actor definitions
A[Start] -->|Action| B[End]
%% Flow complete"""
    
    result = validator.validate(code_with_comments, DiagramType.MERMAID)
    assert result.valid, f"Validation failed with errors: {result.errors}"
    assert not result.errors

def test_whitespace_handling():
    """Test handling of different whitespace patterns."""
    validator = DiagramValidator()
    
    code_with_spaces = """graph TD
A[Start] --> B{Process}
    B -->|Yes| C[Success]
        B -->|No| D[Failure]"""
    result = validator.validate(code_with_spaces, DiagramType.MERMAID)
    assert result.valid, f"Validation failed with errors: {result.errors}"
    assert not result.errors

def test_multiline_validation():
    """Test validation across multiple lines."""
    validator = DiagramValidator()
    
    valid_code = """graph TD
A[Start] --> B{Process}
B -->|Yes| C[Continue]
B -->|No| D[Stop]
C --> E[Complete]"""
    result = validator.validate(valid_code, DiagramType.MERMAID)
    assert result.valid, f"Validation failed with errors: {result.errors}"
    assert not result.errors
