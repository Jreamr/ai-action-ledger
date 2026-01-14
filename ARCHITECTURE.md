# AI Action Ledger — Architecture

## Overview
```
Client → POST /events → Validate → Hash → Store (DB + Archive) → Response
                                     ↓
                              Chain to previous event
```

## Event Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `event_id` | UUID | Server | Unique identifier |
| `agent_id` | String | Client | Which agent performed the action |
| `action_type` | String | Client | What kind of action (llm_call, tool_use, etc.) |
| `tool_name` | String | Client | Optional tool identifier |
| `timestamp` | DateTime | Server | When the event was recorded (UTC) |
| `environment` | String | Client | Optional (production, staging, etc.) |
| `model_version` | String | Client | Optional model identifier |
| `prompt_version` | String | Client | Optional prompt version |
| `input_hash` | String(64) | Client | SHA-256 hash of input |
| `output_hash` | String(64) | Client | SHA-256 hash of output |
| `previous_event_hash` | String(64) | Server | Hash of prior event (null if first) |
| `event_hash` | String(64) | Server | Hash of this event |

**Privacy note:** Raw inputs/outputs are never stored. Only hashes.

## Hash Chain

Each agent has its own chain:
```
Event 1: previous_event_hash = null
         event_hash = SHA256(canonical_json(event_1))

Event 2: previous_event_hash = event_1.event_hash
         event_hash = SHA256(canonical_json(event_2))

Event 3: previous_event_hash = event_2.event_hash
         event_hash = SHA256(canonical_json(event_3))
```

If any event is modified, its hash changes, breaking the chain.

## Canonicalization Rules

To ensure the same event always produces the same hash:

| Rule | Implementation |
|------|----------------|
| Key order | Alphabetically sorted (`sort_keys=True`) |
| Whitespace | No spaces (`separators=(',', ':')`) |
| Timestamps | UTC, fixed precision: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` |
| Null values | JSON `null` |
| Encoding | UTF-8 |

Example canonical JSON:
```json
{"action_type":"llm_call","agent_id":"my-agent","environment":null,...}
```

## Storage

**Database (PostgreSQL):**
- Primary storage for queries
- Indexed by agent_id, timestamp, action_type

**Archive (JSONL files):**
- Append-only backup
- One file per agent per day: `archive/{agent_id}/YYYY-MM-DD.jsonl`
- Used for verification cross-check

## Verification Flow

`GET /verify?agent_id=xxx`:

1. Fetch all events for agent, ordered by timestamp
2. For each event:
   - Recompute hash from stored fields
   - Compare to stored `event_hash`
   - Compare `previous_event_hash` to prior event's hash
3. Return valid/invalid + first broken event

## Threat Model

### What This Detects

| Threat | Detected? |
|--------|-----------|
| Someone edits an event in the DB | ✅ Yes — hash mismatch |
| Someone deletes an event | ✅ Yes — chain break |
| Someone inserts a fake event | ✅ Yes — hash won't match |
| Someone reorders events | ✅ Yes — chain break |

### What This Does NOT Detect

| Threat | Detected? | Why |
|--------|-----------|-----|
| Client never logs an event | ❌ No | We only know what's sent to us |
| Client lies about content | ❌ No | We only store the hash they provide |
| Client sends wrong hash | ❌ No | We trust client-provided hashes |

**Key point:** This proves integrity (no tampering after logging), not completeness (all actions were logged).

## Input Validation

| Field | Validation |
|-------|------------|
| `agent_id` | `^[a-zA-Z0-9._-]{1,128}$` (prevents path traversal) |
| `input_hash` | `^[0-9a-fA-F]{64}$` (valid hex, normalized to lowercase) |
| `output_hash` | `^[0-9a-fA-F]{64}$` (valid hex, normalized to lowercase) |

## ⚠️ Do Not Change Casually

These decisions affect hash integrity. Changing them breaks verification of old events:

| Item | Current Value | Warning |
|------|---------------|---------|
| Hash algorithm | SHA-256 | Changing breaks all existing hashes |
| Canonical JSON format | sorted keys, no whitespace | Changing breaks all existing hashes |
| Timestamp format | `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` | Changing breaks all existing hashes |
| Event immutability | No updates allowed | Allowing updates defeats the purpose |
| `event_id` generation | Server-side UUID | Client-controlled IDs enable replay attacks |
| `timestamp` generation | Server-side UTC | Client-controlled timestamps enable ordering attacks |

If you must change any of these, you'll need a migration strategy and version flag.