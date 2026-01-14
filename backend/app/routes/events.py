from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.database import get_db
from app.auth import verify_api_key
from app.models import EventCreate, EventResponse, EventListResponse
from app.db_models import Event
from app.hash_chain import compute_event_hash, get_previous_event_hash
from app.archive import get_archive_writer

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new event in the ledger.
    
    Events are append-only and hash-chained per agent_id.
    Timestamp is server-generated UTC - not client-provided.
    """
    # Generate event ID and timestamp (server-generated, always UTC)
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc)
    
    # Get previous event hash for this agent (for chaining)
    previous_event_hash = get_previous_event_hash(db, event_data.agent_id)
    
    # Compute event hash (includes previous hash for chain integrity)
    event_hash = compute_event_hash(
        event_id=event_id,
        agent_id=event_data.agent_id,
        action_type=event_data.action_type,
        tool_name=event_data.tool_name,
        timestamp=timestamp,
        environment=event_data.environment,
        model_version=event_data.model_version,
        prompt_version=event_data.prompt_version,
        input_hash=event_data.input_hash,
        output_hash=event_data.output_hash,
        previous_event_hash=previous_event_hash
    )
    
    # Create database record
    db_event = Event(
        event_id=event_id,
        agent_id=event_data.agent_id,
        action_type=event_data.action_type,
        tool_name=event_data.tool_name,
        timestamp=timestamp,
        environment=event_data.environment,
        model_version=event_data.model_version,
        prompt_version=event_data.prompt_version,
        input_hash=event_data.input_hash,
        output_hash=event_data.output_hash,
        previous_event_hash=previous_event_hash,
        event_hash=event_hash
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Write to append-only archive
    try:
        archive_writer = get_archive_writer()
        archive_writer.write_event(db_event)
    except Exception as e:
        # Log but don't fail the request - DB is primary storage
        # In production, this should alert on failure
        print(f"Warning: Archive write failed: {e}")
    
    return EventResponse(
        event_id=db_event.event_id,
        agent_id=db_event.agent_id,
        action_type=db_event.action_type,
        tool_name=db_event.tool_name,
        timestamp=db_event.timestamp,
        environment=db_event.environment,
        model_version=db_event.model_version,
        prompt_version=db_event.prompt_version,
        input_hash=db_event.input_hash,
        output_hash=db_event.output_hash,
        previous_event_hash=db_event.previous_event_hash,
        event_hash=db_event.event_hash
    )


@router.get("", response_model=EventListResponse)
async def list_events(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_time: Optional[datetime] = Query(None, description="Filter events after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter events before this time"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List events with optional filters.
    
    Supports filtering by agent_id, action_type, and time range.
    Results are paginated and ordered by timestamp descending.
    """
    query = db.query(Event)
    
    # Apply filters
    if agent_id:
        query = query.filter(Event.agent_id == agent_id)
    if action_type:
        query = query.filter(Event.action_type == action_type)
    if start_time:
        query = query.filter(Event.timestamp >= start_time)
    if end_time:
        query = query.filter(Event.timestamp <= end_time)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    events = query.order_by(desc(Event.timestamp)).offset(offset).limit(page_size).all()
    
    return EventListResponse(
        events=[
            EventResponse(
                event_id=e.event_id,
                agent_id=e.agent_id,
                action_type=e.action_type,
                tool_name=e.tool_name,
                timestamp=e.timestamp,
                environment=e.environment,
                model_version=e.model_version,
                prompt_version=e.prompt_version,
                input_hash=e.input_hash,
                output_hash=e.output_hash,
                previous_event_hash=e.previous_event_hash,
                event_hash=e.event_hash
            )
            for e in events
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get a single event by ID.
    """
    event = db.query(Event).filter(Event.event_id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    return EventResponse(
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
        previous_event_hash=event.previous_event_hash,
        event_hash=event.event_hash
    )