"""API routes for Ollama service."""

from typing import Dict, List

from fastapi import APIRouter, HTTPException

from diagram_generator.backend.services.ollama import OllamaService

router = APIRouter(prefix="/ollama", tags=["ollama"])
ollama_service = OllamaService(model="llama3.1:8b")

@router.get("/health")
async def check_ollama_health() -> Dict[str, bool]:
    """Check if Ollama service is available."""
    if ollama_service.health_check():
        return {"status": True}
    raise HTTPException(
        status_code=503,
        detail="Ollama service is not available"
    )

@router.get("/models")
async def list_models() -> List[Dict]:
    """Get list of available models."""
    try:
        return ollama_service.get_available_models()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get models: {str(e)}"
        )

@router.post("/generate")
async def generate_completion(
    prompt: str,
    model: str = None,
    system_prompt: str = None,
    temperature: float = 0.7
) -> Dict:
    """Generate completion from Ollama."""
    try:
        return ollama_service.generate_completion(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
