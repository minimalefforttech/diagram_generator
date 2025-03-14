"""Tests for diagram validation utilities."""

import pytest
from datetime import datetime

from diagram_generator.backend.utils.diagram_validator import (
    DiagramType,
    DiagramSubType,
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

def test_validate_mermaid_mindmap():
    """Test validation of Mermaid mindmap diagrams."""
    test_cases = [
        # Valid mindmap with single root
        ("""mindmap
  root((My Project))
    Features
      Core
      Advanced
    Timeline
      Phase 1
      Phase 2""", True),

        # Valid mindmap with explicit root syntax
        ("""mindmap
root((Project))
  Features
    Core
  Timeline
    Phase 1""", True),

        # Invalid - multiple roots
        ("""mindmap
  root((Project 1))
  Features
  Timeline""", False),

        # Invalid - no root node
        ("""mindmap""", False),

        # Invalid - improper indentation
        ("""mindmap
  root((Project))
      Features
    Core""", False),
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors, "Invalid diagram should have error messages"
            assert result.suggestions, "Invalid diagram should have suggestions"

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

def test_validate_plantuml_subtypes():
    """Test validation of different PlantUML diagram subtypes."""
    test_cases = [
        # Sequence diagram
        ("""@startuml
        Alice -> Bob: Authentication Request
        Bob --> Alice: Authentication Response
        @enduml""", True),
        
        # Class diagram
        ("""@startuml
        class Car {
          -brand: String
          +start(): void
          +stop(): void
        }
        @enduml""", True),
        
        # Activity diagram
        ("""@startuml
        start
        :Eat Hot Dogs;
        :Drink Soda;
        stop
        @enduml""", True),
        
        # Component diagram
        ("""@startuml
        [First Component]
        [Another Component] as AC
        [First Component] --> AC
        @enduml""", True),
        
        # State diagram
        ("""@startuml
        [*] --> State1
        State1 --> [*]
        @enduml""", True),
        
        # Invalid diagram - mixed types
        ("""@startuml
        class User {
          +name: String
        }
        Alice -> Bob: hello
        @enduml""", False)
    ]
    
    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, DiagramType.PLANTUML)
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"

def test_plantuml_specific_features():
    """Test PlantUML-specific syntax features."""
    test_cases = [
        # Skinparam usage
        ("""@startuml
        skinparam monochrome true
        Alice -> Bob: Hello
        @enduml""", True),
        
        # Title and header
        ("""@startuml
        title This is a title
        header Page Header
        Alice -> Bob: Hello
        @enduml""", True),
        
        # Note syntax
        ("""@startuml
        Alice -> Bob: Hello
        note left: This is a note
        @enduml""", True),
        
        # Styling with colors
        ("""@startuml
        skinparam sequence {
            ArrowColor DeepSkyBlue
            ActorBorderColor DeepSkyBlue
        }
        Alice -> Bob: Hello
        @enduml""", True),
        
        # Invalid skinparam
        ("""@startuml
        skinparam invalid_param true
        Alice -> Bob: Hello
        @enduml""", True),  # Should still be valid as PlantUML handles unknown params
        
        # Invalid note placement
        ("""@startuml
        note invalid: This note has invalid placement
        Alice -> Bob: Hello
        @enduml""", False)
    ]
    
    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, DiagramType.PLANTUML)
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"

def test_plantuml_diagram_type_detection():
    """Test detection of PlantUML diagram subtypes."""
    test_cases = [
        ("@startuml\nAlice -> Bob\n@enduml", DiagramSubType.PLANTUML_SEQUENCE),
        ("@startuml\nclass User\n@enduml", DiagramSubType.PLANTUML_CLASS),
        ("@startuml\n[Component]\n@enduml", DiagramSubType.PLANTUML_COMPONENT),
        ("@startuml\nstate Idle\n@enduml", DiagramSubType.PLANTUML_STATE),
        ("@startmindmap\n* Root\n@endmindmap", DiagramSubType.PLANTUML_MINDMAP),
        ("@startuml\nstart\n:Step;\nstop\n@enduml", DiagramSubType.PLANTUML_ACTIVITY),
        ("@startuml\nProject starts 2024/01/01\n[Task] lasts 10 days\n@enduml", DiagramSubType.PLANTUML_GANTT),
        ("@startuml\ninvalid content\n@enduml", DiagramSubType.AUTO)  # Default to auto if can't detect
    ]
    
    for diagram, expected_type in test_cases:
        detected_type = DiagramSubType.from_string(DiagramValidator.detect_subtype(diagram))
        assert detected_type == expected_type, f"Failed to detect correct subtype for: {diagram}"

def test_plantuml_code_cleaning():
    """Test cleaning of PlantUML diagram code."""
    test_cases = [
        # Fix tag casing
        ("@StartUML\nBob->Alice\n@EndUML", "@startuml\nBob->Alice\n@enduml"),
        # Normalize whitespace
        ("@startuml    \n   Bob  ->  Alice   \n   @enduml   ", "@startuml\nBob -> Alice\n@enduml"),
        # Fix common tag variants
        ("@startuml\nBob->Alice\n@enduml", "@startuml\nBob->Alice\n@enduml"),
        # Handle empty lines
        ("@startuml\n\n\nBob->Alice\n\n\n@enduml", "@startuml\nBob->Alice\n@enduml"),
        # Preserve indentation structure
        ("@startuml\n  Bob->Alice\n    note right: Hello\n@enduml", "@startuml\n  Bob->Alice\n    note right: Hello\n@enduml")
    ]
    
    for input_code, expected_output in test_cases:
        cleaned = DiagramValidator._clean_plantuml_code(input_code)
        assert cleaned.strip() == expected_output.strip(), f"Failed cleaning for: {input_code}"

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

def test_validate_mermaid_sequence():
    """Test validation of Mermaid sequence diagrams."""
    test_cases = [
        # Valid sequence diagram
        ("""sequenceDiagram
    participant Alice
    participant Bob
    Alice->>Bob: Hello
    Bob-->>Alice: Hi""", True),

        # Missing participants
        ("""sequenceDiagram
    Alice->>Bob: Hello""", False),

        # Invalid message syntax
        ("""sequenceDiagram
    participant Alice
    participant Bob
    Alice Bob Hello""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_mermaid_class():
    """Test validation of Mermaid class diagrams."""
    test_cases = [
        # Valid class diagram
        ("""classDiagram
    class Animal {
        +String name
        +makeSound()
    }
    class Dog {
        +bark()
    }
    Animal <|-- Dog""", True),

        # Missing class declarations
        ("""classDiagram
    Animal <|-- Dog""", False),
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_mermaid_flowchart():
    """Test validation of Mermaid flowcharts."""
    test_cases = [
        # Valid flowchart
        ("""flowchart TD
    A[Start] --> B[Process]
    B --> C[End]""", True),

        # No nodes
        ("""flowchart TD
    --> B --> C""", False),

        # No connections
        ("""flowchart TD
    A[Start]
    B[Process]""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_mermaid_state():
    """Test validation of Mermaid state diagrams."""
    test_cases = [
        # Valid state diagram
        ("""stateDiagram
    [*] --> Idle
    Idle --> Active
    Active --> Idle""", True),

        # No states/transitions
        ("""stateDiagram""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_mermaid_er():
    """Test validation of Mermaid ER diagrams."""
    test_cases = [
        # Valid ER diagram
        ("""erDiagram
    CUSTOMER {
        string name
        string email
    }
    ORDER {
        int id
    }
    CUSTOMER ||--o{ ORDER : places""", True),

        # Missing relationships
        ("""erDiagram
    CUSTOMER {
        string name
    }
    ORDER {
        int id
    }""", False),

        # Missing entities
        ("""erDiagram
    CUSTOMER ||--o{ ORDER : places""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_mermaid_gantt():
    """Test validation of Mermaid Gantt charts."""
    test_cases = [
        # Valid Gantt chart
        ("""gantt
    dateFormat YYYY-MM-DD
    section Tests
    First task: 2024-01-01, 7d
    Second task: 2024-01-08, 5d""", True),

        # Missing date format
        ("""gantt
    section Tests
    First task: 2024-01-01, 7d""", False),

        # Missing tasks
        ("""gantt
    dateFormat YYYY-MM-DD
    section Tests""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "mermaid")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_sequence():
    """Test validation of PlantUML sequence diagrams."""
    test_cases = [
        # Valid sequence diagram
        ("""@startuml
participant User
participant System
User -> System: Request
System --> User: Response
@enduml""", True),

        # Missing participants
        ("""@startuml
Alice -> Bob: Hello
@enduml""", False),

        # Invalid message syntax (missing colon)
        ("""@startuml
participant Alice
participant Bob
Alice -> Bob
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_class():
    """Test validation of PlantUML class diagrams."""
    test_cases = [
        # Valid class diagram
        ("""@startuml
class User {
    +name: String
    +email: String
}
class Account {
    +balance: Number
}
User --> Account: has
@enduml""", True),

        # Missing class definitions
        ("""@startuml
User --> Account: has
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_state():
    """Test validation of PlantUML state diagrams."""
    test_cases = [
        # Valid state diagram
        ("""@startuml
[*] --> Idle
state Idle
state Active
Idle -> Active: Start
Active -> Idle: Stop
@enduml""", True),

        # Valid with implicit states
        ("""@startuml
[*] --> Idle
Idle -> Active: Start
Active -> Idle: Stop
@enduml""", True),

        # No states or transitions
        ("""@startuml
title State Machine
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_activity():
    """Test validation of PlantUML activity diagrams."""
    test_cases = [
        # Valid activity diagram
        ("""@startuml
start
:Initialize;
if (Valid?) then (yes)
    :Process Data;
else (no)
    :Handle Error;
endif
stop
@enduml""", True),

        # Missing start
        ("""@startuml
:Initialize;
:Process;
stop
@enduml""", False),

        # Missing stop/end
        ("""@startuml
start
:Initialize;
:Process;
@enduml""", False),

        # No activities
        ("""@startuml
start
stop
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_component():
    """Test validation of PlantUML component diagrams."""
    test_cases = [
        # Valid component diagram
        ("""@startuml
package "Frontend" {
    [UserInterface]
    [APIClient]
}
package "Backend" {
    [APIServer]
    [Database]
}
[UserInterface] --> [APIServer]
@enduml""", True),

        # No components
        ("""@startuml
title System Components
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_usecase():
    """Test validation of PlantUML use case diagrams."""
    test_cases = [
        # Valid use case diagram
        ("""@startuml
actor User
usecase "Login" as UC1
usecase "View Profile" as UC2
User --> UC1
User --> UC2
@enduml""", True),

        # Missing actors/use cases
        ("""@startuml
title Use Cases
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_er():
    """Test validation of PlantUML ER diagrams."""
    test_cases = [
        # Valid ER diagram
        ("""@startuml
entity User {
    id: number
    name: string
}
entity Order {
    id: number
    total: number
}
User ||--o{ Order
@enduml""", True),

        # Missing entities
        ("""@startuml
User ||--o{ Order
@enduml""", False),

        # Missing relationships
        ("""@startuml
entity User {
    id: number
}
entity Order {
    id: number
}
@enduml""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_mindmap():
    """Test validation of PlantUML mindmap diagrams."""
    test_cases = [
        # Valid mindmap
        ("""@startmindmap
* Project
** Frontend
*** React
*** TypeScript
** Backend
*** Python
*** FastAPI
@endmindmap""", True),

        # Missing nodes
        ("""@startmindmap
@endmindmap""", False),

        # Invalid hierarchy (skipping level)
        ("""@startmindmap
* Root
*** Invalid Level
@endmindmap""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions

def test_validate_plantuml_gantt():
    """Test validation of PlantUML Gantt charts."""
    test_cases = [
        # Valid gantt chart
        ("""@startgantt
Project starts 2024-01-01
[Task 1] lasts 10 days
[Task 2] starts at [Task 1]'s end
@endgantt""", True),

        # Missing project start
        ("""@startgantt
[Task 1] lasts 10 days
@endgantt""", False),

        # Missing tasks
        ("""@startgantt
Project starts 2024-01-01
@endgantt""", False)
    ]

    for diagram, should_be_valid in test_cases:
        result = DiagramValidator.validate(diagram, "plantuml")
        assert result.valid == should_be_valid, f"Failed validation for: {diagram}"
        if not should_be_valid:
            assert result.errors
            assert result.suggestions
