"""Router for log management endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from collections import deque
from typing import List, Optional, Any, Literal

# Configure logging
logger = logging.getLogger(__name__)

class LogEntry(BaseModel):
    """Model for log entries."""
    type: Literal["error", "llm", "info"]
    message: str
    timestamp: str
    details: Optional[Any] = None

class CreateLogRequest(BaseModel):
    """Request model for creating a log entry."""
    type: Literal["error", "llm", "info"]
    message: str
    details: Optional[Any] = None

class LogService:
    """Service class for managing logs."""
    def __init__(self):
        # Using a deque with maxlen to prevent unbounded memory growth
        self.log_entries = deque(maxlen=1000)  # Store last 1000 logs

    def get_logs(self) -> List[LogEntry]:
        """Get all log entries."""
        return list(self.log_entries)

    def add_entry(self, type: str, message: str, details: Any = None) -> LogEntry:
        """Add a new log entry."""
        entry = LogEntry(
            type=type,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )
        self.log_entries.append(entry)
        return entry

# Create a singleton instance
log_service = LogService()

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
)

@router.get("", response_model=List[LogEntry])
async def get_logs():
    """Get all log entries."""
    return log_service.get_logs()

@router.post("", response_model=LogEntry)
async def create_log(request: CreateLogRequest):
    """Create a new log entry."""
    return log_service.add_entry(
        type=request.type,
        message=request.message,
        details=request.details
    )
