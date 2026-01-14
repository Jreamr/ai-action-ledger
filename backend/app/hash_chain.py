import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db_models import Event


def normalize_timestamp(ts: datetime) -> str:
    """
    Normalize timestamp to UTC ISO format for consistent hashing.
    
    Always outputs: YYYY-MM-DDTHH:MM:SS.ffffff+00:00
    This ensures the same moment in time always produces the same string.
    """
    # If naive datetime, assume UTC
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # Convert to UTC
    ts_utc = ts.astimezone(timezone.utc)
    # Format with fixed precision (6 decimal places for microseconds)
    return ts_utc.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def canonicalize_event(
    event_id: str,
    agent_id: str,
    action_type: str,
    tool_name: Optional[str],
    timestamp: datetime,
    environment: Optional[str],
    model_version: Optional[str],
    prompt_version: Optional[str],
    input_hash: str,
    output_hash: str,
    previous_event_hash: Optional[str]
) -> str:
    """
    Create a canonical JSON representation of an event for hashing.
    
    Determinism guarantees:
    - Keys are sorted alphabetically
    - No whitespace between elements
    - Timestamps normalized to UTC with fixed microsecond precision
    - None values serialize as JSON null
    """
    canonical = {
        "event_id": event_id,
        "agent_id": agent_id,
        "action_type": action_type,
        "tool_name": tool_name,
        "timestamp": normalize_timestamp(timestamp),
        "environment": environment,
        "model_version": model_version,
        "prompt_version": prompt_version,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "previous_event_hash": previous_event_hash
    }
    
    # Sort keys for consistent ordering, use separators without spaces
    return json.dumps(canonical, sort_keys=True, separators=(',', ':'))


def compute_event_hash(
    event_id: str,
    agent_id: str,
    action_type: str,
    tool_name: Optional[str],
    timestamp: datetime,
    environment: Optional[str],
    model_version: Optional[str],
    prompt_version: Optional[str],
    input_hash: str,
    output_hash: str,
    previous_event_hash: Optional[str]
) -> str:
    """
    Compute SHA-256 hash of the canonical event representation.
    
    The hash includes the previous_event_hash to create the chain.
    """
    canonical = canonicalize_event(
        event_id=event_id,
        agent_id=agent_id,
        action_type=action_type,
        tool_name=tool_name,
        timestamp=timestamp,
        environment=environment,
        model_version=model_version,
        prompt_version=prompt_version,
        input_hash=input_hash,
        output_hash=output_hash,
        previous_event_hash=previous_event_hash
    )
    
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def get_previous_event_hash(db: Session, agent_id: str) -> Optional[str]:
    """
    Get the hash of the most recent event for a given agent.
    
    Returns None if this is the first event for the agent.
    """
    previous_event = (
        db.query(Event)
        .filter(Event.agent_id == agent_id)
        .order_by(desc(Event.timestamp), desc(Event.event_id))
        .first()
    )
    
    return previous_event.event_hash if previous_event else None


def verify_event_hash(event: Event) -> bool:
    """
    Verify that an event's hash is correct.
    
    Returns True if the stored hash matches the computed hash.
    """
    computed_hash = compute_event_hash(
        event_id=event.event_id,
        agent_id=event.agent_id,
        action_type=event.action_type,
        tool_name=event.tool_name,
        timestamp=event.timestamp,
        environment=event.environment,
        model_version=event.model_version,
        prompt_version=event.prompt_version,
        input_hash=event.input_hash,
        output_hash=event.output_hash,
        previous_event_hash=event.previous_event_hash
    )
    
    return computed_hash == event.event_hash


def verify_chain(db: Session, agent_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> tuple[bool, int, Optional[str], Optional[str]]:
    """
    Verify the integrity of the event chain for an agent.
    
    Returns:
        - is_valid: True if chain is valid
        - events_checked: Number of events verified
        - first_invalid_event_id: ID of first invalid event (if any)
        - error_message: Description of the error (if any)
    """
    query = db.query(Event).filter(Event.agent_id == agent_id)
    
    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)
    
    events = query.order_by(Event.timestamp, Event.event_id).all()
    
    if not events:
        return True, 0, None, None
    
    events_checked = 0
    expected_previous_hash = None
    
    # If we have a start_time filter, get the previous event to establish the chain
    if start_time and events:
        first_event = events[0]
        expected_previous_hash = first_event.previous_event_hash
    
    for i, event in enumerate(events):
        events_checked += 1
        
        # Verify the event's own hash
        if not verify_event_hash(event):
            return False, events_checked, event.event_id, f"Event hash mismatch for event {event.event_id}"
        
        # For the first event in a full chain (no start_time filter), previous should be None
        # For subsequent events, previous should match the last event's hash
        if i == 0 and not start_time:
            if event.previous_event_hash is not None:
                # Check if there's actually a prior event
                prior = db.query(Event).filter(
                    Event.agent_id == agent_id,
                    Event.timestamp < event.timestamp
                ).first()
                if prior is None and event.previous_event_hash is not None:
                    return False, events_checked, event.event_id, f"First event should have no previous hash"
        elif i > 0:
            if event.previous_event_hash != expected_previous_hash:
                return False, events_checked, event.event_id, f"Chain broken: previous_event_hash mismatch"
        
        expected_previous_hash = event.event_hash
    
    return True, events_checked, None, None