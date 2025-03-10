"""Core diagram generation and validation logic."""

from typing import Dict, List, Optional, Tuple

from backend.services.ollama import OllamaService

class DiagramGenerator:
    """Handles generation and validation of diagrams."""

    def __init__(self, llm_service: OllamaService):
        """Initialize DiagramGenerator.
        
        Args:
            llm_service: LLM service for diagram generation
        """
        self.llm_service = llm_service
        
        # System prompts for different operations
        self.prompts = {
            "generate": """You are a diagram expert. Convert the following description into 
a valid diagram using {type} syntax. Respond ONLY with the diagram code without explanations or markdown:

Description: {description}
""",
            "validate": """You are a {type} syntax validator. Check if the following diagram 
code is valid and return a JSON response with format:
{{
    "valid": boolean,
    "errors": string[],
    "suggestions": string[]
}}

Code to validate:
{code}
""",
            "convert": """You are a diagram conversion expert. Convert the following {source_type} 
diagram into a valid {target_type} diagram while preserving the semantics:

Source diagram:
{diagram}
"""
        }

    async def generate_diagram(
        self,
        description: str,
        diagram_type: str = "mermaid",
        options: Optional[Dict] = None
    ) -> Tuple[str, List[str]]:
        """Generate a diagram from a description.
        
        Args:
            description: Text description of desired diagram
            diagram_type: Target diagram syntax type
            options: Optional generation parameters
        
        Returns:
            Tuple of (diagram code, list of notes/warnings)
        """
        prompt = self.prompts["generate"].format(
            type=diagram_type,
            description=description
        )
        
        response = self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.2  # Lower temperature for more consistent output
        )
        
        # Extract diagram code and any warnings
        raw_response = response["response"]
        code = raw_response
        notes = []

        # Try to extract diagram code from markdown blocks
        if "```mermaid" in raw_response:
            try:
                code = raw_response.split("```mermaid")[1].split("```")[0].strip()
            except IndexError:
                notes.append("Failed to extract diagram code from markdown")
        
        try:
            # Validate the generated diagram
            validation = await self.validate_diagram(code, diagram_type)
            if isinstance(validation, dict) and not validation.get("valid", False):
                notes.extend(validation.get("errors", []))
        except Exception as e:
            notes.append(f"Validation warning: {str(e)}")
        
        return code, notes

    async def validate_diagram(
        self,
        code: str,
        diagram_type: str = "mermaid"
    ) -> Dict:
        """Validate diagram syntax.
        
        Args:
            code: Diagram code to validate
            diagram_type: Type of diagram syntax
        
        Returns:
            Dictionary containing validation results
        """
        prompt = self.prompts["validate"].format(
            type=diagram_type,
            code=code
        )
        
        response = self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.1  # Very low temperature for consistent validation
        )
        
        try:
            # Expect JSON response from validation prompt
            return self.llm_service.validate_response(
                response,
                expected_format={
                    "valid": bool,
                    "errors": List[str],
                    "suggestions": List[str]
                }
            )
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "suggestions": []
            }

    async def convert_diagram(
        self,
        diagram: str,
        source_type: str,
        target_type: str
    ) -> Tuple[str, List[str]]:
        """Convert diagram between different syntax types.
        
        Args:
            diagram: Source diagram code
            source_type: Source diagram syntax type
            target_type: Target diagram syntax type
        
        Returns:
            Tuple of (converted diagram code, list of notes/warnings)
        """
        prompt = self.prompts["convert"].format(
            source_type=source_type,
            target_type=target_type,
            diagram=diagram
        )
        
        response = self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.3
        )
        
        code = response["response"]
        notes = []
        
        try:
            # Validate the converted diagram
            validation = await self.validate_diagram(code, target_type)
            if isinstance(validation, dict) and not validation.get("valid", False):
                notes.extend(validation.get("errors", []))
        except Exception as e:
            notes.append(f"Validation warning: {str(e)}")
            
        return code, notes
