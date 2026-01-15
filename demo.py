#!/usr/bin/env python3
"""
AI Action Ledger Demo

This script demonstrates the full flow:
1. Log several events
2. Verify the chain
3. List all events

Prerequisites:
- AI Action Ledger running: docker compose up
- requests installed: pip install requests

Usage:
    python demo.py
"""

import hashlib
import requests
import time

# Configuration
LEDGER_URL = "http://localhost:8000"
API_KEY = "dev-api-key-change-me"
AGENT_ID = f"demo-agent-{int(time.time())}"

def sha256(content: str) -> str:
    """Hash content using SHA-256."""
    return hashlib.sha256(content.encode()).hexdigest()

def log_event(action_type: str, input_text: str, output_text: str, tool_name: str = None):
    """Log an event to the ledger."""
    payload = {
        "agent_id": AGENT_ID,
        "action_type": action_type,
        "input_hash": sha256(input_text),
        "output_hash": sha256(output_text),
    }
    if tool_name:
        payload["tool_name"] = tool_name
    
    response = requests.post(
        f"{LEDGER_URL}/events",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    response.raise_for_status()
    return response.json()

def verify_chain():
    """Verify the hash chain for our agent."""
    response = requests.get(
        f"{LEDGER_URL}/verify",
        headers={"X-API-Key": API_KEY},
        params={"agent_id": AGENT_ID}
    )
    response.raise_for_status()
    return response.json()

def list_events():
    """List all events for our agent."""
    response = requests.get(
        f"{LEDGER_URL}/events",
        headers={"X-API-Key": API_KEY},
        params={"agent_id": AGENT_ID}
    )
    response.raise_for_status()
    return response.json()

def main():
    print("=" * 60)
    print("AI Action Ledger Demo")
    print("=" * 60)
    print(f"\nAgent ID: {AGENT_ID}")
    print(f"Ledger URL: {LEDGER_URL}")
    
    # Check health
    print("\n[1/5] Checking ledger health...")
    try:
        health = requests.get(f"{LEDGER_URL}/health").json()
        print(f"  Status: {health['status']}")
        print(f"  Database: {health['database']}")
        print(f"  Archive: {health['archive']}")
    except Exception as e:
        print(f"  ERROR: Could not connect to ledger. Is it running?")
        print(f"  Run: docker compose up")
        return

    # Log events
    print("\n[2/5] Logging events...")
    
    events = [
        ("llm_call", "What is the capital of France?", "The capital of France is Paris.", None),
        ("llm_call", "What is 2 + 2?", "2 + 2 equals 4.", None),
        ("tool_use", "search: weather in NYC", "Currently 72°F and sunny in New York City.", "web_search"),
        ("llm_call", "Summarize the weather", "It's a nice day in NYC - 72°F and sunny.", None),
    ]
    
    for i, (action_type, input_text, output_text, tool_name) in enumerate(events, 1):
        event = log_event(action_type, input_text, output_text, tool_name)
        print(f"  Event {i}: {action_type}")
        print(f"    ID: {event['event_id'][:8]}...")
        print(f"    Hash: {event['event_hash'][:16]}...")
        if event['previous_event_hash']:
            print(f"    Previous: {event['previous_event_hash'][:16]}...")
        else:
            print(f"    Previous: (genesis event)")
    
    # Verify chain
    print("\n[3/5] Verifying chain integrity...")
    verification = verify_chain()
    print(f"  Valid: {verification['is_valid']}")
    print(f"  Events checked: {verification['events_checked']}")
    if verification['error_message']:
        print(f"  Error: {verification['error_message']}")
    
    # List events
    print("\n[4/5] Listing all events...")
    events_response = list_events()
    print(f"  Total events: {events_response['total']}")
    for event in events_response['events']:
        print(f"    - {event['action_type']}: {event['event_hash'][:16]}...")
    
    # Summary
    print("\n[5/5] Summary")
    print("=" * 60)
    print(f"  Agent: {AGENT_ID}")
    print(f"  Events logged: {events_response['total']}")
    print(f"  Chain valid: {verification['is_valid']}")
    print(f"  Dashboard: http://localhost:3000")
    print("=" * 60)
    print("\n✓ Demo complete! Check the dashboard to see your events.")

if __name__ == "__main__":
    main()
