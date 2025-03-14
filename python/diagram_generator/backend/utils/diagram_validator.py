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

# Define PlantUML start tags
PLANTUML_START_TAGS = {
    'mindmap': '@startmindmap',
    'gantt': '@startgantt',
    'class': '@startuml',  # with class context
    'sequence': '@startuml',  # with sequence context
    'state': '@startuml',  # with state context
    'activity': '@startuml',  # with activity context
    'component': '@startuml',  # with component context
    'deployment': '@startuml',  # with deployment context
    'object': '@startuml',  # with object context
    'usecase': '@startuml',  # with usecase context
    'er': '@startuml',  # with ER context
    'timing': '@startuml'  # with timing context
}

class DiagramSubType(Enum):
    """Specific diagram types."""
    AUTO = "auto"
    # Mermaid types
    MERMAID_GRAPH = "graph TD"
    MERMAID_FLOWCHART = "flowchart"
    MERMAID_SEQUENCE = "sequenceDiagram"
    MERMAID_CLASS = "classDiagram"
    MERMAID_STATE = "stateDiagram"
    MERMAID_ER = "erDiagram"
    MERMAID_GANTT = "gantt"
    MERMAID_PIE = "pie"
    MERMAID_MINDMAP = "mindmap"
    MERMAID_JOURNEY = "journey"
    MERMAID_QUADRANT = "quadrantChart"
    # PlantUML types
    PLANTUML_SEQUENCE = "sequence"
    PLANTUML_CLASS = "class"
    PLANTUML_ACTIVITY = "activity"
    PLANTUML_COMPONENT = "component"
    PLANTUML_STATE = "state"
    PLANTUML_MINDMAP = "mindmap"
    PLANTUML_GANTT = "gantt"
    PLANTUML_DEPLOYMENT = "deployment"
    PLANTUML_OBJECT = "object"
    PLANTUML_USECASE = "usecase"
    PLANTUML_ER = "er"
    PLANTUML_TIMING = "timing"

    @classmethod
    def from_string(cls, value: str) -> 'DiagramSubType':
        """Convert string to DiagramSubType enum."""
        try:
            # Handle prefixed values
            if value.startswith('plantuml_'):
                return cls(value)
            if value.startswith('mermaid_'):
                # Try to match against enum values
                for enum_item in cls:
                    if enum_item.name.lower() == value.lower():
                        return enum_item
            return cls(value)
        except ValueError:
            return cls.AUTO

    @classmethod
    def for_syntax(cls, syntax_type: DiagramType) -> List['DiagramSubType']:
        """Get available subtypes for a given syntax."""
        if syntax_type == DiagramType.MERMAID:
            return [
                cls.MERMAID_GRAPH, cls.MERMAID_FLOWCHART, cls.MERMAID_SEQUENCE,
                cls.MERMAID_CLASS, cls.MERMAID_STATE, cls.MERMAID_ER,
                cls.MERMAID_GANTT, cls.MERMAID_PIE, cls.MERMAID_MINDMAP,
                cls.MERMAID_JOURNEY, cls.MERMAID_QUADRANT
            ]
        elif syntax_type == DiagramType.PLANTUML:
            return [
                cls.PLANTUML_SEQUENCE, cls.PLANTUML_CLASS, cls.PLANTUML_ACTIVITY,
                cls.PLANTUML_COMPONENT, cls.PLANTUML_STATE, cls.PLANTUML_MINDMAP,
                cls.PLANTUML_GANTT, cls.PLANTUML_DEPLOYMENT, cls.PLANTUML_OBJECT,
                cls.PLANTUML_USECASE, cls.PLANTUML_ER, cls.PLANTUML_TIMING
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
        is_pie_chart = False

        for i, line in enumerate(lines):
            # Check if this is a pie chart
            if i == 0 and line.strip().lower().startswith('pie'):
                is_pie_chart = True
                # If line is 'pie title X', keep it, otherwise just use 'pie'
                if not line.strip().lower().startswith('pie title'):
                    line = 'pie'
            # Strip trailing semicolons from all lines except those in special sections
            stripped = line.rstrip()
            if stripped.endswith(';'):
                stripped = stripped[:-1]

            # For pie charts, remove % signs from values
            if is_pie_chart and i > 0 and '%' in stripped:
                # Remove % signs from the end of lines, preserving the number
                stripped = stripped.rstrip('%')
                
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

        # Validate pie chart values if this is a pie chart
        if first_word == 'pie':
            lines = code.split('\n')[1:]  # Skip the pie/title line
            for line in lines:
                if line.strip() and not line.strip().startswith('%'):  # Skip empty lines and comments
                    # Check if the line has a value
                    parts = line.strip().split(' ')
                    if len(parts) >= 2:
                        value = parts[-1].strip('"')  # Remove quotes if present
                        try:
                            float(value)  # Try to convert to float
                        except ValueError:
                            return ValidationResult(
                                False,
                                ["Invalid pie chart value"],
                                ["Pie chart values must be numbers (not percentages)"]
                            )

        return ValidationResult(True)

    @staticmethod
    def _validate_plantuml(code: str) -> ValidationResult:
        """Validate PlantUML diagram code."""
        code = code.strip()
        
        # Check for any valid start tag
        valid_start = any(tag in code.split('\n')[0].lower() for tag in PLANTUML_START_TAGS.values())
        if not valid_start:
            available_types = [f"{k} ({v})" for k, v in PLANTUML_START_TAGS.items()]
            return ValidationResult(
                False,
                ["Invalid or missing PlantUML start tag"],
                [f"Diagram must start with one of: {', '.join(available_types)}"]
            )
            
        # Check for matching end tag
        if not code.strip().endswith('@enduml'):
            return ValidationResult(
                False,
                ["Missing @enduml tag"],
                ["Diagram must end with @enduml"]
            )
            
        # Check for content between tags
        first_line_end = code.find('\n')
        if first_line_end == -1:
            return ValidationResult(
                False,
                ["Single line PlantUML diagram"],
                ["Add content between start and end tags"]
            )
            
        content = code[first_line_end:code.rindex('@enduml')].strip()
        if not content:
            return ValidationResult(
                False,
                ["Empty diagram content"],
                ["Add diagram content between start and end tags"]
            )

        # Extract diagram type from start tag
        start_line = code.split('\n')[0].lower()
        for diagram_type, tag in PLANTUML_START_TAGS.items():
            if tag in start_line:
                if diagram_type in ['class', 'sequence', 'state', 'activity', 'component', 'deployment', 'object', 'usecase', 'er', 'timing']:
                    # For @startuml diagrams, we should look for type-specific syntax
                    type_indicators = {
                        'class': ['class ', 'interface ', 'enum '],
                        'sequence': ['participant ', '-> ', '<- '],
                        'state': ['state ', '[*] -> '],
                        'activity': ['start', 'stop', ':'],
                        'component': ['component ', 'interface ', 'package '],
                        'deployment': ['node ', 'artifact ', 'database '],
                        'object': ['object ', 'map '],
                        'usecase': ['actor ', 'usecase '],
                        'er': ['entity ', 'relationship '],
                        'timing': ['clock ', 'binary ']
                    }
                    
                    # Check for type-specific indicators
                    indicators = type_indicators.get(diagram_type, [])
                    if not any(indicator in content.lower() for indicator in indicators):
                        return ValidationResult(
                            False,
                            [f"Missing {diagram_type} diagram specific syntax"],
                            [f"Add {diagram_type}-specific elements like {', '.join(indicators)}"]
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
