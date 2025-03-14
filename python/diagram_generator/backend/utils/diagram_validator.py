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
        
        first_word = code.split()[0].lower() if code else ''
        
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

        # Type-specific validation
        if first_word == 'sequenceDiagram':
            # Validate participant declarations and message syntax
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            if not any(line.startswith('participant ') or line.startswith('actor ') for line in lines):
                return ValidationResult(
                    False,
                    ["Missing participant declarations"],
                    ["Sequence diagrams should declare participants using 'participant' or 'actor'"]
                )
            
            # Check message syntax
            message_lines = [line for line in lines if '->' in line or '-->' in line or '>>' in line]
            if not message_lines:
                return ValidationResult(
                    False,
                    ["No messages defined"],
                    ["Add at least one message between participants using ->, -->, or >>"]
                )

            # Validate message syntax
            for line in message_lines:
                if not (':' in line and any(x in line for x in ['->', '-->>', '->>', '-->', '-x'])):
                    return ValidationResult(
                        False,
                        ["Invalid message syntax"],
                        ["Messages should follow format: ParticipantA->ParticipantB: Message"]
                    )

        elif first_word in ['graph', 'flowchart']:
            # Validate node and connection syntax
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            nodes = set()
            connections = []
            
            for line in lines[1:]:  # Skip the declaration line
                if '-->' in line or '---' in line:
                    connections.append(line)
                    parts = line.split('--')
                    for part in parts[0].split():
                        if part and not part.startswith('(') and not part.startswith('['):
                            nodes.add(part)
            
            if not nodes:
                return ValidationResult(
                    False,
                    ["No nodes defined"],
                    ["Add at least one node using [] or () syntax"]
                )
            
            if not connections:
                return ValidationResult(
                    False,
                    ["No connections between nodes"],
                    ["Connect nodes using --> or --- syntax"]
                )

        elif first_word == 'classDiagram':
            # Validate class declarations and relationships
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            classes = []
            relationships = []
            
            for line in lines[1:]:
                if line.startswith('class '):
                    classes.append(line)
                elif any(x in line for x in ['<|--', '*--', 'o--', '-->', '<--']):
                    relationships.append(line)
                
            if not classes:
                return ValidationResult(
                    False,
                    ["No classes defined"],
                    ["Define at least one class using 'class ClassName' syntax"]
                )

        elif first_word == 'stateDiagram':
            # Validate state transitions
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            states = set()
            transitions = []
            
            for line in lines[1:]:
                if '-->' in line:
                    transitions.append(line)
                    parts = line.split('-->')
                    states.add(parts[0].strip())
                    states.add(parts[1].strip())
                    
            if not states:
                return ValidationResult(
                    False,
                    ["No states defined"],
                    ["Define states and transitions using state --> state syntax"]
                )

        elif first_word == 'erDiagram':
            # Validate entity declarations and relationships
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            entities = set()
            relationships = []
            
            for line in lines[1:]:
                if '|' in line and 'o' in line:  # Relationship line
                    relationships.append(line)
                    parts = line.split()
                    if parts:
                        entities.add(parts[0])
                elif '{' in line:  # Entity declaration
                    entity_name = line.split('{')[0].strip()
                    entities.add(entity_name)
                    
            if not entities:
                return ValidationResult(
                    False,
                    ["No entities defined"],
                    ["Define at least one entity with properties"]
                )
                
            if not relationships:
                return ValidationResult(
                    False,
                    ["No relationships defined"],
                    ["Define relationships between entities using |o--o|, ||--|{, etc."]
                )

        elif first_word == 'gantt':
            # Validate gantt chart structure
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            has_date_format = any('dateFormat' in line for line in lines)
            has_tasks = any(':' in line for line in lines[1:])  # Skip title line
            
            if not has_date_format:
                return ValidationResult(
                    False,
                    ["Missing date format"],
                    ["Specify date format using dateFormat directive"]
                )
                
            if not has_tasks:
                return ValidationResult(
                    False,
                    ["No tasks defined"],
                    ["Add at least one task with duration"]
                )

        elif first_word == 'mindmap':
            # Mindmap validation (already implemented)
            lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('%')]
            if len(lines) < 2:
                return ValidationResult(
                    False,
                    ["Mindmap must have at least one node"],
                    ["Add at least one root node to the mindmap"]
                )
            
            # Check for single root
            root_level_items = []
            for line in lines[1:]:  # Skip the mindmap declaration
                indent = len(line) - len(line.lstrip())
                if indent == 0 or (indent == 2 and line.strip().startswith('root')):
                    root_level_items.append(line.strip())
            
            if len(root_level_items) == 0:
                return ValidationResult(
                    False,
                    ["Mindmap missing root node"],
                    ["Add a root level node to the mindmap"]
                )
            elif len(root_level_items) > 1:
                return ValidationResult(
                    False,
                    ["Multiple root nodes detected"],
                    ["Mindmap must have exactly one root node. Remove or indent additional root level items"]
                )

            # Validate indent structure
            prev_indent = 0
            for line in lines[1:]:
                if not line.strip():
                    continue
                indent = len(line) - len(line.lstrip())
                if indent > prev_indent + 2:
                    return ValidationResult(
                        False,
                        ["Invalid indentation"],
                        ["Each level should be indented by 2 spaces relative to its parent"]
                    )
                prev_indent = indent

        elif first_word == 'pie':
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

        # Extract diagram type and validate type-specific syntax
        start_line = code.split('\n')[0].lower()
        content_lines = [line.strip() for line in content.split('\n') if line.strip()]

        if '@startmindmap' in start_line:
            # Validate mindmap structure
            if not any('*' in line for line in content_lines):
                return ValidationResult(
                    False,
                    ["No mindmap nodes found"],
                    ["Add at least one node using * syntax"]
                )

            # Check node hierarchy
            prev_level = 0
            for line in content_lines:
                level = len(line) - len(line.lstrip('*'))
                if level > prev_level + 1:
                    return ValidationResult(
                        False,
                        ["Invalid node hierarchy"],
                        ["Each level can only increase by one * at a time"]
                    )
                prev_level = level

        elif '@startuml' in start_line:
            # Look for diagram type indicators
            if any(line.startswith('class ') for line in content_lines):
                # Class diagram validation
                classes = []
                relationships = []
                
                for line in content_lines:
                    if line.startswith('class '):
                        classes.append(line)
                    elif any(x in line for x in ['<|--', '*--', 'o--', '-->', '<--', '<|-', '-|>']):
                        relationships.append(line)
                
                if not classes:
                    return ValidationResult(
                        False,
                        ["No classes defined"],
                        ["Define at least one class using 'class' keyword"]
                    )

            elif '->' in content or '-->' in content:
                # Sequence diagram validation
                found_participant = False
                found_message = False
                
                for line in content_lines:
                    if line.startswith('participant ') or line.startswith('actor '):
                        found_participant = True
                    elif '->' in line or '-->' in line:
                        if ':' not in line:
                            return ValidationResult(
                                False,
                                ["Invalid message syntax"],
                                ["Messages should include a description after ':' symbol"]
                            )
                        found_message = True
                
                if not found_participant:
                    return ValidationResult(
                        False,
                        ["No participants defined"],
                        ["Define participants using 'participant' or 'actor' keywords"]
                    )
                
                if not found_message:
                    return ValidationResult(
                        False,
                        ["No messages defined"],
                        ["Add at least one message between participants"]
                    )

            elif 'state ' in content or '[*] ->' in content:
                # State diagram validation
                states = set()
                transitions = []
                
                for line in content_lines:
                    if line.startswith('state '):
                        states.add(line.split()[1])
                    elif '->' in line:
                        transitions.append(line)
                        parts = line.split('->')
                        if len(parts) == 2:
                            states.add(parts[0].strip())
                            states.add(parts[1].split(':')[0].strip())
                
                if not states and not any('[*]' in line for line in content_lines):
                    return ValidationResult(
                        False,
                        ["No states defined"],
                        ["Define states using 'state' keyword or [*] for start/end states"]
                    )
                
                if not transitions:
                    return ValidationResult(
                        False,
                        ["No transitions defined"],
                        ["Add transitions between states using ->"]
                    )

            elif any(line.startswith('package ') or line.startswith('[') or line.startswith('component ') for line in content_lines):
                # Component diagram validation
                components = []
                connections = []
                
                for line in content_lines:
                    if line.startswith('package ') or line.startswith('[') or line.startswith('component '):
                        components.append(line)
                    elif '-->' in line or '<--' in line:
                        connections.append(line)
                
                if not components:
                    return ValidationResult(
                        False,
                        ["No components defined"],
                        ["Define components using 'component', 'package', or [] syntax"]
                    )

            elif any(line.startswith('usecase ') or line.startswith('actor ') for line in content_lines):
                # Use case diagram validation
                elements = []
                connections = []
                
                for line in content_lines:
                    if line.startswith('usecase ') or line.startswith('actor '):
                        elements.append(line)
                    elif '-->' in line or '--' in line:
                        connections.append(line)
                
                if not elements:
                    return ValidationResult(
                        False,
                        ["No actors or use cases defined"],
                        ["Define actors and use cases using 'actor' and 'usecase' keywords"]
                    )

            elif any(line.startswith('start') or line.startswith(':') or line.startswith('if ') for line in content_lines):
                # Activity diagram validation
                if not any(line.startswith('start') for line in content_lines):
                    return ValidationResult(
                        False,
                        ["Missing start node"],
                        ["Activity diagrams must begin with 'start'"]
                    )
                
                if not any(line.startswith('stop') or line.startswith('end') for line in content_lines):
                    return ValidationResult(
                        False,
                        ["Missing end node"],
                        ["Activity diagrams must end with 'stop' or 'end'"]
                    )

                # Check activity definitions
                if not any(line.startswith(':') for line in content_lines):
                    return ValidationResult(
                        False,
                        ["No activities defined"],
                        ["Define activities using :activity name; syntax"]
                    )

            elif any(line.startswith('entity ') for line in content_lines):
                # ER diagram validation
                entities = set()
                relationships = []
                
                for line in content_lines:
                    if line.startswith('entity '):
                        entities.add(line.split()[1])
                    elif any(x in line for x in ['--|{', '--||', '--o|', '--||']):
                        relationships.append(line)
                
                if not entities:
                    return ValidationResult(
                        False,
                        ["No entities defined"],
                        ["Define entities using 'entity' keyword"]
                    )
                
                if not relationships:
                    return ValidationResult(
                        False,
                        ["No relationships defined"],
                        ["Define relationships between entities"]
                    )

        elif '@startgantt' in start_line:
            # Gantt chart validation
            has_project = False
            has_tasks = False
            
            for line in content_lines:
                if 'project starts' in line.lower():
                    has_project = True
                elif '] lasts' in line or '] starts' in line:
                    has_tasks = True
            
            if not has_project:
                return ValidationResult(
                    False,
                    ["Missing project start"],
                    ["Define project start date using 'Project starts' directive"]
                )
            
            if not has_tasks:
                return ValidationResult(
                    False,
                    ["No tasks defined"],
                    ["Add tasks using [Task] syntax with starts/lasts duration"]
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
