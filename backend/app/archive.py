import json
import os
from datetime import datetime
from pathlib import Path
from typing import Protocol
from app.config import get_settings
from app.db_models import Event


class ArchiveWriter(Protocol):
    """Protocol for archive writers (allows future S3 implementation)."""
    
    def write_event(self, event: Event) -> None:
        """Write an event to the archive."""
        ...


class LocalFileArchiveWriter:
    """
    Append-only local file archive writer.
    
    Writes events to daily files organized by agent_id:
    /archive/{agent_id}/{YYYY-MM-DD}.jsonl
    
    Each line is a complete JSON object (JSON Lines format).
    """
    
    def __init__(self, base_path: str = None):
        settings = get_settings()
        self.base_path = Path(base_path or settings.archive_path)
        self._ensure_base_path()
    
    def _ensure_base_path(self) -> None:
        """Create base archive directory if it doesn't exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_archive_path(self, agent_id: str, timestamp: datetime) -> Path:
        """Get the archive file path for a given agent and date."""
        date_str = timestamp.strftime("%Y-%m-%d")
        agent_dir = self.base_path / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir / f"{date_str}.jsonl"
    
    def write_event(self, event: Event) -> None:
        """
        Append an event to the appropriate daily archive file.
        
        Uses append mode to ensure we never overwrite existing events.
        """
        archive_path = self._get_archive_path(event.agent_id, event.timestamp)
        
        event_data = {
            "event_id": event.event_id,
            "agent_id": event.agent_id,
            "action_type": event.action_type,
            "tool_name": event.tool_name,
            "timestamp": event.timestamp.isoformat(),
            "environment": event.environment,
            "model_version": event.model_version,
            "prompt_version": event.prompt_version,
            "input_hash": event.input_hash,
            "output_hash": event.output_hash,
            "previous_event_hash": event.previous_event_hash,
            "event_hash": event.event_hash
        }
        
        # Append mode - never overwrites
        with open(archive_path, 'a') as f:
            f.write(json.dumps(event_data, separators=(',', ':')) + '\n')
    
    def read_events(self, agent_id: str, date: datetime) -> list[dict]:
        """Read all events from an archive file (for verification)."""
        archive_path = self._get_archive_path(agent_id, date)
        
        if not archive_path.exists():
            return []
        
        events = []
        with open(archive_path, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        return events
    
    def check_health(self) -> bool:
        """Check if archive directory is writable."""
        try:
            test_file = self.base_path / ".health_check"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False


def get_archive_writer() -> ArchiveWriter:
    """Factory function to get the appropriate archive writer."""
    # For v1, always use local file writer
    # Later, this can check config to return S3 writer
    return LocalFileArchiveWriter()