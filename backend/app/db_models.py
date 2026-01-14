from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Event(Base):
    """SQLAlchemy model for events table."""
    
    __tablename__ = "events"
    
    # Primary key - UUID as string for compatibility
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core fields
    agent_id = Column(String(255), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Context fields
    environment = Column(String(100), nullable=True)
    model_version = Column(String(100), nullable=True)
    prompt_version = Column(String(100), nullable=True)
    
    # Hash fields (privacy-safe - no raw content)
    input_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=False)
    
    # Chain fields
    previous_event_hash = Column(String(64), nullable=True)  # NULL for first event in chain
    event_hash = Column(String(64), nullable=False, unique=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_agent_timestamp', 'agent_id', 'timestamp'),
        Index('idx_agent_action', 'agent_id', 'action_type'),
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "environment": self.environment,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash
        }