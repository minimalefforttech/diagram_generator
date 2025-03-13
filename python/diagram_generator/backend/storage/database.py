"""Database storage for diagrams and conversation history."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from pydantic import BaseModel
import traceback

# Configure logger
logger = logging.getLogger(__name__)

class DiagramRecord(BaseModel):
    """Record of a generated diagram."""
    id: str
    description: str
    diagram_type: str
    code: str
    created_at: datetime
    tags: Set[str] = set()
    metadata: Dict[str, Any] = {}

class ConversationMessage(BaseModel):
    """Message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class ConversationRecord(BaseModel):
    """Record of a diagram generation conversation."""
    id: str
    diagram_id: str
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}

class LogRecord(BaseModel):
    """Record of a log entry."""
    type: str
    message: str
    timestamp: datetime
    details: Optional[Any] = None

class StorageError(Exception):
    """Base class for storage-related errors."""
    pass

class StorageConfig(BaseModel):
    """Configuration for storage layer."""
    data_dir: str = "data"
    diagrams_dir: str = "diagrams"
    conversations_dir: str = "conversations"
    logs_dir: str = "logs"
    user_preferences_dir: str = "user_preferences"
    index_file: str = "index.json"

class Storage:
    """Storage layer for diagrams and conversations."""

    def __init__(self, config: StorageConfig = StorageConfig()):
        """Initialize storage.
        
        Args:
            config: Storage configuration
        """
        self.index = {"diagrams": {}, "conversations": {}, "logs": []}
        self.config = config
        self.base_path = Path(config.data_dir)
        self.diagrams_path = self.base_path / config.diagrams_dir
        self.conversations_path = self.base_path / config.conversations_dir
        self.logs_path = self.base_path / config.logs_dir
        self.user_preferences_path = self.base_path / config.user_preferences_dir
        self.index_path = self.base_path / config.index_file

        # Create directory structure
        self.diagrams_path.mkdir(parents=True, exist_ok=True)
        self.conversations_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.user_preferences_path.mkdir(parents=True, exist_ok=True)

        # Load or create index
        self.index = self._load_index()
        
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load storage index from disk.
        
        Returns:
            dict: Storage index
        """
        default_index = {"diagrams": {}, "conversations": {}, "logs": []}
        if self.index_path.exists():
            try:
                index = json.loads(self.index_path.read_text())
                # Ensure all required keys exist with default values
                for key, default_value in default_index.items():
                    if key not in index:
                        index[key] = default_value
                return index
            except json.JSONDecodeError as e:
                error_msg = "Failed to parse index file, creating new one"
                self.log_exception(error_msg, e)
                return default_index
        return default_index
        
    def _save_index(self) -> None:
        """Save storage index to disk."""
        try:
            self.index_path.write_text(json.dumps(self.index, indent=2))
        except Exception as e:
            logger.error(f"Failed to save index file: {str(e)}", exc_info=True)
            raise StorageError("Failed to save index file")
    
    def log_exception(self, message:str, exception: Exception) -> None:
        """Log an exception to the storage layer.
        
        Args:
            message: Message to log
            exception: Exception to log
        """
        details = {}
        details["traceback"] = traceback.format_exception(type(exception), exception, exception.__traceback__)
        
        # Log the exception
        log_record = LogRecord(
            type="error",
            message=message,
            timestamp=datetime.now(),
            details={"exception": str(exception), "traceback": details["traceback"]}
        )
        self.save_log(log_record)
        logger.error(message, extra={"details": details}, exc_info=True)

    def save_log(self, log: LogRecord) -> None:
        """Save a log record.
        
        Args:
            log: Log record to save
        """
        # Convert log to dict
        log_dict = log.model_dump()
        log_dict["timestamp"] = log_dict["timestamp"].isoformat()
        
        # Add to index
        self.index["logs"].append(log_dict)
        
        # Keep only last 1000 logs
        if len(self.index["logs"]) > 1000:
            self.index["logs"] = self.index["logs"][-1000:]
            
        self._save_index()

    def get_logs(self) -> List[LogRecord]:
        """Get all log records.
        
        Returns:
            List[LogRecord]: List of log records
        """
        return [LogRecord(**log) for log in self.index.get("logs", [])]

    def clear_logs(self) -> None:
        """Clear all log records."""
        self.index["logs"] = []
        self._save_index()
        
    def save_diagram(self, diagram: DiagramRecord) -> None:
        """Save a diagram record.
        
        Args:
            diagram: Diagram record to save
        """
        try:
            # Convert diagram to dict and ensure tags is serialized as a list
            diagram_dict = diagram.model_dump()
            diagram_dict["tags"] = list(diagram_dict["tags"]) if diagram_dict.get("tags") else []
            
            # Save diagram data
            diagram_path = self.diagrams_path / f"{diagram.id}.json"
            diagram_path.write_text(json.dumps(diagram_dict, indent=2, default=str))
            
            # Update index
            self.index["diagrams"][diagram.id] = {
                "type": diagram.diagram_type,
                "tags": list(diagram.tags),
                "created_at": diagram.created_at.isoformat()
            }
            self._save_index()
        except Exception as e:
            self.log_exception(f"Failed to save diagram {diagram.id}: {str(e)}", e)
            raise StorageError(f"Failed to save diagram {diagram.id}")

    def get_diagram(self, diagram_id: str) -> Optional[DiagramRecord]:
        """Retrieve a diagram record.
        
        Args:
            diagram_id: ID of diagram to retrieve
            
        Returns:
            DiagramRecord or None: Retrieved diagram record
        """
        diagram_path = self.diagrams_path / f"{diagram_id}.json"
        
        if not diagram_path.exists():
            return None
            
        try:
            data = json.loads(diagram_path.read_text())
            # Convert tags from list back to set if it exists
            if "tags" in data:
                data["tags"] = set(data["tags"]) if isinstance(data["tags"], list) else set()
            return DiagramRecord.model_validate(data)
        except Exception as e:
            self.log_exception(f"Failed to load diagram {diagram_id}: {e}", e)
            raise StorageError(f"Failed to load diagram {diagram_id}: {e}")

    def save_conversation(self, conversation: ConversationRecord) -> None:
        """Save a conversation record.
        
        Args:
            conversation: Conversation record to save
        """
        try:
            # Save conversation data
            conv_path = self.conversations_path / f"{conversation.id}.json"
            conv_path.write_text(json.dumps(conversation.model_dump(), indent=2, default=str))
            
            # Update index
            self.index["conversations"][conversation.id] = {
                "diagram_id": conversation.diagram_id,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            }
            self._save_index()
        except Exception as e:
            self.log_exception(f"Failed to save conversation {conversation.id}: {str(e)}", e)
            raise StorageError(f"Failed to save conversation {conversation.id}")
        
    def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        """Retrieve a conversation record.
        
        Args:
            conversation_id: ID of conversation to retrieve
            
        Returns:
            ConversationRecord or None: Retrieved conversation record
        """
        conv_path = self.conversations_path / f"{conversation_id}.json"
        
        if not conv_path.exists():
            return None
            
        try:
            data = json.loads(conv_path.read_text())
            return ConversationRecord.model_validate(data)
        except Exception as e:
            self.log_exception(f"Failed to load conversation {conversation_id}: {e}", e)
            raise StorageError(f"Failed to load conversation {conversation_id}: {e}")
            
    def delete_diagram(self, diagram_id: str) -> bool:
        """Delete a diagram record.
        
        Args:
            diagram_id: ID of diagram to delete
            
        Returns:
            bool: Whether deletion was successful
        """
        diagram_path = self.diagrams_path / f"{diagram_id}.json"
        
        try:
            diagram_path.unlink(missing_ok=True)
            self.index["diagrams"].pop(diagram_id, None)
            self._save_index()
            return True
        except Exception as e:
            self.log_exception(f"Failed to delete diagram {diagram_id}: {str(e)}", e)
            return False
            
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation record.
        
        Args:
            conversation_id: ID of conversation to delete
            
        Returns:
            bool: Whether deletion was successful
        """
        conv_path = self.conversations_path / f"{conversation_id}.json"
        
        try:
            conv_path.unlink(missing_ok=True)
            self.index["conversations"].pop(conversation_id, None)
            self._save_index()
            return True
        except Exception as e:
            self.log_exception(f"Failed to delete conversation {conversation_id}: {str(e)}", e)
            return False

    def clear_diagrams(self) -> None:
        """Clear all diagram records and associated conversations."""
        try:
            # Get all diagram IDs first
            diagram_ids = list(self.index["diagrams"].keys())
            
            # Delete each diagram and its associated conversations
            for diagram_id in diagram_ids:
                # Delete associated conversations first
                conv_ids = self.get_diagram_history(diagram_id)
                for conv_id in conv_ids:
                    self.delete_conversation(conv_id)
                
                # Then delete the diagram
                self.delete_diagram(diagram_id)
            
            # Clear index entries
            self.index["diagrams"].clear()
            self._save_index()

        except Exception as e:
            self.log_exception(f"Failed to clear diagrams: {str(e)}", e)
            raise StorageError(f"Failed to clear diagrams: {str(e)}")

    def search_diagrams(
        self,
        diagram_type: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[str]:
        """Search for diagram IDs matching criteria.
        
        Args:
            diagram_type: Filter by diagram type
            tags: Filter by tags (all must match)
            start_date: Filter by creation date (inclusive)
            end_date: Filter by creation date (inclusive)
            
        Returns:
            List[str]: Matching diagram IDs
        """
        results = []
        
        for diagram_id, info in self.index["diagrams"].items():
            if diagram_type and info["type"] != diagram_type:
                continue
                
            if tags and not tags.issubset(set(info["tags"])):
                continue
                
            created_at = datetime.fromisoformat(info["created_at"])
            
            if start_date and created_at < start_date:
                continue
                
            if end_date and created_at > end_date:
                continue
                
            results.append(diagram_id)
            
        return results
        
    def get_diagram_history(self, diagram_id: str) -> List[str]:
        """Get conversation IDs associated with a diagram.
        
        Args:
            diagram_id: Diagram ID to get history for
            
        Returns:
            List[str]: Associated conversation IDs
        """
        return [
            conv_id for conv_id, info in self.index["conversations"].items()
            if info["diagram_id"] == diagram_id
        ]

    def list_conversations(self, diagram_id: str) -> List[ConversationRecord]:
        """List all conversations for a diagram.
        
        Args:
            diagram_id: Diagram ID to list conversations for
            
        Returns:
            List[ConversationRecord]: List of conversations
        """
        conversations = []
        for conv_id, info in self.index["conversations"].items():
            if info["diagram_id"] == diagram_id:
                conv = self.get_conversation(conv_id)
                if conv:
                    conversations.append(conv)
        return conversations

    def update_conversation(self, conversation: ConversationRecord) -> None:
        """Update an existing conversation record.
        
        Args:
            conversation: Updated conversation record
        """
        # Just use save_conversation since it handles both create and update
        self.save_conversation(conversation)

    def get_all_diagrams(self) -> List[DiagramRecord]:
        """Get all diagrams in storage.
        
        Returns:
            List[DiagramRecord]: List of all diagram records
        """
        # Reload index to ensure we have latest data
        self.index = self._load_index()
        
        diagrams = []
        for diagram_id in self.index["diagrams"]:
            diagram = self.get_diagram(diagram_id)
            if diagram:
                diagrams.append(diagram)
        return diagrams

    def save_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Save user preferences.

        Args:
            user_id: ID of user
            preferences: User preferences to save
        """
        try:
            # Save preferences data
            pref_path = self.user_preferences_path / f"{user_id}.json"
            pref_path.write_text(json.dumps(preferences, indent=2, default=str))
        except Exception as e:
            self.log_exception(f"Failed to save preferences for user {user_id}: {str(e)}", e)
            raise StorageError(f"Failed to save preferences for user {user_id}")

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user preferences.

        Args:
            user_id: ID of user

        Returns:
            Dict[str, Any] or None: Retrieved user preferences
        """
        pref_path = self.user_preferences_path / f"{user_id}.json"

        if not pref_path.exists():
            return None

        try:
            data = json.loads(pref_path.read_text())
            return data
        except Exception as e:
            error_msg = f"Failed to load preferences for user {user_id}: {e}"
            self.log_exception(error_msg, e)
            raise StorageError(error_msg)
