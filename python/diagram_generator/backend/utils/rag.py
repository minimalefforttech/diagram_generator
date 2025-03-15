"""RAG (Retrieval Augmented Generation) utility for retrieving relevant context."""

import os
import re
import logging
from typing import List, Dict, Optional, Any, Union
import asyncio
from pydantic import BaseModel, Field
import json

# Import logging functions
from diagram_generator.backend.api.logs import log_info, log_error, log_warning

logger = logging.getLogger(__name__)

class EmbeddingResult(BaseModel):
    """Model for embedding results."""
    embedding: List[float] = Field(..., description="Vector embedding")
    error: Optional[str] = Field(None, description="Error message if failed")

class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    source: str = Field("", description="Source file or origin")
    chunk_id: int = Field(0, description="Chunk ID")
    chunk_size: int = Field(0, description="Size of chunk in characters")
    total_chunks: int = Field(1, description="Total chunks in source")
    file_extension: Optional[str] = Field(None, description="File extension")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")

class Document(BaseModel):
    """Document with content and metadata."""
    content: str = Field(..., description="Document content")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

class EmbeddedDocument(Document):
    """Document with embedding."""
    embedding: List[float] = Field(..., description="Vector embedding")
    score: Optional[float] = Field(None, description="Similarity score")

class SearchResult(BaseModel):
    """Search results with documents and scores."""
    query: str = Field(..., description="Search query")
    documents: List[EmbeddedDocument] = Field(default_factory=list, description="Matching documents")
    scores: List[float] = Field(default_factory=list, description="Similarity scores")

class RetrievalResult(BaseModel):
    """Result from retrieval including documents and metadata."""
    documents: List[Document] = Field(default_factory=list, description="Retrieved documents")
    query: str = Field("", description="Original query")

class RAGConfig(BaseModel):
    """Configuration for RAG provider."""
    enabled: bool = Field(False, description="Whether RAG is enabled")
    api_doc_dir: Optional[str] = Field(None, description="Directory with API docs")
    embedding_model: str = Field("nomic-embed-text", description="Embedding model to use")
    max_documents: int = Field(5, description="Maximum documents to retrieve")
    similarity_threshold: float = Field(0.2, description="Minimum similarity score")

class RAGStats(BaseModel):
    """Statistics for RAG provider."""
    total_documents: int = Field(0, description="Total documents processed")
    loaded_files: int = Field(0, description="Number of files loaded")
    failed_files: int = Field(0, description="Number of files that failed to load")
    embedding_requests: int = Field(0, description="Number of embedding requests made")
    search_requests: int = Field(0, description="Number of search requests made")

class RAGProvider:
    """Provider for Retrieval Augmented Generation."""

    def __init__(self, config: Any, ollama_base_url: str = "http://localhost:11434"):
        """Initialize RAG provider."""
        self.config = config
        # Safe access to config attributes
        self.similarity_threshold = getattr(config, 'similarity_threshold', 0.2)
        self.max_documents = getattr(config, 'max_documents', 5)
        self.embedding_model = getattr(config, 'embedding_model', 'nomic-embed-text')
        
        self.ollama_base_url = ollama_base_url
        self.documents: List[EmbeddedDocument] = []
        self.stats = RAGStats()
        self.logger = logging.getLogger(__name__)

    def _is_code_file(self, filename: str) -> bool:
        """Check if a file is a code file based on extension."""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', 
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.less', '.json', '.yaml', '.yml',
            '.md', '.rst', '.txt', '.sh', '.bash', '.ps1', '.bat', '.cmd'
        }
        _, ext = os.path.splitext(filename)
        return ext.lower() in code_extensions

    async def load_docs_from_directory(self, directory: str, use_simple_file_splitting: bool = False) -> bool:
        """Load documents from directory using simple file-based splitting."""
        try:
            if not os.path.isdir(directory):
                log_error(f"Directory not found: {directory}")
                return False

            log_info(f"Loading documents from {directory}")
            self.documents = []  # Reset documents
            loaded_files = 0
            failed_files = 0

            # Simple file-based splitting approach - each file is one document
            if use_simple_file_splitting:
                for root, _, files in os.walk(directory):
                    for filename in files:
                        if not self._is_code_file(filename):
                            continue
                            
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, directory)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            # Skip empty or very small files
                            if len(content.strip()) < 5:
                                continue
                                
                            # Create document metadata
                            _, ext = os.path.splitext(filename)
                            metadata = DocumentMetadata(
                                source=rel_path,
                                chunk_id=1,
                                chunk_size=len(content),
                                total_chunks=1,
                                file_extension=ext
                            )
                            
                            # Create document
                            doc = Document(content=content, metadata=metadata)
                            
                            # Embed the document
                            embedded_doc = await self._embed_document(doc)
                            if embedded_doc:
                                self.documents.append(embedded_doc)
                                loaded_files += 1
                                self.logger.debug(f"Loaded document from {rel_path}")
                            else:
                                failed_files += 1
                                log_warning(f"Failed to embed document from {rel_path}")
                                
                        except Exception as e:
                            failed_files += 1
                            log_error(f"Error loading file {file_path}: {str(e)}")
            else:
                # Original approach with complex chunking (not implemented here)
                log_warning("Complex chunking not implemented, defaulting to file-based splitting")
                return await self.load_docs_from_directory(directory, use_simple_file_splitting=True)

            # Update stats
            self.stats.total_documents = len(self.documents)
            self.stats.loaded_files = loaded_files
            self.stats.failed_files = failed_files
            
            log_info(f"Loaded {loaded_files} files with {len(self.documents)} documents. Failed: {failed_files}")
            return True
            
        except Exception as e:
            log_error(f"Error loading documents: {str(e)}", exc_info=True)
            return False

    async def _embed_document(self, doc: Document) -> Optional[EmbeddedDocument]:
        """Embed a document using Ollama embedding API."""
        try:
            import aiohttp
            
            # Prepare the request
            url = f"{self.ollama_base_url}/api/embeddings"
            payload = {
                "model": "nomic-embed-text", # Good default embedding model
                "prompt": doc.content
            }
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response_json = await response.json()
                    
                    if response.status != 200:
                        error = response_json.get("error", "Unknown error")
                        log_error(f"Embedding API error: {error}")
                        return None
                        
                    # Extract embedding
                    embedding = response_json.get("embedding")
                    if not embedding:
                        log_error("No embedding returned")
                        return None
                        
                    # Update stats
                    self.stats.embedding_requests += 1
                    
                    # Create embedded document
                    return EmbeddedDocument(
                        content=doc.content,
                        metadata=doc.metadata,
                        embedding=embedding
                    )
                    
        except Exception as e:
            log_error(f"Error embedding document: {str(e)}", exc_info=True)
            return None

    async def get_relevant_context(self, query: str) -> Optional[RetrievalResult]:
        """Get relevant context based on query."""
        try:
            if not self.documents:
                log_warning("No documents loaded for search")
                return None
                
            # Embed the query
            query_embedding = await self._get_query_embedding(query)
            if not query_embedding:
                log_error("Failed to embed query")
                return None
                
            # Calculate similarity with each document
            results = []
            for doc in self.documents:
                similarity = self._calculate_similarity(query_embedding, doc.embedding)
                # Use the instance variable instead of accessing config directly
                if similarity > self.similarity_threshold:
                    # Add score to the document for debugging
                    doc_copy = EmbeddedDocument(
                        content=doc.content,
                        metadata=doc.metadata,
                        embedding=doc.embedding,
                        score=similarity
                    )
                    results.append((doc_copy, similarity))
                    
            # Sort by similarity and take top N
            results.sort(key=lambda x: x[1], reverse=True)
            # Use the instance variable
            results = results[:self.max_documents]
            
            # Update stats
            self.stats.search_requests += 1
            
            # Create result
            result_docs = []
            for doc, score in results:
                # Create a copy of the document without embedding
                result_doc = Document(
                    content=doc.content,
                    metadata=doc.metadata
                )
                result_doc.metadata.source = doc.metadata.source  # Ensure source is copied
                result_docs.append(result_doc)
                self.logger.debug(f"Document {doc.metadata.source} score: {score}")
                
            return RetrievalResult(
                documents=result_docs,
                query=query
            )
            
        except Exception as e:
            log_error(f"Error in get_relevant_context: {str(e)}", exc_info=True)
            return None

    async def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Get embedding for a query."""
        try:
            import aiohttp
            
            # Prepare the request
            url = f"{self.ollama_base_url}/api/embeddings"
            payload = {
                "model": self.embedding_model,  # Use instance variable
                "prompt": query
            }
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response_json = await response.json()
                    
                    if response.status != 200:
                        error = response_json.get("error", "Unknown error")
                        log_error(f"Embedding API error: {error}")
                        return None
                        
                    # Extract embedding
                    embedding = response_json.get("embedding")
                    if not embedding:
                        log_error("No embedding returned")
                        return None
                        
                    # Update stats
                    self.stats.embedding_requests += 1
                    
                    return embedding
                    
        except Exception as e:
            log_error(f"Error getting query embedding: {str(e)}", exc_info=True)
            return None

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm_a = np.linalg.norm(vec1)
            norm_b = np.linalg.norm(vec2)
            
            if norm_a == 0 or norm_b == 0:
                return 0
                
            return dot_product / (norm_a * norm_b)
            
        except Exception as e:
            log_error(f"Error calculating similarity: {str(e)}", exc_info=True)
            return 0
