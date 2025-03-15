"""Tests for RAG utilities."""

import os
import json
import numpy as np
from pathlib import Path
import pytest
from unittest.mock import MagicMock, Mock, patch, AsyncMock

from diagram_generator.backend.models.configs import DiagramRAGConfig
from diagram_generator.backend.utils.rag import (
    RAGProvider, Document, RAGDocument, RAGSearchResult, 
    TextSplitter, VectorStore
)

@pytest.fixture
def mock_embeddings_response():
    """Mock embeddings response from Ollama API."""
    return {
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
    }

@pytest.fixture
def test_docs_dir(tmp_path):
    """Create a temporary directory with test files."""
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()
    
    # Create test files
    (docs_dir / "api.md").write_text("# API Documentation\nEndpoint details here")
    (docs_dir / "guide.md").write_text("# User Guide\nHow to use the API")
    (docs_dir / "nested").mkdir()
    (docs_dir / "nested" / "advanced.md").write_text("# Advanced Topics\nComplex scenarios")
    
    return str(docs_dir)

def test_text_splitter():
    """Test TextSplitter functionality."""
    splitter = TextSplitter(chunk_size=10, chunk_overlap=3)
    text = "This is a test document. It has multiple sentences."
    chunks = splitter.split_text(text)
    
    assert len(chunks) > 0
    assert all(len(chunk) <= 10 for chunk in chunks)

def test_vector_store():
    """Test VectorStore functionality."""
    store = VectorStore()
    
    # Create test documents with embeddings
    docs = [
        Document(
            content="Test doc 1",
            metadata={"source": "test1.md"},
            embedding=[0.1, 0.2, 0.3]
        ),
        Document(
            content="Test doc 2",
            metadata={"source": "test2.md"},
            embedding=[0.4, 0.5, 0.6]
        )
    ]
    
    store.add_documents(docs)
    
    # Test search
    results = store.similarity_search_with_score([0.1, 0.2, 0.3], k=2)
    assert len(results) == 2
    assert all(isinstance(score, float) for _, score in results)

@pytest.mark.asyncio
async def test_rag_provider_load_docs(test_docs_dir, mock_embeddings_response):
    """Test loading documents with RAG provider."""
    config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=test_docs_dir,
        top_k_results=3
    )
    
    provider = RAGProvider(config)
    
    # Mock the embeddings API call
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_embeddings_response
        
        result = await provider.load_docs_from_directory()
        
        assert result is True
        assert provider.stats.total_documents > 0
        assert provider.stats.total_chunks > 0
        assert provider.stats.vector_store_initialized is True

@pytest.mark.asyncio
async def test_rag_provider_search(test_docs_dir, mock_embeddings_response):
    """Test searching with RAG provider."""
    config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir=test_docs_dir,
        top_k_results=2
    )
    
    provider = RAGProvider(config)
    
    # Mock the embeddings API call
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_embeddings_response
        
        # First load documents
        await provider.load_docs_from_directory()
        
        # Then search
        result = await provider.get_relevant_context("test query")
        
        assert result is not None
        assert isinstance(result, RAGSearchResult)
        assert len(result.documents) > 0
        assert all(isinstance(doc, RAGDocument) for doc in result.documents)
        assert all(isinstance(doc.score, float) for doc in result.documents)
