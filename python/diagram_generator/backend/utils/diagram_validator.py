"""Validator for diagram code."""

from enum import Enum
from typing import List, Dict, Optional, Set

class DiagramType(Enum):
    """High-level diagram syntax types."""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"

    @classmethod
    def from_string(cls, value: str) -> Optional['DiagramType']:
        """Create enum from string, case-insensitive."""
        try:
            # Try exact match first
            return cls(value.lower())
        except ValueError:
            # Try case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
            return None

class DiagramSubType(Enum):
    """Specific diagram types."""
    AUTO = "auto"
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ER = "er"
    GANTT = "gantt"
    PIE = "pie"
    MINDMAP = "mindmap"

    @classmethod
    def from_string(cls, value: str) -> 'DiagramSubType':
        """Create enum from string, case-insensitive."""
        try:
            # Try exact match first
            return cls(value.lower())
        except ValueError:
            # Try case-insensitive match
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
            # Default to auto if no match
            return cls.AUTO

class ValidationResult:
    """Result of diagram validation."""
    def __init__(self, valid: bool, errors: List[str] = None, suggestions: List[str] = None):
        self.valid = valid
        self.errors = errors or []
        self.suggestions = suggestions or []

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "suggestions": self.suggestions
        }

class DiagramValidator:
    """Static validator for diagram code."""

    @staticmethod
    def validate(code: str, diagram_type: str) -> ValidationResult:
        """Validate diagram code for given type.

        Args:
            code: Diagram code to validate
            diagram_type: Type of diagram (e.g., 'mermaid', 'plantuml')

        Returns:
            ValidationResult with validation status and any errors
        """
        # Handle case-insensitive type matching
        
        if not code or not code.strip():
            return ValidationResult(False, ["Empty diagram code"])

        # Convert type to enum if string provided
        if isinstance(diagram_type, str):
            diagram_type_enum = DiagramType.from_string(diagram_type.lower())
            if not diagram_type_enum:
                return ValidationResult(
                    False,
                    [f"Invalid diagram type: {diagram_type}"],
                    [f"Available types: {[t.value for t in DiagramType]}"]
                )
        else:
            diagram_type_enum = diagram_type

        # Clean trailing semicolons and validate
        if diagram_type_enum == DiagramType.MERMAID:
            # Strip trailing semicolons
            cleaned_code = DiagramValidator._clean_mermaid_code(code)
            return DiagramValidator._validate_mermaid(cleaned_code)
        elif diagram_type_enum == DiagramType.PLANTUML:
            return DiagramValidator._validate_plantuml(code)
        else:
            return ValidationResult(False, [f"Unsupported diagram type: {diagram_type}"])

    @staticmethod
    def _clean_mermaid_code(code: str) -> str:
        """Clean Mermaid diagram code by removing trailing semicolons and fixing link styles."""
        lines = code.strip().split('\n')
        cleaned_lines = []
        found_link_style = False
        
        for line in lines:
            # Strip trailing semicolons from all lines except those in special sections
            stripped = line.rstrip()
            if stripped.endswith(';'):
                stripped = stripped[:-1]
                
            # Check for linkStyle declarations
            if 'linkStyle' in stripped:
                if 'linkStyle 0 ' in stripped or 'linkStyle 1 ' in stripped:
                    # Replace numbered linkStyle with default
                    stripped = stripped.replace('linkStyle 0 ', 'linkStyle default ').replace('linkStyle 1 ', 'linkStyle default ')
                found_link_style = True
                
            cleaned_lines.append(stripped)
            
        return '\n'.join(cleaned_lines)

    @staticmethod
    def _validate_mermaid(code: str) -> ValidationResult:
        """Validate Mermaid diagram code."""
        code = code.strip()
        valid_starters = {
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 'mindmap'
        }
        
        # Get the first word to check diagram type
        first_word = code.split(' ')[0].lower() if code else ''
        
        if first_word not in valid_starters:
            return ValidationResult(
                False,
                ["Invalid or missing diagram type declaration"],
                [f"Diagram must start with one of: {', '.join(valid_starters)}"]
            )
            
        # Basic structure validation
        if not any(line.strip() and not line.strip().startswith('%') for line in code.split('\n')[1:]):
            return ValidationResult(
                False,
                ["Diagram is empty or contains only comments"],
                ["Add at least one node or connection"]
            )

        # Check for consistency in link styling
        link_styles = [line for line in code.split('\n') if 'linkStyle' in line]
        if link_styles:
            numbered_styles = any('linkStyle 0 ' in style or 'linkStyle 1 ' in style for style in link_styles)
            if numbered_styles:
                return ValidationResult(
                    False,
                    ["Inconsistent link styling"],
                    ["Use 'linkStyle default' instead of numbered linkStyles for consistent styling"]
                )

        return ValidationResult(True)

    @staticmethod
    def _validate_plantuml(code: str) -> ValidationResult:
        """Validate PlantUML diagram code."""
        code = code.strip()
        
        if not code.startswith('@startuml') or not code.endswith('@enduml'):
            return ValidationResult(
                False,
                ["Missing @startuml/@enduml tags"],
                ["Wrap diagram code with @startuml and @enduml"]
            )
            
        # Check for content between tags
        content = code[9:-8].strip()  # Remove tags
        if not content:
            return ValidationResult(
                False,
                ["Empty diagram content"],
                ["Add diagram content between @startuml and @enduml tags"]
            )

        return ValidationResult(True)
