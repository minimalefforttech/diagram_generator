"""Ollama service for LLM integration."""

import json
from typing import Any, Dict, List, Optional

import requests
from requests_cache import CachedSession

class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        cache_expire_after: int = 3600,
    ):
        """Initialize OllamaService.
        
        Args:
            base_url: Base URL for Ollama API
            model: Default model to use
            cache_expire_after: Cache expiration in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        
        # Setup cached session for API calls
        self.session = CachedSession(
            cache_name='ollama_cache',
            backend='sqlite',
            expire_after=cache_expire_after
        )

    def health_check(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/version")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama.
        
        Returns:
            List of model information dictionaries
        
        Raises:
            requests.RequestException: If API call fails
        """
        response = self.session.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])

    def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate a completion from Ollama.
        
        Args:
            prompt: The prompt to generate from
            model: Optional model override
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
        
        Returns:
            Dictionary containing the completion and metadata
        
        Raises:
            requests.RequestException: If API call fails
        """
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        response = self.session.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        return response.json()

    def validate_response(
        self,
        response: Dict[str, Any],
        expected_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate an LLM response against expected format.
        
        Args:
            response: The response to validate
            expected_format: Optional expected format specification
        
        Returns:
            Dict: Parsed and validated response
        """
        try:
            if not isinstance(response, dict):
                raise ValueError("Response must be a dictionary")
                
            # Basic validation
            if "response" not in response:
                raise ValueError("Response missing 'response' field")
                
            # Format validation if specified
            if expected_format:
                try:
                    parsed = json.loads(response["response"])
                    if not self._validate_against_format(parsed, expected_format):
                        raise ValueError("Response format validation failed")
                    return parsed
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse JSON response")
                    
            return response
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "suggestions": []
            }
            
    def _validate_against_format(
        self,
        data: Any,
        format_spec: Any
    ) -> bool:
        """Recursively validate data against a format specification."""
        if isinstance(format_spec, dict):
            if not isinstance(data, dict):
                return False
            return all(
                k in data and self._validate_against_format(data[k], v)
                for k, v in format_spec.items()
            )
        elif isinstance(format_spec, list):
            if not isinstance(data, list):
                return False
            return all(
                self._validate_against_format(item, format_spec[0])
                for item in data
            ) if format_spec else True
        else:
            return isinstance(data, format_spec)
