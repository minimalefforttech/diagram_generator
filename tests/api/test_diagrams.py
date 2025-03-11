"""Tests for diagram API endpoints."""

import json
from unittest.mock import Mock, patch
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from diagram_generator.backend.main import app
from diagram_generator.backend.storage.database import ConversationRecord, ConversationMessage

client = TestClient(app)

def test_generate_diagram_success():
    """Test successful diagram generation endpoint."""
    test_mermaid = "graph TD\nA[Start] --> B[End]"
    
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.generate_diagram') as mock_generate:
        mock_generate.return_value = (test_mermaid, [])
        
        response = client.post(
            "/diagrams/generate",
            params={
                "description": "Create a simple flowchart",
                "diagram_type": "mermaid",
                "use_agent": True
            }
        )
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["type"] == "mermaid"
        assert response_json["notes"] == []
        assert response_json["diagram"].strip().replace(" ", "").replace("\n", "") == test_mermaid.strip().replace(" ", "").replace("\n", "")

def test_generate_diagram_with_rag():
    """Test diagram generation with RAG enabled."""
    test_mermaid = "graph TD\nA[Start] --> B[End]"
    
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.generate_diagram') as mock_generate:
        mock_generate.return_value = (test_mermaid, ["Used API docs for context"])
        
        response = client.post(
            "/diagrams/generate",
            params={
                "description": "Create a simple flowchart",
                "diagram_type": "mermaid",
                "use_agent": True,
                "api_docs_dir": "./docs/api"
            }
        )
        
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["type"] == "mermaid"
        assert len(response_json["notes"]) == 1
        assert "API docs" in response_json["notes"][0]

def test_generate_diagram_failure():
    """Test diagram generation endpoint with error."""
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.generate_diagram') as mock_generate:
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
    
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.validate_diagram') as mock_validate:
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
    
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.validate_diagram') as mock_validate:
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
    
    with patch('diagram_generator.backend.api.diagrams.diagram_generator.convert_diagram') as mock_convert:
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

    with patch('diagram_generator.backend.api.diagrams.diagram_generator.convert_diagram') as mock_convert:
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

class TestConversationEndpoints:
    """Tests for conversation API endpoints."""

    def test_create_conversation(self):
        """Test creating a new conversation."""
        with patch('diagram_generator.backend.api.diagrams.storage.save_conversation') as mock_save:
            mock_save.return_value = None
            response = client.post(
                "/diagrams/conversations",
                json={
                    "diagram_id": "test-diagram",
                    "message": "test message"
                }
            )

            assert response.status_code == 200, response.text
            response_json = response.json()
            assert response_json["diagram_id"] == "test-diagram"
            assert len(response_json["messages"]) == 1
            assert response_json["messages"][0]["content"] == "test message"
            mock_save.assert_called_once()

    def test_get_conversation(self):
        """Test retrieving a conversation."""
        test_time = datetime(2025, 3, 11, 14, 47, 55, 399110)
        conversation = ConversationRecord(
            id="test-conv",
            diagram_id="test-diagram",
            messages=[ConversationMessage(role="user", content="test message", timestamp=test_time, metadata={})],
            created_at=test_time,
            updated_at=test_time,
            metadata={}
        )

        with patch('diagram_generator.backend.api.diagrams.storage.get_conversation') as mock_get:
            mock_get.return_value = conversation

            response = client.get("/diagrams/conversations/test-conv")

            assert response.status_code == 200, response.text
            response_json = response.json()
            assert response_json["id"] == "test-conv"
            assert response_json["diagram_id"] == "test-diagram"
            assert len(response_json["messages"]) == 1
            assert response_json["messages"][0]["content"] == "test message"
            mock_get.assert_called_once_with("test-conv")

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        with patch('diagram_generator.backend.api.diagrams.storage.delete_conversation') as mock_delete:
            mock_delete.return_value = True

            response = client.delete("/diagrams/conversations/test-conv")

            assert response.status_code == 200, response.text
            assert response.json()["message"] == "Conversation test-conv deleted"
            mock_delete.assert_called_once_with("test-conv")

    def test_delete_conversation_not_found(self):
        """Test deleting a nonexistent conversation."""
        with patch('diagram_generator.backend.api.diagrams.storage.delete_conversation') as mock_delete:
            mock_delete.return_value = False

            response = client.delete("/diagrams/conversations/test-conv")

            assert response.status_code == 404, response.text
            assert response.json()["detail"] == "Conversation not found"
            mock_delete.assert_called_once_with("test-conv")

    def test_list_conversations(self):
        """Test listing conversations for a diagram."""
        test_time = datetime(2025, 3, 11, 14, 47, 55, 399110)
        conversations = [
            ConversationRecord(
                id=f"test-conv-{i}",
                diagram_id="test-diagram",
                messages=[ConversationMessage(role="user", content=f"message {i}", timestamp=test_time, metadata={})],
                created_at=test_time,
                updated_at=test_time,
                metadata={}
            )
            for i in range(2)
        ]

        with patch('diagram_generator.backend.api.diagrams.storage.list_conversations') as mock_list:
            mock_list.return_value = conversations

            response = client.get("/diagrams/conversations", params={"diagram_id": "test-diagram"})

            assert response.status_code == 200, response.text
            response_json = response.json()
            assert len(response_json) == 2
            assert all(conv["diagram_id"] == "test-diagram" for conv in response_json)
            mock_list.assert_called_once_with("test-diagram")

    def test_continue_conversation(self):
        """Test continuing an existing conversation."""
        test_time = datetime(2025, 3, 11, 14, 47, 55, 399110)
        conversation = ConversationRecord(
            id="test-conv",
            diagram_id="test-diagram",
            messages=[
                ConversationMessage(role="user", content="initial message", timestamp=test_time, metadata={}),
                ConversationMessage(role="assistant", content="response", timestamp=test_time, metadata={})
            ],
            created_at=test_time,
            updated_at=test_time,
            metadata={}
        )

        with patch('diagram_generator.backend.api.diagrams.storage.get_conversation') as mock_get, \
             patch('diagram_generator.backend.api.diagrams.storage.update_conversation') as mock_update:
            mock_get.return_value = conversation
            mock_update.return_value = None

            response = client.post(
                f"/diagrams/conversations/{conversation.id}/continue",
                json={"message": "follow up"}
            )

            assert response.status_code == 200, response.text
            response_json = response.json()
            assert response_json["id"] == conversation.id
            assert len(response_json["messages"]) == 3  # Original + response + new message
            assert response_json["messages"][-1]["content"] == "follow up"
            mock_get.assert_called_once_with(conversation.id)
            mock_update.assert_called_once()
