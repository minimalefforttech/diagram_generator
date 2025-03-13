"""Router for log management endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any, Literal

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parents[3])
if project_root not in sys.path:
    sys.path.append(project_root)

from diagram_generator.backend.storage.database import Storage
from diagram_generator.backend.models.logs import LogRecord

# Configure logging
logger = logging.getLogger(__name__)

# Re-export LogRecord for backward compatibility
LogEntry = LogRecord

class CreateLogRequest(BaseModel):
    """Request model for creating a log entry."""
    type: str
    message: str
    details: Optional[Any] = None

# Initialize storage singleton
storage = Storage()

def add_entry(type: str, message: str, details: Any = None) -> LogRecord:
    """Add a new log entry."""
    entry = LogRecord(
        type=type,
        message=message,
        timestamp=datetime.utcnow(),
        details=details
    )
    storage.save_log(entry)
    return entry

# Helper functions for logging specific types of events
def log_llm(message: str, details: Optional[Any] = None) -> LogRecord:
    """Log an LLM-related event."""
    return add_entry("llm", message, details)

import traceback

def log_error(message: str, details: Optional[Any] = None, exc_info: bool = False) -> LogRecord:
    """Log an error event."""
    if exc_info:
        details = details or {}
        details["traceback"] = traceback.format_exc()
    logger.error(message, extra={"details": details}, exc_info=exc_info)
    return add_entry("error", message, details)

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
)

@router.get("")
async def get_logs() -> List[LogRecord]:
    """Get all log entries."""
    return storage.get_logs()

@router.post("")
async def create_log(request: CreateLogRequest) -> LogRecord:
    """Create a new log entry."""
    return add_entry(
        type=request.type,
        message=request.message,
        details=request.details
    )

@router.delete("")
async def clear_logs():
    """Clear all log entries."""
    storage.clear_logs()
    return {"status": "success", "message": "All logs cleared"}
