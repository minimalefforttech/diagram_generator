"""Tests for Ollama API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from diagram_generator.backend.main import app
from diagram_generator.backend.api.ollama import ollama_service

client = TestClient(app)

def test_ollama_health_check_success():
    """Test Ollama health check endpoint when service is healthy."""
    with patch.object(ollama_service, 'health_check', return_value=True):
        response = client.get("/ollama/health")
        assert response.status_code == 200
        assert response.json() == {"status": True}

def test_ollama_health_check_failure():
    """Test Ollama health check endpoint when service is unhealthy."""
    with patch.object(ollama_service, 'health_check', return_value=False):
        response = client.get("/ollama/health")
        assert response.status_code == 503
        assert response.json() == {"detail": "Ollama service is not available"}

def test_list_models_success():
    """Test listing models endpoint with successful response."""
    test_models = [{"name": "model1"}, {"name": "model2"}]
    with patch.object(ollama_service, 'get_available_models', return_value=test_models):
        response = client.get("/ollama/models")
        assert response.status_code == 200
        assert response.json() == test_models

def test_list_models_failure():
    """Test listing models endpoint when service fails."""
    with patch.object(
        ollama_service,
        'get_available_models',
        side_effect=Exception("Failed to fetch models")
    ):
        response = client.get("/ollama/models")
        assert response.status_code == 500
        assert "Failed to fetch models" in response.json()["detail"]

def test_generate_completion_success():
    """Test generation endpoint with successful response."""
    test_completion = {
        "model": "llama2:13b",
        "response": "Test response",
        "done": True
    }
    with patch.object(ollama_service, 'generate_completion', return_value=test_completion):
        response = client.post(
            "/ollama/generate",
            params={
                "prompt": "Test prompt",
                "model": "llama2:13b",
                "system_prompt": "Test system prompt",
                "temperature": 0.7
            }
        )
        assert response.status_code == 200
        assert response.json() == test_completion

def test_generate_completion_failure():
    """Test generation endpoint when service fails."""
    with patch.object(
        ollama_service,
        'generate_completion',
        side_effect=Exception("Generation failed")
    ):
        response = client.post(
            "/ollama/generate",
            params={
                "prompt": "Test prompt"
            }
        )
        assert response.status_code == 500
        assert "Generation failed" in response.json()["detail"]

def test_generate_completion_missing_prompt():
    """Test generation endpoint with missing prompt."""
    response = client.post("/ollama/generate")
    assert response.status_code == 422  # Unprocessable Entity
