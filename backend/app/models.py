from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum
import re


class EventCreate(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=128)
    action_type: str = Field(..., min_length=1, max_length=100)
    tool_name: Optional[str] = Field(None, max_length=255)
    environment: Optional[str] = Field(None, max_length=100)
    model_version: Optional[str] = Field(None, max_length=100)
    prompt_version: Optional[str] = Field(None, max_length=100)
    input_hash: str = Field(..., min_length=64, max_length=64)
    output_hash: str = Field(..., min_length=64, max_length=64)

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Prevent path traversal attacks - only allow safe characters."""
        if not re.match(r'^[a-zA-Z0-9._-]{1,128}$', v):
            raise ValueError('agent_id must contain only letters, numbers, dots, underscores, and hyphens')
        return v

    @field_validator('input_hash', 'output_hash')
    @classmethod
    def validate_hex_hash(cls, v: str) -> str:
        """Ensure hashes are valid lowercase hex."""
        if not re.match(r'^[0-9a-fA-F]{64}$', v):
            raise ValueError('Hash must be exactly 64 hexadecimal characters')
        return v.lower()  # Normalize to lowercase


class EventResponse(BaseModel):
    event_id: str
    agent_id: str
    action_type: str
    tool_name: Optional[str]
    timestamp: datetime
    environment: Optional[str]
    model_version: Optional[str]
    prompt_version: Optional[str]
    input_hash: str
    output_hash: str
    previous_event_hash: Optional[str]
    event_hash: str

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class VerifyResponse(BaseModel):
    agent_id: str
    is_valid: bool
    events_checked: int
    first_invalid_event_id: Optional[str] = None
    error_message: Optional[str] = None


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


class HealthResponse(BaseModel):
    status: str
    database: str
    archive: str