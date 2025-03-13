"""API routes for diagram generation and management."""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
import traceback

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from diagram_generator.backend.utils.diagram_validator import DiagramValidator, ValidationResult, DiagramType, DiagramSubType
from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.models.configs import DiagramGenerationOptions
from diagram_generator.backend.services.ollama import OllamaService
from .logs import log_llm, log_error

from diagram_generator.backend.storage.database import Storage, ConversationRecord, ConversationMessage
from .logs import LogEntry, log_service

# Initialize services
ollama_service = OllamaService()
diagram_generator = DiagramGenerator(llm_service=ollama_service)
storage = Storage()

class ConversationCreateRequest(BaseModel):
    """Request model for creating a new conversation."""
    diagram_id: str
    message: str

class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    diagram_id: str
    messages: List[Dict]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

class ContinueConversationRequest(BaseModel):
    """Request model for continuing a conversation."""
    message: str

class DiagramHistoryItem(BaseModel):
    """Model for diagram history item."""
    id: str
    description: str
    syntax: str
    createdAt: str
    iterations: Optional[int] = None

class DiagramResponse(BaseModel):
    """Response model for a diagram."""
    id: str
    code: str
    type: str
    subtype: Optional[str] = None
    description: str
    createdAt: str
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[List[str]] = None

router = APIRouter(prefix="/diagrams", tags=["diagrams"])

class GenerateDiagramRequest(BaseModel):
    """Request model for generating a diagram."""
    description: str
    syntax_type: Optional[str] = "mermaid"  # High level syntax type (mermaid, plantuml)
    subtype: Optional[str] = "auto"  # Specific diagram type (flowchart, sequence, etc)
    model: Optional[str] = None
    options: Optional[Dict] = None

@router.post("/generate")
async def generate_diagram(request: GenerateDiagramRequest) -> Dict:
    """Generate a diagram from a text description."""
    try:
        # Convert input types to proper enums using their from_string methods
        diagram_type = DiagramType.from_string(request.syntax_type or "mermaid")
        diagram_subtype = DiagramSubType.from_string(request.subtype or "auto")
        
        if not diagram_type:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid syntax type: {request.syntax_type}. Must be one of: {[t.value for t in DiagramType]}"
            )
            
        # Prepare generation options
        generation_options = request.options or {}
        
        # Log model being used
        log_llm("Selected model", {
            "model": request.model or ollama_service.model
        })
        
        # Set model if provided
        if request.model:
            generation_options["model"] = request.model

        # Configure agent options if not provided
        if "agent" not in generation_options:
            generation_options["agent"] = {
                "enabled": True,
                "max_iterations": 3
            }
        
        # Configure RAG if enabled in options
        if generation_options.get("rag", {}).get("enabled", False):
            api_docs_dir = generation_options["rag"].get("api_doc_dir")
            if api_docs_dir and not os.path.isdir(api_docs_dir):
                error_msg = f"API docs directory not found: {api_docs_dir}"
                log_error(error_msg)
                raise HTTPException(status_code=400, detail=error_msg)

        # Log the generation request
        log_llm("Generating diagram", {
            "description": request.description,
            "type": diagram_type.value,
            "subtype": diagram_subtype.value,
            "model": request.model or ollama_service.model,
            "options": generation_options
        })

        # Add subtype to description if not auto
        description = request.description
        if diagram_subtype != DiagramSubType.AUTO:
            description = f"Create a {diagram_subtype.value} diagram: {description}"

        # Generate the diagram
        code, notes = await diagram_generator.generate_diagram(
            description=description,
            diagram_type=diagram_type.value,
            options=generation_options
        )
        
        # Clean up the diagram code
        cleaned_code = code.strip()
        if "```mermaid" in cleaned_code:
            try:
                cleaned_code = cleaned_code.split("```mermaid")[1].split("```")[0].strip()
            except IndexError:
                pass

        # Final cleaning pass to ensure consistent style and no semicolons
        if diagram_type == DiagramType.MERMAID:
            cleaned_code = DiagramValidator._clean_mermaid_code(cleaned_code)
            
        # Log successful generation
        log_llm("Generated diagram successfully", {
            "code": cleaned_code,
            "notes": notes
        })
            
        return {
            "code": cleaned_code,
            "type": diagram_type.value,
            "subtype": diagram_subtype.value,
            "notes": [note for note in notes if note != "Failed to parse JSON response"]
        }

    except Exception as e:
        error_msg = f"Failed to generate diagram: {str(e)}"
        log_error(error_msg, {
            "error": str(e),
            "description": request.description,
            "diagram_type": request.syntax_type,
            "options": generation_options
        })
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/syntax-types")
async def get_syntax_types() -> Dict[str, Any]:
    """Get available diagram syntax types and their subtypes."""
    return {
        "syntax": [t.value for t in DiagramType],
        "types": {
            DiagramType.MERMAID.value: [t.value for t in DiagramSubType if t != DiagramSubType.AUTO],
            DiagramType.PLANTUML.value: ["sequence", "class", "activity", "component", "state", "mindmap", "gantt"]
        }
    }

@router.get("/history")
async def get_diagram_history() -> List[DiagramHistoryItem]:
    """Get the history of all generated diagrams."""
    try:
        diagrams = storage.get_all_diagrams()
        
        # Convert to response model
        history_items = []
        for diagram in diagrams:
            # Get iterations from metadata if available
            iterations = diagram.metadata.get("iterations", 0) if diagram.metadata else 0
            
            history_items.append(DiagramHistoryItem(
                id=diagram.id,
                description=diagram.description[:100] + ("..." if len(diagram.description) > 100 else ""),
                syntax=diagram.diagram_type,
                createdAt=diagram.created_at.isoformat(),
                iterations=iterations
            ))
            
        # Sort by creation date (most recent first)
        history_items.sort(key=lambda x: x.createdAt, reverse=True)
        
        return history_items
    except Exception as e:
        error_msg = f"Failed to get diagram history: {str(e)}"
        log_error(error_msg)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/diagram/{diagram_id}/iterations")
async def get_diagram_iterations(diagram_id: str) -> int:
    """Get the number of iterations for a diagram."""
    try:
        diagram = storage.get_diagram(diagram_id)
        
        if not diagram:
            raise HTTPException(
                status_code=404,
                detail=f"Diagram with ID {diagram_id} not found"
            )
            
        # Get iterations from metadata if available
        metadata = diagram.metadata or {}
        iterations = metadata.get("iterations", 0)
            
        return iterations
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get diagram iterations: {str(e)}"
        log_error(error_msg)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/diagram/{diagram_id}")
async def get_diagram_by_id(diagram_id: str) -> DiagramResponse:
    """Get diagram by ID."""
    try:
        diagram = storage.get_diagram(diagram_id)
        
        if not diagram:
            raise HTTPException(
                status_code=404,
                detail=f"Diagram with ID {diagram_id} not found"
            )
            
        # Get iterations from metadata if available
        metadata = diagram.metadata or {}
        
        return DiagramResponse(
            id=diagram.id,
            code=diagram.code,
            type=diagram.diagram_type,
            description=diagram.description,
            createdAt=diagram.created_at.isoformat(),
            metadata=metadata,
            notes=[]  # Could populate from conversation records if needed
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to get diagram: {str(e)}"
        log_error(error_msg)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
