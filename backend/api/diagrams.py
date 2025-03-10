"""API routes for diagram generation and management."""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.core.diagram_generator import DiagramGenerator
from backend.services.ollama import OllamaService

router = APIRouter(prefix="/diagrams", tags=["diagrams"])
ollama_service = OllamaService()
diagram_generator = DiagramGenerator(ollama_service)

@router.post("/generate")
async def generate_diagram(
    description: str,
    diagram_type: str = "mermaid",
    options: Optional[Dict] = None
) -> Dict:
    """Generate a diagram from a text description.
    
    Args:
        description: Text description of the desired diagram
        diagram_type: Target diagram syntax type (default: mermaid)
        options: Optional generation parameters
    
    Returns:
        Dictionary containing the generated diagram and any notes/warnings
    """
    try:
        code, notes = await diagram_generator.generate_diagram(
            description=description,
            diagram_type=diagram_type,
            options=options
        )
        # Clean up the diagram code and remove any markdown formatting
        cleaned_code = code.strip()
        if "```mermaid" in cleaned_code:
            try:
                cleaned_code = cleaned_code.split("```mermaid")[1].split("```")[0].strip()
            except IndexError:
                pass
                
        # Normalize line endings and indentation
        if "\n" in cleaned_code:
            lines = cleaned_code.splitlines()
            # Find minimum indentation
            min_indent = float('inf')
            for line in lines:
                if line.strip():
                    min_indent = min(min_indent, len(line) - len(line.lstrip()))
            min_indent = 0 if min_indent == float('inf') else min_indent
            # Remove extra indentation and normalize line endings
            cleaned_code = "\n".join(line[min_indent:].rstrip() for line in lines)
            
        return {
            "diagram": cleaned_code,
            "type": diagram_type,
            "notes": [note for note in notes if note != "Failed to parse JSON response"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate diagram: {str(e)}"
        )

@router.post("/validate")
async def validate_diagram(
    code: str,
    diagram_type: str = "mermaid"
) -> Dict:
    """Validate diagram syntax.
    
    Args:
        code: Diagram code to validate
        diagram_type: Type of diagram syntax
    
    Returns:
        Validation results including any errors or suggestions
    """
    try:
        result = await diagram_generator.validate_diagram(
            code=code,
            diagram_type=diagram_type
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/convert")
async def convert_diagram(
    diagram: str,
    source_type: str = Query(..., description="Source diagram type"),
    target_type: str = Query(..., description="Target diagram type")
) -> Dict:
    """Convert diagram between different formats.
    
    Args:
        diagram: Source diagram code
        source_type: Source diagram syntax type
        target_type: Target diagram syntax type
    
    Returns:
        Dictionary containing converted diagram and any notes
    """
    try:
        code, notes = await diagram_generator.convert_diagram(
            diagram=diagram,
            source_type=source_type,
            target_type=target_type
        )
        return {
            "diagram": code,
            "source_type": source_type,
            "target_type": target_type,
            "notes": notes
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )
