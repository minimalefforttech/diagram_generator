"""Main FastAPI application module for LLM Diagram Generator."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api import diagrams, ollama

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
