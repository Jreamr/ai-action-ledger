from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import verify_api_key
from app.models import VerifyResponse
from app.hash_chain import verify_chain
from app.archive import get_archive_writer
from app.db_models import Event

router = APIRouter(prefix="/verify", tags=["verify"])


class ArchiveVerifyResponse(BaseModel):
    """Response for archive verification."""
    agent_id: str
    date: str
    is_valid: bool
    db_events: int
    archive_events: int
    mismatches: int
    missing_in_archive: int
    error_message: Optional[str] = None


@router.get("", response_model=VerifyResponse)
async def verify_integrity(
    agent_id: str = Query(..., description="Agent ID to verify"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO format)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Verify the integrity of the event chain for an agent.
    
    Checks that:
    1. Each event's hash matches its content
    2. Each event's previous_event_hash correctly references the prior event
    
    Returns verification status and details about any chain breaks.
    """
    is_valid, events_checked, first_invalid_event_id, error_message = verify_chain(
        db=db,
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time
    )
    
    return VerifyResponse(
        agent_id=agent_id,
        is_valid=is_valid,
        events_checked=events_checked,
        first_invalid_event_id=first_invalid_event_id,
        error_message=error_message
    )


@router.get("/archive", response_model=ArchiveVerifyResponse)
async def verify_archive(
    agent_id: str = Query(..., description="Agent ID to verify"),
    date: str = Query(..., description="Date to verify (YYYY-MM-DD format)"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Verify that archive files match database records for a given agent and date.
    
    Compares event_hash values between DB and archive to detect:
    - Events in DB but missing from archive
    - Hash mismatches between DB and archive
    """
    try:
        verify_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return ArchiveVerifyResponse(
            agent_id=agent_id,
            date=date,
            is_valid=False,
            db_events=0,
            archive_events=0,
            mismatches=0,
            missing_in_archive=0,
            error_message="Invalid date format. Use YYYY-MM-DD."
        )
    
    # Get events from DB for this agent and date
    start_of_day = verify_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = verify_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    db_events = db.query(Event).filter(
        Event.agent_id == agent_id,
        Event.timestamp >= start_of_day,
        Event.timestamp <= end_of_day
    ).all()
    
    # Get events from archive
    archive_writer = get_archive_writer()
    archive_events = archive_writer.read_events(agent_id, verify_date)
    
    # Build lookup of archive events by event_hash
    archive_by_hash = {e["event_hash"]: e for e in archive_events}
    
    mismatches = 0
    missing_in_archive = 0
    
    for db_event in db_events:
        if db_event.event_hash not in archive_by_hash:
            missing_in_archive += 1
        else:
            # Verify the archived event_hash matches
            archived = archive_by_hash[db_event.event_hash]
            if archived["event_id"] != db_event.event_id:
                mismatches += 1
    
    is_valid = (mismatches == 0 and missing_in_archive == 0)
    
    error_message = None
    if not is_valid:
        errors = []
        if missing_in_archive > 0:
            errors.append(f"{missing_in_archive} events missing from archive")
        if mismatches > 0:
            errors.append(f"{mismatches} hash mismatches")
        error_message = "; ".join(errors)
    
    return ArchiveVerifyResponse(
        agent_id=agent_id,
        date=date,
        is_valid=is_valid,
        db_events=len(db_events),
        archive_events=len(archive_events),
        mismatches=mismatches,
        missing_in_archive=missing_in_archive,
        error_message=error_message
    )