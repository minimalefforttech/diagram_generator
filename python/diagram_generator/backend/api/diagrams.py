"""API routes for diagram generation and management."""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from typing import List

class ModelInfo(BaseModel):
    """Model for LLM model information."""
    id: str
    name: str
    provider: str = "ollama"

from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.models.configs import DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.services.ollama import OllamaService
from diagram_generator.backend.storage.database import Storage, ConversationRecord, ConversationMessage
from .logs import LogEntry, log_service

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

router = APIRouter(prefix="/diagrams", tags=["diagrams"])
ollama_service = OllamaService()
diagram_generator = DiagramGenerator(ollama_service)
storage = Storage()
logger = logging.getLogger(__name__)

def log_error(message: str, details: Any = None) -> None:
    """Helper function to log errors."""
    log_service.add_entry("error", message, details)

def log_llm(message: str, details: Any = None) -> None:
    """Helper function to log LLM interactions."""
    log_service.add_entry("llm", message, details)

def _conversation_to_response(conversation: ConversationRecord) -> ConversationResponse:
    """Convert ConversationRecord to ConversationResponse."""
    return ConversationResponse(
        id=conversation.id,
        diagram_id=conversation.diagram_id,
        messages=[{
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
            "metadata": m.metadata
        } for m in conversation.messages],
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        metadata=conversation.metadata
    )

@router.post("/conversations")
async def create_conversation(request: ConversationCreateRequest) -> ConversationResponse:
    """Create a new conversation."""
    try:
        conversation_id = str(uuid.uuid4())
        conversation = ConversationRecord(
            id=conversation_id,
            diagram_id=request.diagram_id,
            messages=[ConversationMessage(role="user", content=request.message, timestamp=datetime.now())],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )
        storage.save_conversation(conversation)
        return _conversation_to_response(conversation)
    except Exception as e:
        error_msg = f"Failed to create conversation: {str(e)}"
        log_error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """Retrieve a conversation by ID."""
    try:
        conversation = storage.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return _conversation_to_response(conversation)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to retrieve conversation: {str(e)}"
        log_error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict:
    """Delete a conversation by ID."""
    try:
        result = storage.delete_conversation(conversation_id)
        if result is False:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": f"Conversation {conversation_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to delete conversation: {str(e)}"
        log_error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/conversations")
async def list_conversations(diagram_id: str) -> List[ConversationResponse]:
    """List conversations for a diagram."""
    try:
        conversations = storage.list_conversations(diagram_id)
        return [_conversation_to_response(conv) for conv in conversations]
    except Exception as e:
        error_msg = f"Failed to list conversations: {str(e)}"
        log_error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/conversations/{conversation_id}/continue")
async def continue_conversation(
    conversation_id: str,
    request: ContinueConversationRequest
) -> ConversationResponse:
    """Continue an existing conversation."""
    try:
        # Get existing conversation
        conversation = storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Add new message
        conversation.messages.append(
            ConversationMessage(
                role="user",
                content=request.message,
                timestamp=datetime.now(),
                metadata={}
            )
        )
        conversation.updated_at = datetime.now()

        # Save updated conversation
        storage.update_conversation(conversation)
        return _conversation_to_response(conversation)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to continue conversation: {str(e)}"
        log_error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

class GenerateDiagramRequest(BaseModel):
    """Request model for generating a diagram."""
    description: str
    type: Optional[str] = "mermaid"
    model: Optional[str] = None  # If not provided, use service default
    options: Optional[Dict] = None

@router.post("/generate")
async def generate_diagram(request: GenerateDiagramRequest) -> Dict:
    """Generate a diagram from a text description."""
    try:
        # Prepare generation options
        generation_options = request.options or {}
        
        # Log model being used
        log_llm("Selected model", {
            "model": request.model or ollama_service.model
        })
        
        # Set model if provided, otherwise use default
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
            "type": request.type,
            "model": request.model or ollama_service.model,
            "options": generation_options
        })

        # Generate the diagram
        code, notes = await diagram_generator.generate_diagram(
            description=request.description,
            diagram_type=request.type,
            options=generation_options
        )
        
        # Clean up the diagram code
        cleaned_code = code.strip()
        if "```mermaid" in cleaned_code:
            try:
                cleaned_code = cleaned_code.split("```mermaid")[1].split("```")[0].strip()
            except IndexError:
                pass
        
        # Normalize the code
        if "\n" in cleaned_code:
            lines = cleaned_code.splitlines()
            min_indent = float('inf')
            for line in lines:
                if line.strip():
                    min_indent = min(min_indent, len(line) - len(line.lstrip()))
            min_indent = 0 if min_indent == float('inf') else min_indent
            cleaned_code = "\n".join(line[min_indent:].rstrip() for line in lines)

        # Log successful generation
        log_llm("Generated diagram successfully", {
            "code": cleaned_code,
            "notes": notes
        })
            
        return {
            "code": cleaned_code,
            "type": request.type,
            "notes": [note for note in notes if note != "Failed to parse JSON response"]
        }
    except Exception as e:
        error_msg = f"Failed to generate diagram: {str(e)}"
        log_error(error_msg, {
            "error": str(e),
            "description": request.description,
            "diagram_type": request.type,
            "options": generation_options
        })
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/models")
async def get_available_models() -> List[ModelInfo]:
    """Get list of available LLM models."""
    try:
        # Currently only supporting Ollama models
        raw_models = ollama_service.get_available_models()
        
        # Extract model names and create unique model entries
        models = []
        seen_names = set()
        
        for model_info in raw_models:
            model_name = model_info.get("name", "")
            tag = model_info.get("tag", "latest")
            
            # Format model identifier
            model_id = model_info["id"]
            
            # Skip duplicates and empty names
            if not model_name or model_id in seen_names:
                continue
            
            seen_names.add(model_id)
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_name,
                    provider="ollama"
                )
            )
        
        if not models:
            # Provide a default model if none are found
            models.append(
                ModelInfo(
                    id=ollama_service.model,
                    name=ollama_service.model,
                    provider="ollama"
                )
            )
        
        return models
    except Exception as e:
        error_msg = f"Failed to get available models: {str(e)}"
        log_error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/validate")
async def validate_diagram(
    code: str,
    diagram_type: str = "mermaid"
) -> Dict:
    """Validate diagram syntax."""
    try:
        result = await diagram_generator.validate_diagram(code, diagram_type)
        log_llm("Validated diagram", {
            "code": code,
            "type": diagram_type,
            "result": result
        })
        return result
    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        log_error(error_msg, {
            "error": str(e),
            "code": code,
            "type": diagram_type
        })
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/convert")
async def convert_diagram(
    diagram: str,
    source_type: str = Query(..., description="Source diagram type"),
    target_type: str = Query(..., description="Target diagram type"),
    model: Optional[str] = None
) -> Dict:
    """Convert diagram between different formats.
    
    Args:
        diagram: Source diagram to convert
        source_type: Original diagram format
        target_type: Target diagram format
        model: Optional model override for conversion
    """
    try:
        log_llm("Converting diagram", {
            "source_type": source_type,
            "target_type": target_type,
            "diagram": diagram
        })

        # Log model being used
        using_model = model or ollama_service.model
        log_llm("Using model for conversion", {"model": using_model})

        # Prepare options with model if provided
        options = {"model": model} if model else None

        code, notes = await diagram_generator.convert_diagram(
            diagram=diagram,
            source_type=source_type,
            target_type=target_type,
            options=options
        )

        log_llm("Converted diagram successfully", {
            "code": code,
            "notes": notes
        })

        return {
            "diagram": code,
            "source_type": source_type,
            "target_type": target_type,
            "notes": notes
        }
    except Exception as e:
        error_msg = f"Conversion failed: {str(e)}"
        log_error(error_msg, {
            "error": str(e),
            "diagram": diagram,
            "source_type": source_type,
            "target_type": target_type
        })
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
