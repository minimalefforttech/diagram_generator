"""Pydantic models for Ollama API interactions."""

import logging
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class OllamaRequest(BaseModel):
    """Base model for Ollama API requests."""
    model: str
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Model parameters like temperature, top_p, etc."
    )
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    format: Optional[str] = None

class OllamaResponse(BaseModel):
    """Base model for Ollama API responses."""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str
    code: Optional[int] = None

class OllamaAPI:
    """Utility class for Ollama API interactions."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint."""
        return f"{self.base_url}/api/{endpoint}"
        
    async def generate(
        self,
        prompt: str,
        model: str = "llama2:13b",  # Default model
        temperature: float = 0.2,
        system: Optional[str] = None
    ) -> Union[OllamaResponse, ErrorResponse]:
        """Generate a response using the Ollama API."""
        try:
            import aiohttp
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "options": {"temperature": temperature},
                "system": system
            }
            # Clean up None values
            request_data = {k: v for k, v in request_data.items() if v is not None}
            request = OllamaRequest(**request_data)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._build_url("generate"),
                    json=request.model_dump(exclude_none=True)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {error_text}")
                        return ErrorResponse(
                            error=f"Ollama API returned {response.status}: {error_text}",
                            code=response.status
                        )
                    
                    result = await response.json()
                    return OllamaResponse(**result)
                    
        except Exception as e:
            logger.exception("Error calling Ollama API")
            return ErrorResponse(error=str(e))

    async def health_check(self) -> bool:
        """Check if Ollama API is available."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(self._build_url("version")) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
