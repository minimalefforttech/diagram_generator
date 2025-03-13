"""Validator for diagram code."""

from enum import Enum
from typing import List, Dict, Optional, Set

class DiagramType(Enum):
    """High-level diagram syntax types."""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"

    @classmethod
    def from_string(cls, value: str) -> Optional['DiagramType']:
        """Convert string to DiagramType enum.
        
        Args:
            value: String value to convert
            
        Returns:
            DiagramType enum value or None if not found
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None

    @classmethod
    def to_list(cls) -> List[str]:
        """Get list of all diagram type values."""
        return [t.value for t in cls]

class DiagramSubType(Enum):
    """Specific diagram types."""
    AUTO = "auto"
    # Mermaid types
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ER = "er"
    GANTT = "gantt"
    PIE = "pie"
    MINDMAP = "mindmap"
    # PlantUML types
    PLANTUML_SEQUENCE = "plantuml_sequence"
    PLANTUML_CLASS = "plantuml_class"
    PLANTUML_ACTIVITY = "plantuml_activity"
    PLANTUML_COMPONENT = "plantuml_component"
    PLANTUML_STATE = "plantuml_state"
    PLANTUML_MINDMAP = "plantuml_mindmap"
    PLANTUML_GANTT = "plantuml_gantt"

    @classmethod
    def from_string(cls, value: str) -> 'DiagramSubType':
        """Convert string to DiagramSubType enum."""
        try:
            # Handle both plain and plantuml-prefixed values
            if value.startswith('plantuml_'):
                return cls(value)
            return cls(value.upper())
        except ValueError:
            return cls.AUTO

    @classmethod
    def for_syntax(cls, syntax_type: DiagramType) -> List['DiagramSubType']:
        """Get available subtypes for a given syntax."""
        if syntax_type == DiagramType.MERMAID:
            return [
                cls.FLOWCHART, cls.SEQUENCE, cls.CLASS,
                cls.STATE, cls.ER, cls.GANTT, cls.PIE, cls.MINDMAP
            ]
        elif syntax_type == DiagramType.PLANTUML:
            return [
                cls.PLANTUML_SEQUENCE, cls.PLANTUML_CLASS,
                cls.PLANTUML_ACTIVITY, cls.PLANTUML_COMPONENT,
                cls.PLANTUML_STATE, cls.PLANTUML_MINDMAP,
                cls.PLANTUML_GANTT
            ]
        return []

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
            cleaned_code = DiagramValidator._clean_plantuml_code(code)
            return DiagramValidator._validate_plantuml(cleaned_code)
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

    @staticmethod
    def _clean_plantuml_code(code: str) -> str:
        """Clean PlantUML diagram code by normalizing tags and whitespace."""
        lines = code.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace
            stripped = line.strip()
            
            # Fix common tag issues
            if stripped.startswith('@start') and not ' ' in stripped:
                # Fix missing space in tags like @startUML -> @startuml
                stripped = stripped[:5].lower() + stripped[5:]
            elif stripped.startswith('@end') and not ' ' in stripped:
                stripped = stripped[:4].lower() + stripped[4:]
                
            cleaned_lines.append(stripped)
            
        return '\n'.join(cleaned_lines)
