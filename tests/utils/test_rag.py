"""Tests for RAG utilities."""

import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, Mock, patch

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from diagram_generator.backend.models.configs import DiagramRAGConfig
from diagram_generator.backend.utils.rag import RAGProvider

@pytest.fixture
def mock_embeddings():
    """Create a mock embeddings model."""
    mock = MagicMock(spec=OllamaEmbeddings)
    return mock

@pytest.fixture
def mock_vector_store():
    """Create a mock FAISS vector store."""
    mock = MagicMock(spec=FAISS)
    mock.similarity_search.return_value = [
        Document(page_content="API docs content 1"),
        Document(page_content="API docs content 2")
    ]
    return mock

@pytest.fixture
def test_docs_dir(tmp_path):
    """Create a temporary directory with test markdown files."""
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()
    
    # Create test markdown files
    (docs_dir / "api.md").write_text("# API Documentation\nEndpoint details here")
    (docs_dir / "guide.md").write_text("# User Guide\nHow to use the API")
    (docs_dir / "nested").mkdir()
    (docs_dir / "nested" / "advanced.md").write_text("# Advanced Topics\nComplex scenarios")
    
    return str(docs_dir)

def test_rag_provider_init():
    """Test RAGProvider initialization."""
    config = DiagramRAGConfig(
        enabled=True,
        api_doc_dir="/test/docs",
        top_k_results=3
    )
    
    provider = RAGProvider(config)
    
    assert provider.config == config
    assert provider.base_url == "http://localhost:11434"
    assert provider.embedding_model == "nomic-embed-text"
    assert provider.vector_store is None

@pytest.mark.asyncio
async def test_load_docs_success(test_docs_dir, mock_embeddings):
    """Test successful document loading."""
    config = DiagramRAGConfig(enabled=True, api_doc_dir=test_docs_dir)
    provider = RAGProvider(config)
    
    with patch('diagram_generator.backend.utils.rag.OllamaEmbeddings', return_value=mock_embeddings), \
         patch('diagram_generator.backend.utils.rag.FAISS.from_documents') as mock_faiss_create:
        
        # Setup mock vector store
        mock_vector_store = MagicMock()
        mock_faiss_create.return_value = mock_vector_store
        
        # Load documents
        result = provider.load_docs_from_directory()
        
        assert result is True
        assert provider.vector_store == mock_vector_store
        mock_faiss_create.assert_called_once()

def test_load_docs_invalid_directory():
    """Test document loading with invalid directory."""
    config = DiagramRAGConfig(enabled=True, api_doc_dir="/nonexistent")
    provider = RAGProvider(config)
    
    result = provider.load_docs_from_directory()
    
    assert result is False
    assert provider.vector_store is None

def test_load_docs_no_markdown_files(tmp_path):
    """Test document loading with no markdown files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    config = DiagramRAGConfig(enabled=True, api_doc_dir=str(empty_dir))
    provider = RAGProvider(config)
    
    result = provider.load_docs_from_directory()
    
    assert result is False
    assert provider.vector_store is None

def test_get_relevant_context_success(mock_vector_store):
    """Test successful context retrieval."""
    config = DiagramRAGConfig(enabled=True, top_k_results=2)
    provider = RAGProvider(config)
    provider.vector_store = mock_vector_store
    
    context = provider.get_relevant_context("test query")
    
    assert context is not None
    assert "API docs content 1" in context
    assert "API docs content 2" in context
    mock_vector_store.similarity_search.assert_called_once_with("test query", k=2)

def test_get_relevant_context_no_vector_store():
    """Test context retrieval with no vector store."""
    config = DiagramRAGConfig(enabled=True)
    provider = RAGProvider(config)
    
    context = provider.get_relevant_context("test query")
    
    assert context is None

def test_get_relevant_context_empty_results(mock_vector_store):
    """Test context retrieval with empty search results."""
    mock_vector_store.similarity_search.return_value = []
    
    config = DiagramRAGConfig(enabled=True)
    provider = RAGProvider(config)
    provider.vector_store = mock_vector_store
    
    context = provider.get_relevant_context("test query")
    
    assert context is None
