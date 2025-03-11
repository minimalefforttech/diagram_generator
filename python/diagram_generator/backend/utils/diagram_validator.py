"""Utilities for validating diagram syntax."""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

class DiagramType(Enum):
    """Supported diagram types."""
    MERMAID = "mermaid"
    PLANTUML = "plantuml"

class ValidationResult:
    """Result of diagram validation."""
    def __init__(self, valid: bool, errors: List[str] = None, suggestions: List[str] = None):
        self.valid = valid
        self.errors = errors or []
        self.suggestions = suggestions or []

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "suggestions": self.suggestions
        }

class DiagramValidator:
    """Validates diagram syntax for different formats."""
    
    @staticmethod
    def detect_type(code: str) -> Optional[DiagramType]:
        """Detect diagram type from code.
        
        Args:
            code: Diagram code to analyze
            
        Returns:
            DiagramType if detected, None otherwise
        """
        # Check for Mermaid syntax indicators
        mermaid_indicators = [
            r"^\s*graph\s+",
            r"^\s*sequenceDiagram",
            r"^\s*classDiagram",
            r"^\s*stateDiagram",
            r"^\s*erDiagram",
            r"^\s*gantt",
            r"^\s*pie",
            r"^\s*flowchart\s+",
        ]
        
        # Check for PlantUML syntax indicators
        plantuml_indicators = [
            r"^\s*@startuml",
            r"^\s*@startmindmap",
            r"^\s*@startsalt",
            r"^\s*@startgantt",
        ]
        
        # Normalize line endings and clean whitespace
        code = "\n".join(line.strip() for line in code.strip().split("\n"))
        
        for pattern in mermaid_indicators:
            if re.search(pattern, code, re.MULTILINE):
                return DiagramType.MERMAID
                
        for pattern in plantuml_indicators:
            if re.search(pattern, code, re.MULTILINE):
                return DiagramType.PLANTUML
                
        return None

    @staticmethod
    def validate_mermaid(code: str) -> ValidationResult:
        """Validate Mermaid diagram syntax.
        
        Args:
            code: Mermaid diagram code
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        suggestions = []
        
        # Basic structure validation
        if not code.strip():
            errors.append("Diagram code is empty")
            return ValidationResult(False, errors, suggestions)
        
        # Normalize whitespace and split into lines
        code = code.strip()
        lines = [line.strip() for line in code.split("\n") if line.strip()]
        if not lines:
            errors.append("Diagram code is empty after whitespace normalization")
            return ValidationResult(False, errors, suggestions)
            
        # Remove excessive indentation from input
        min_indent = float('inf')
        for line in lines:
            indent = len(line) - len(line.lstrip())
            if line and indent < min_indent:
                min_indent = indent
        if min_indent != float('inf'):
            lines = [line[min_indent:] if line else line for line in lines]
            
        first_line = lines[0].strip()
        
        # Validate diagram type declaration
        valid_starts = [
            r"^\s*graph\s+", r"^\s*sequenceDiagram",
            r"^\s*classDiagram", r"^\s*stateDiagram",
            r"^\s*erDiagram", r"^\s*gantt",
            r"^\s*pie", r"^\s*flowchart\s+"
        ]
        if not any(re.match(pattern, first_line) for pattern in valid_starts):
            errors.append("Invalid or missing diagram type declaration")
            suggestions.append("Start with a valid diagram type (e.g., 'graph TD', 'sequenceDiagram', etc.)")
        
        # Define valid characters for nodes and arrows
        node_chars = r'[A-Za-z0-9_\-\s\[\]\(\){}"\':]'
        arrow_pattern = rf'{node_chars}+\s*-+>+\s*{node_chars}+'

        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Check arrow syntax - allow both -> and --> in Mermaid
            if "->" in line and not re.search(arrow_pattern, line):
                errors.append(f"Invalid arrow syntax on line {i}")
                suggestions.append("Use proper arrow format: 'nodeA --> nodeB'")
            
            # Check for unmatched brackets
            if line.count("[") != line.count("]"):
                errors.append(f"Unmatched brackets on line {i}")
            
            # Check for unmatched parentheses
            if line.count("(") != line.count(")"):
                errors.append(f"Unmatched parentheses on line {i}")
            
            # More permissive character check for node names
            if re.search(r'[^\w\s\-\[\]\(\){}"\'<>:;,.|=]+', line):
                errors.append(f"Invalid characters on line {i}")
                suggestions.append("Use alphanumeric characters and common symbols in diagram elements")
        
        return ValidationResult(len(errors) == 0, errors, suggestions)

    @staticmethod
    def validate_plantuml(code: str) -> ValidationResult:
        """Validate PlantUML diagram syntax.
        
        Args:
            code: PlantUML diagram code
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        suggestions = []
        
        # Basic structure validation
        if not code.strip():
            errors.append("Diagram code is empty")
            return ValidationResult(False, errors, suggestions)
        
        # Normalize whitespace and split into lines
        code = code.strip()
        lines = [line.strip() for line in code.split("\n") if line.strip()]
        if not lines:
            errors.append("Diagram code is empty after whitespace normalization")
            return ValidationResult(False, errors, suggestions)
        
        # Check for matching start/end tags
        start_tag = None
        for line in lines:
            if line.startswith('@start'):
                start_tag = line.split()[0][1:]  # Remove @ and get tag name
                break
                
        if not start_tag:
            errors.append("Missing @start tag")
            suggestions.append("Add @startuml at the beginning of the diagram")
            return ValidationResult(False, errors, suggestions)
            
        # Check for corresponding end tag
        has_matching_end = False
        for line in reversed(lines):
            if line.startswith(f'@end{start_tag[5:]}'):  # Match the type (e.g., uml, mindmap)
                has_matching_end = True
                break
                
        if not has_matching_end:
            errors.append("Missing or mismatched @end tag")
            suggestions.append(f"Add {f'@end{start_tag[5:]}' } at the end of the diagram")
            return ValidationResult(False, errors, suggestions)

        # Define valid characters for elements and specific syntax patterns
        element_chars = r'[A-Za-z0-9_\-\s\[\]\(\){}"\'<>:;,.|=+*#@]'
        arrow_pattern = r'[A-Za-z0-9_\-\s]+\s*-+>+\s*[A-Za-z0-9_\-\s]+'
        
        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('@'):
                continue
                
            # Check arrow syntax
            if "->" in line and not re.match(arrow_pattern, line):
                errors.append(f"Invalid arrow syntax on line {i}")
                suggestions.append("Use proper arrow format: 'A -> B'")
            
            # Check for unmatched quotes
            if line.count('"') % 2 != 0:
                errors.append(f"Unmatched quotes on line {i}")
            
            # Check for invalid characters
            if re.search(r'[^\w\s\-\[\]\(\){}"\'<>:;,.|=+*#@]', line):
                errors.append(f"Invalid characters on line {i}")
                suggestions.append("Use alphanumeric characters and common symbols in diagram elements")
            
            # Check for invalid arrow syntax combinations
            if ">->" in line or "<-<" in line:
                errors.append(f"Invalid arrow syntax on line {i}")
                suggestions.append("Use standard arrow formats like '->', '<-', '-->', or '<--'")
        
        return ValidationResult(len(errors) == 0, errors, suggestions)

    @classmethod
    def validate(cls, code: str, diagram_type: Optional[DiagramType] = None) -> ValidationResult:
        """Validate diagram syntax.
        
        Args:
            code: Diagram code to validate
            diagram_type: Optional diagram type (auto-detected if not provided)
            
        Returns:
            ValidationResult with validation details
        """
        try:
            # Handle string diagram type input
            if isinstance(diagram_type, str):
                diagram_type = DiagramType(diagram_type.lower())
            elif not diagram_type:
                detected_type = cls.detect_type(code)
                if not detected_type:
                    return ValidationResult(
                        False, 
                        ["Unable to determine diagram type"], 
                        ["Specify diagram type explicitly or ensure code starts with proper syntax"]
                    )
                diagram_type = detected_type
                
            if diagram_type == DiagramType.MERMAID:
                return cls.validate_mermaid(code)
            elif diagram_type == DiagramType.PLANTUML:
                return cls.validate_plantuml(code)
            else:
                return ValidationResult(
                    False,
                    [f"Unsupported diagram type: {diagram_type}"],
                    ["Use either Mermaid or PlantUML syntax"]
                )
        except ValueError:
            return ValidationResult(
                False,
                [f"Invalid diagram type: {diagram_type}"],
                ["Use 'mermaid' or 'plantuml' as diagram type"]
            )
