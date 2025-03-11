"""Tests for main FastAPI application."""

from fastapi.testclient import TestClient

from diagram_generator.backend.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint returns expected response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "version": app.version
    }
