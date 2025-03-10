"""Tests for diagram API endpoints."""

import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_generate_diagram_success():
    """Test successful diagram generation endpoint."""
    test_mermaid = """
    graph TD
        A[Start] --> B[End]
    """
    
    with patch('backend.api.diagrams.diagram_generator.generate_diagram') as mock_generate:
        mock_generate.return_value = (test_mermaid, [])
        
        response = client.post(
            "/diagrams/generate",
            params={
                "description": "Create a simple flowchart",
                "diagram_type": "mermaid"
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {
            "diagram": test_mermaid,
            "type": "mermaid",
            "notes": []
        }

def test_generate_diagram_failure():
    """Test diagram generation endpoint with error."""
    with patch('backend.api.diagrams.diagram_generator.generate_diagram') as mock_generate:
        mock_generate.side_effect = Exception("Generation failed")
        
        response = client.post(
            "/diagrams/generate",
            params={
                "description": "Create a simple flowchart",
                "diagram_type": "mermaid"
            }
        )
        
        assert response.status_code == 500
        assert "Generation failed" in response.json()["detail"]

def test_validate_diagram_valid():
    """Test diagram validation endpoint with valid input."""
    valid_mermaid = """
    graph TD
        A[Start] --> B[End]
    """
    
    validation_result = {
        "valid": True,
        "errors": [],
        "suggestions": ["Consider adding more detail"]
    }
    
    with patch('backend.api.diagrams.diagram_generator.validate_diagram') as mock_validate:
        mock_validate.return_value = validation_result
        
        response = client.post(
            "/diagrams/validate",
            params={
                "code": valid_mermaid,
                "diagram_type": "mermaid"
            }
        )
        
        assert response.status_code == 200
        assert response.json() == validation_result

def test_validate_diagram_invalid():
    """Test diagram validation endpoint with invalid input."""
    invalid_mermaid = "graph TD A-->B[Missing bracket"
    
    validation_result = {
        "valid": False,
        "errors": ["Missing closing bracket"],
        "suggestions": ["Add closing bracket"]
    }
    
    with patch('backend.api.diagrams.diagram_generator.validate_diagram') as mock_validate:
        mock_validate.return_value = validation_result
        
        response = client.post(
            "/diagrams/validate",
            params={
                "code": invalid_mermaid,
                "diagram_type": "mermaid"
            }
        )
        
        assert response.status_code == 200
        assert not response.json()["valid"]
        assert "Missing closing bracket" in response.json()["errors"]

def test_convert_diagram_success():
    """Test successful diagram conversion endpoint."""
    mermaid_diagram = """
    graph TD
        A[Start] --> B[End]
    """
    
    plantuml_diagram = """
    @startuml
    [Start] --> [End]
    @enduml
    """
    
    with patch('backend.api.diagrams.diagram_generator.convert_diagram') as mock_convert:
        mock_convert.return_value = (plantuml_diagram, [])
        
        response = client.post(
            "/diagrams/convert",
            params={
                "diagram": mermaid_diagram,
                "source_type": "mermaid",
                "target_type": "plantuml"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["diagram"] == plantuml_diagram
        assert result["source_type"] == "mermaid"
        assert result["target_type"] == "plantuml"
        assert not result["notes"]

def test_convert_diagram_failure():
    """Test diagram conversion endpoint with error."""
    mermaid_diagram = """
    graph TD
        A[Start] --> B[End]
    """
    
    with patch('backend.api.diagrams.diagram_generator.convert_diagram') as mock_convert:
        mock_convert.side_effect = Exception("Conversion failed")
        
        response = client.post(
            "/diagrams/convert",
            params={
                "diagram": mermaid_diagram,
                "source_type": "mermaid",
                "target_type": "plantuml"
            }
        )
        
        assert response.status_code == 500
        assert "Conversion failed" in response.json()["detail"]
