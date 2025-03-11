"""API routes for diagram generation and management."""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.models.configs import DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.services.ollama import OllamaService
from diagram_generator.backend.storage.database import Storage, ConversationRecord, ConversationMessage

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )

@router.get("/conversations")
async def list_conversations(diagram_id: str) -> List[ConversationResponse]:
    """List conversations for a diagram."""
    try:
        conversations = storage.list_conversations(diagram_id)
        return [_conversation_to_response(conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to continue conversation: {str(e)}"
        )

@router.post("/generate")
async def generate_diagram(
    description: str,
    diagram_type: str = "mermaid",
    options: Optional[Dict] = None,
    use_agent: bool = Query(True, description="Use the agentic system for generation and validation"),
    max_iterations: int = Query(3, description="Maximum iterations for fix attempts"),
    api_docs_dir: Optional[str] = Query(None, description="Directory containing API documentation for RAG")
) -> Dict:
    """Generate a diagram from a text description."""
    try:
        # Prepare generation options
        generation_options = options or {}
        
        # Configure agent options
        if "agent" not in generation_options:
            generation_options["agent"] = {}
        generation_options["agent"]["enabled"] = use_agent
        generation_options["agent"]["max_iterations"] = max_iterations
        
        # Configure RAG if a directory is provided
        if api_docs_dir:
            if os.path.isdir(api_docs_dir):
                if "rag" not in generation_options:
                    generation_options["rag"] = {}
                generation_options["rag"]["enabled"] = True
                generation_options["rag"]["api_doc_dir"] = api_docs_dir
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"API docs directory not found: {api_docs_dir}"
                )
        
        # Generate the diagram
        code, notes = await diagram_generator.generate_diagram(
            description=description,
            diagram_type=diagram_type,
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
    """Validate diagram syntax."""
    try:
        return await diagram_generator.validate_diagram(code, diagram_type)
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
    """Convert diagram between different formats."""
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
