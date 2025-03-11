"""RAG utilities for document embedding and retrieval."""

import os
from typing import Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from diagram_generator.backend.models.configs import DiagramRAGConfig


class RAGProvider:
    """Handles document loading, embedding, and retrieval for RAG."""

    def __init__(
        self, 
        config: DiagramRAGConfig,
        ollama_base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ):
        """Initialize RAGProvider.
        
        Args:
            config: RAG configuration
            ollama_base_url: Ollama API base URL
            embedding_model: Embedding model to use
        """
        self.config = config
        self.base_url = ollama_base_url
        self.embedding_model = embedding_model
        self.vector_store = None
        
    def load_docs_from_directory(self, directory_path: Optional[str] = None) -> bool:
        """Load documents from a directory and create embeddings.
        
        Args:
            directory_path: Path to directory containing documents (overrides config)
            
        Returns:
            bool: True if documents were loaded successfully
        """
        try:
            doc_dir = directory_path or self.config.api_doc_dir
            if not doc_dir or not os.path.isdir(doc_dir):
                return False
                
            # Load markdown files from directory
            loader = DirectoryLoader(
                doc_dir, 
                glob="**/*.md",
                loader_cls=TextLoader
            )
            documents = loader.load()
            
            if not documents:
                return False
                
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)
            
            # Create embeddings
            embeddings = OllamaEmbeddings(
                base_url=self.base_url,
                model=self.embedding_model,
            )
            
            # Create vector store
            self.vector_store = FAISS.from_documents(
                chunks, 
                embeddings
            )
            
            return True
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
            
    def get_relevant_context(self, query: str) -> Optional[str]:
        """Get relevant context for a query.
        
        Args:
            query: Query to search for
            
        Returns:
            str: Relevant context or None if no context found
        """
        if not self.vector_store:
            return None
            
        try:
            docs = self.vector_store.similarity_search(
                query, 
                k=self.config.top_k_results
            )
            
            if not docs:
                return None
                
            contexts = [doc.page_content for doc in docs]
            return "\n\n".join(contexts)
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return None