"""Service for interacting with Ollama API."""

import logging
import requests
from typing import Dict, List, Optional, Any, Union
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:latest",
        cache_expire_after: int = 3600,
    ):
        self.base_url = base_url
        self.model = model
        self.cache_expire_after = cache_expire_after

        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = self.session.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama.
        
        Returns:
            List of model information dictionaries
        
        Raises:
            requests.RequestException: If API call fails
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            # Transform the response to match our expected format
            formatted_models = []
            for model_info in models:
                model_name = model_info.get("name", "")
                    
                formatted_models.append({
                    "id": model_info.get("name", model_name),  # Use name as ID
                    "name": model_name,
                    "provider": "ollama",
                    "size": model_info.get("size", 0),
                    "digest": model_info.get("digest", "")
                })
            
            return formatted_models
            
        except requests.RequestException as e:
            # Return default model if we can't fetch the list
            logger.error(f"Failed to fetch models: {e}")
            return [{
                "id": self.model,
                "name": self.model,
                "provider": "ollama",
                "size": 0,
                "digest": ""
            }]

    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate a completion using the Ollama API.
        
        Args:
            prompt: The prompt to generate from
            model: Optional model override
            system_prompt: Optional system prompt
            temperature: Model temperature (0.0 to 1.0)
            
        Returns:
            Response from Ollama API
            
        Raises:
            requests.RequestException: If API call fails
        """
        try:
            request_data = {
                "model": model or self.model,
                "prompt": prompt,
                "system": system_prompt,
                "options": {
                    "temperature": temperature,
                }
            }
            # Clean up None values
            if not request_data["system"]:
                del request_data["system"]
                
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=request_data
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            error_msg = f"Failed to generate completion: {str(e)}"
            logger.error(error_msg)
            raise
