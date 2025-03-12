"""Main FastAPI application module for LLM Diagram Generator."""

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from diagram_generator.backend.api import diagrams, ollama, logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console output
        logging.FileHandler('diagram_generator.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

# Configure Python path for development
if 'PYTHONPATH' not in os.environ:
    project_root = Path(__file__).parents[3]  # Go up 3 levels from backend/main.py
    python_path = str(project_root / 'python')
    os.environ['PYTHONPATH'] = python_path
    sys.path.insert(0, python_path)
    logger.info(f"Development mode: Added {python_path} to PYTHONPATH")

app = FastAPI(
    title="LLM Diagram Generator",
    description="API for generating and managing diagrams using LLMs",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": app.version
    }

# Include routers
app.include_router(ollama.router)
app.include_router(diagrams.router)
app.include_router(logs.router)

def run_server():
    """Entry point for the console script to run the server."""
    import uvicorn
    uvicorn.run(
        "diagram_generator.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["python/diagram_generator/backend"],
        reload_excludes=["*.pyc", "*.log", "data/*", ".git/*", "__pycache__/*"],
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
