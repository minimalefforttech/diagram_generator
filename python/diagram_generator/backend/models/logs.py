"""Shared log models."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel

class LogRecord(BaseModel):
    """Record of a log entry."""
    type: str
    message: str
    timestamp: datetime
    details: Optional[Any] = None
