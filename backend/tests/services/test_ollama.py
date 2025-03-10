"""Tests for Ollama service."""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from backend.services.ollama import OllamaService

@pytest.fixture
def ollama_service():
    """Create OllamaService instance for testing."""
    return OllamaService(model="llama2:13b")

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = Mock()
    mock.status_code = 200
    return mock

def test_health_check_success(ollama_service, mock_response):
    """Test health check with successful response."""
    with patch.object(ollama_service.session, 'get', return_value=mock_response) as mock_get:
        assert ollama_service.health_check() is True
        mock_get.assert_called_once_with(f"{ollama_service.base_url}/api/version")

def test_health_check_failure(ollama_service):
    """Test health check with failed response."""
    with patch.object(ollama_service.session, 'get', side_effect=requests.RequestException):
        assert ollama_service.health_check() is False

def test_get_available_models(ollama_service, mock_response):
    """Test getting available models."""
    mock_response.json.return_value = {"models": [{"name": "model1"}, {"name": "model2"}]}
    
    with patch.object(ollama_service.session, 'get', return_value=mock_response) as mock_get:
        models = ollama_service.get_available_models()
        assert len(models) == 2
        assert models[0]["name"] == "model1"
        mock_get.assert_called_once_with(f"{ollama_service.base_url}/api/tags")

def test_generate_completion(ollama_service, mock_response):
    """Test generating completion."""
    expected_response = {
        "model": "llama2:13b",
        "response": "Test response",
        "done": True
    }
    mock_response.json.return_value = expected_response
    
    with patch.object(ollama_service.session, 'post', return_value=mock_response) as mock_post:
        response = ollama_service.generate_completion("Test prompt")
        assert response == expected_response
        mock_post.assert_called_once()

def test_generate_completion_with_system_prompt(ollama_service, mock_response):
    """Test generating completion with system prompt."""
    expected_response = {
        "model": "llama2:13b",
        "response": "Test response",
        "done": True
    }
    mock_response.json.return_value = expected_response
    
    with patch.object(ollama_service.session, 'post', return_value=mock_response) as mock_post:
        response = ollama_service.generate_completion(
            "Test prompt",
            system_prompt="System prompt"
        )
        assert response == expected_response
        
        # Verify system prompt was included in payload
        call_args = mock_post.call_args
        assert "system" in call_args[1]["json"]
        assert call_args[1]["json"]["system"] == "System prompt"

def test_validate_response_basic(ollama_service):
    """Test basic response validation."""
    valid_response = {"response": "test"}
    invalid_response = {"error": "test"}
    
    assert ollama_service.validate_response(valid_response) is True
    assert ollama_service.validate_response(invalid_response) is False

def test_validate_response_with_format(ollama_service):
    """Test response validation with format specification."""
    expected_format = {
        "type": str,
        "data": {
            "value": int
        }
    }
    
    valid_json = json.dumps({
        "type": "test",
        "data": {
            "value": 42
        }
    })
    
    invalid_json = json.dumps({
        "type": "test",
        "data": {
            "value": "not an int"
        }
    })
    
    assert ollama_service.validate_response(
        {"response": valid_json},
        expected_format
    ) is True
    
    assert ollama_service.validate_response(
        {"response": invalid_json},
        expected_format
    ) is False

def test_validate_response_with_invalid_json(ollama_service):
    """Test response validation with invalid JSON."""
    expected_format = {"key": str}
    
    assert ollama_service.validate_response(
        {"response": "not json"},
        expected_format
    ) is False
