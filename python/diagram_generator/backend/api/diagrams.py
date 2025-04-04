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

from diagram_generator.backend.storage.database import Storage, ConversationRecord, ConversationMessage, DiagramRecord
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
    description: Optional[str] = None  # Optional user-provided description
    prompt: str  # Original prompt used to generate diagram
    syntax: str
    createdAt: str
    iterations: Optional[int] = None

class DiagramResponse(BaseModel):
    """Response model for a diagram."""
    id: str
    code: str
    type: str
    subtype: Optional[str] = None
    description: Optional[str] = None  # Optional user-provided description
    prompt: str  # Original prompt used to generate diagram
    createdAt: str
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[List[str]] = None

router = APIRouter(prefix="/diagrams", tags=["diagrams"])

class GenerateDiagramRequest(BaseModel):
    """Request model for generating a diagram."""
    description: Optional[str] = None  # Optional user-provided description
    prompt: str  # The diagram prompt/description
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
            "prompt": request.prompt,
            "type": diagram_type.value,
            "subtype": diagram_subtype.value,
            "model": request.model or ollama_service.model,
            "options": generation_options
        })

        # Add subtype to prompt if not auto
        prompt = request.prompt
        if diagram_subtype != DiagramSubType.AUTO:
            prompt = f"Create a {diagram_subtype.value} diagram: {prompt}"

        # Generate the diagram and get agent output
        result = await diagram_generator.generate_diagram(
            description=prompt,
            diagram_type=diagram_type.value,
            options=generation_options
        )

        # Log success/failure
        if result.code and result.valid:
            # Create and save the diagram record if generation was successful
            diagram = DiagramRecord(
                id=result.diagram_id,
                description=request.description or request.prompt,
                diagram_type=diagram_type.value,
                code=result.code,
                created_at=datetime.now(),
                metadata={
                    "description": request.description,
                    "prompt": request.prompt,
                    "iterations": result.iterations,
                    "valid": result.valid
                }
            )
            storage.save_diagram(diagram)

            log_llm("Generation successful", {
                "diagram_type": diagram_type.value,
                "code": result.code,
                "notes": result.notes,
                "iterations": result.iterations,
                "diagram_id": result.diagram_id,
                "conversation_id": result.conversation_id
            })
        else:
            log_error("Failed to generate valid diagram", {
                "diagram_type": diagram_type.value,
                "code": result.code,
                "notes": result.notes,
                "iterations": result.iterations,
                "valid": result.valid
            })
        
        return {
            "code": result.code,
            "type": diagram_type.value,
            "subtype": diagram_subtype.value,
            "description": request.description,
            "prompt": request.prompt,
            "notes": result.notes,
            "iterations": result.iterations,
            "valid": result.valid,
            "diagram_id": result.diagram_id,
            "conversation_id": result.conversation_id
        }

    except Exception as e:
        error_msg = f"Failed to generate diagram: {str(e)}"
        log_error(error_msg, {
            "error": str(e),
            "description": request.description,
            "prompt": request.prompt,
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
    try:
        # Get available types from enum
        syntax_types = DiagramType.to_list()
        types = {}
        
        # Get subtypes for each syntax type
        for syntax in syntax_types:
            syntax_enum = DiagramType.from_string(syntax)
            if syntax_enum:
                subtypes = [t.value.replace('plantuml_', '') for t in DiagramSubType.for_syntax(syntax_enum)]
                types[syntax] = subtypes
        
        return {
            "syntax": syntax_types,
            "types": types
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get syntax types: {str(e)}"
        )

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
            
            # Get description and prompt from metadata or fallback to description field
            metadata = diagram.metadata or {}
            description = metadata.get("description")
            prompt = metadata.get("prompt", diagram.description)
            
            history_items.append(DiagramHistoryItem(
                id=diagram.id,
                description=description,
                prompt=prompt[:100] + ("..." if len(prompt) > 100 else ""),
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

@router.post("/diagram/{diagram_id}/update")
async def update_diagram(
    diagram_id: str,
    request: GenerateDiagramRequest
) -> DiagramResponse:
    """Update an existing diagram."""
    try:
        diagram = storage.get_diagram(diagram_id)
        
        if not diagram:
            raise HTTPException(
                status_code=404,
                detail=f"Diagram with ID {diagram_id} not found"
            )

        # Convert input types to proper enums
        diagram_type = DiagramType.from_string(request.syntax_type or diagram.diagram_type)
        diagram_subtype = DiagramSubType.from_string(request.subtype or "auto")
        
        # Prepare generation options
        generation_options = request.options or {}
        if request.model:
            generation_options["model"] = request.model

        # Configure agent options if not provided
        if "agent" not in generation_options:
            generation_options["agent"] = {
                "enabled": True,
                "max_iterations": 3
            }

        # Use the update_diagram method instead of generate_diagram
        result = await diagram_generator.update_diagram(
            diagram_code=diagram.code,
            update_notes=request.prompt,
            diagram_type=diagram_type.value,
            options=generation_options
        )
        
        # Update the diagram and save it back with metadata
        diagram.code = result.code
        diagram.description = request.prompt
        diagram.metadata = {
            **(diagram.metadata or {}),
            "description": request.description,
            "prompt": request.prompt,
            "iterations": result.iterations,
            "valid": result.valid
        }
        storage.save_diagram(diagram)

        return DiagramResponse(
            id=diagram.id,
            code=result.code,
            type=diagram_type.value,
            description=request.description,
            prompt=request.prompt,
            createdAt=diagram.created_at.isoformat(),
            metadata=diagram.metadata,
            notes=result.notes
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to update diagram: {str(e)}"
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
            
        # Get metadata
        metadata = diagram.metadata or {}
        description = metadata.get("description")
        prompt = metadata.get("prompt", diagram.description)
        
        return DiagramResponse(
            id=diagram.id,
            code=diagram.code,
            type=diagram.diagram_type,
            description=description,
            prompt=prompt,
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

@router.delete("/diagram/{diagram_id}")
async def delete_diagram(diagram_id: str) -> Dict[str, str]:
    """Delete a specific diagram by ID."""
    try:
        diagram = storage.get_diagram(diagram_id)
        
        if not diagram:
            raise HTTPException(
                status_code=404,
                detail=f"Diagram with ID {diagram_id} not found"
            )
            
        storage.delete_diagram(diagram_id)
        return {"status": "success", "message": f"Diagram {diagram_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to delete diagram: {str(e)}"
        log_error(error_msg)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.delete("/clear")
async def clear_history() -> Dict[str, str]:
    """Clear all diagram history."""
    try:
        # Log the clear request
        log_llm("Clearing all diagram history")
        
        # Get initial count to report how many were deleted
        initial_count = len(storage.get_all_diagrams())
        
        # Clear all diagrams
        storage.clear_diagrams()
        
        # Log success
        log_llm("Successfully cleared diagram history", {"deleted_count": initial_count})
        
        return {
            "status": "success", 
            "message": f"All diagrams deleted successfully ({initial_count} diagrams)",
            "state": {
                "diagrams_deleted": initial_count,
                "success": True
            }
        }
    except Exception as e:
        error_msg = f"Failed to clear diagram history: {str(e)}"
        log_error(error_msg)
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": error_msg,
            "state": {
                "success": False,
                "error": str(e)
            }
        }
