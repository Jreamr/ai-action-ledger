from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
import csv
import json
import io

from app.database import get_db
from app.auth import verify_api_key
from app.models import ExportFormat
from app.db_models import Event

router = APIRouter(prefix="/export", tags=["export"])


@router.get("")
async def export_events(
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_time: Optional[datetime] = Query(None, description="Filter events after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter events before this time"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Export events as CSV or JSON.
    
    Supports the same filters as the list endpoint.
    Returns a downloadable file.
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
    
    events = query.order_by(Event.timestamp).all()
    
    if format == ExportFormat.CSV:
        return _export_csv(events)
    else:
        return _export_json(events)


def _export_csv(events: list[Event]) -> StreamingResponse:
    """Generate CSV export."""
    output = io.StringIO()
    
    fieldnames = [
        "event_id",
        "agent_id",
        "action_type",
        "tool_name",
        "timestamp",
        "environment",
        "model_version",
        "prompt_version",
        "input_hash",
        "output_hash",
        "previous_event_hash",
        "event_hash"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for event in events:
        writer.writerow({
            "event_id": event.event_id,
            "agent_id": event.agent_id,
            "action_type": event.action_type,
            "tool_name": event.tool_name or "",
            "timestamp": event.timestamp.isoformat(),
            "environment": event.environment or "",
            "model_version": event.model_version or "",
            "prompt_version": event.prompt_version or "",
            "input_hash": event.input_hash,
            "output_hash": event.output_hash,
            "previous_event_hash": event.previous_event_hash or "",
            "event_hash": event.event_hash
        })
    
    output.seek(0)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"events_export_{timestamp}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_json(events: list[Event]) -> StreamingResponse:
    """Generate JSON export."""
    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "total_events": len(events),
        "events": [
            {
                "event_id": e.event_id,
                "agent_id": e.agent_id,
                "action_type": e.action_type,
                "tool_name": e.tool_name,
                "timestamp": e.timestamp.isoformat(),
                "environment": e.environment,
                "model_version": e.model_version,
                "prompt_version": e.prompt_version,
                "input_hash": e.input_hash,
                "output_hash": e.output_hash,
                "previous_event_hash": e.previous_event_hash,
                "event_hash": e.event_hash
            }
            for e in events
        ]
    }
    
    output = json.dumps(data, indent=2)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"events_export_{timestamp}.json"
    
    return StreamingResponse(
        iter([output]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )