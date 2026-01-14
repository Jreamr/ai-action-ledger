👉 New here? Start with [LANDINGPAGE.md](./LANDINGPAGE.md)

# AI Action Ledger

A tamper-evident, append-only logging system for AI actions. This is v1 - intentionally minimal.

## Features

- **Append-only events**: No updates, no deletes. Corrections are new events.
- **Hash chain integrity**: Each event includes a hash of the previous event, creating a tamper-evident chain per agent.
- **Privacy-safe defaults**: Stores hashes of inputs/outputs, not raw content.
- **Simple dashboard**: View, filter, export, and verify events.
- **Dual storage**: PostgreSQL for queries + append-only files for archival.

## Architecture

```
SDK → POST /events → Hash Chain → PostgreSQL + Archive Files → Dashboard
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git (to clone or download)

### 1. Setup

```bash
# Clone/download the project, then:
cd ai-action-ledger

# Create environment file
cp .env.example .env

# Edit .env and set your API key (or keep default for dev)
# API_KEY=your-secret-api-key-here

# Create archive directory
mkdir -p archive
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 3. Access

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:3000

## API Reference

All endpoints require the `X-API-Key` header.

### Create Event
```bash
POST /events
Content-Type: application/json
X-API-Key: your-api-key

{
  "agent_id": "agent-001",
  "action_type": "llm_call",
  "tool_name": "web_search",
  "environment": "production",
  "model_version": "gpt-4-0125",
  "prompt_version": "v1.2.3",
  "input_hash": "a1b2c3d4e5f6...",  # 64-char SHA-256 hex
  "output_hash": "f6e5d4c3b2a1..."   # 64-char SHA-256 hex
}
```

### List Events
```bash
GET /events?agent_id=agent-001&action_type=llm_call&start_time=2024-01-01T00:00:00Z&page=1&page_size=50
X-API-Key: your-api-key
```

### Get Single Event
```bash
GET /events/{event_id}
X-API-Key: your-api-key
```

### Export Events
```bash
GET /export?format=json&agent_id=agent-001
GET /export?format=csv&agent_id=agent-001
X-API-Key: your-api-key
```

### Verify Chain Integrity
```bash
GET /verify?agent_id=agent-001&start_time=2024-01-01T00:00:00Z&end_time=2024-12-31T23:59:59Z
X-API-Key: your-api-key
```

### Verify Archive (DB vs Files)
```bash
GET /verify/archive?agent_id=agent-001&date=2024-01-15
X-API-Key: your-api-key
```

### Health Check
```bash
GET /health
```

## Testing the System

### Test 1: Create Events and Verify Chain

```bash
# Set your API key
export API_KEY="dev-api-key-change-me"

# Create first event for agent-001
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "agent_id": "agent-001",
    "action_type": "llm_call",
    "tool_name": "chat",
    "environment": "test",
    "model_version": "gpt-4",
    "prompt_version": "v1",
    "input_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "output_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }'

# Create second event (will chain to first)
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "agent_id": "agent-001",
    "action_type": "tool_use",
    "tool_name": "web_search",
    "environment": "test",
    "model_version": "gpt-4",
    "prompt_version": "v1",
    "input_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "output_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
  }'

# Create third event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "agent_id": "agent-001",
    "action_type": "llm_call",
    "tool_name": "chat",
    "environment": "test",
    "model_version": "gpt-4",
    "prompt_version": "v1",
    "input_hash": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "output_hash": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  }'

# Verify the chain is intact
curl "http://localhost:8000/verify?agent_id=agent-001" \
  -H "X-API-Key: $API_KEY"

# Expected: {"agent_id":"agent-001","is_valid":true,"events_checked":3,...}
```

### Test 2: Verify Tampering Detection

```bash
# Connect to the database and tamper with an event
# Note: Postgres requires subquery for UPDATE with LIMIT
docker-compose exec db psql -U ledger -d action_ledger -c \
  "UPDATE events SET action_type = 'TAMPERED' WHERE event_id = (SELECT event_id FROM events WHERE agent_id = 'agent-001' ORDER BY timestamp LIMIT 1);"

# Now verify - should detect the tampering
curl "http://localhost:8000/verify?agent_id=agent-001" \
  -H "X-API-Key: $API_KEY"

# Expected: {"agent_id":"agent-001","is_valid":false,"error_message":"Event hash mismatch..."}

# Restore the database for further testing
docker-compose down -v
docker-compose up -d
```

### Test 3: Verify Archive Matches Database

```bash
# After creating events, verify archive integrity
# Replace YYYY-MM-DD with today's date
curl "http://localhost:8000/verify/archive?agent_id=agent-001&date=$(date +%Y-%m-%d)" \
  -H "X-API-Key: $API_KEY"

# Expected: {"agent_id":"agent-001","date":"...","is_valid":true,"db_events":3,"archive_events":3,...}
```

### Test 4: Test API Key Security

```bash
# Try without API key - should get 401
curl http://localhost:8000/events

# Try with wrong API key - should get 401
curl http://localhost:8000/events -H "X-API-Key: wrong-key"
```

### Test 5: Export and View

```bash
# List all events
curl "http://localhost:8000/events" -H "X-API-Key: $API_KEY"

# Export as JSON
curl "http://localhost:8000/export?format=json" -H "X-API-Key: $API_KEY" -o events.json

# Export as CSV
curl "http://localhost:8000/export?format=csv" -H "X-API-Key: $API_KEY" -o events.csv
```

### Test 6: Check Archive Files

```bash
# View archive directory structure
ls -la archive/

# View archive file for an agent
cat archive/agent-001/*.jsonl
```

## File Structure

```
ai-action-ledger/
├── docker-compose.yml      # Service orchestration
├── .env.example            # Environment template
├── README.md               # This file
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py         # FastAPI app
│       ├── config.py       # Settings
│       ├── auth.py         # API key auth
│       ├── models.py       # Pydantic schemas
│       ├── database.py     # DB connection
│       ├── db_models.py    # SQLAlchemy models
│       ├── hash_chain.py   # Hash chain logic
│       ├── archive.py      # File archive writer
│       └── routes/
│           ├── events.py   # Event CRUD
│           ├── export.py   # Export endpoints
│           └── verify.py   # Verification endpoint
├── dashboard/
│   ├── index.html          # Dashboard UI
│   ├── styles.css          # Styling
│   └── nginx.conf          # Nginx config
└── archive/                # Archive storage (git-ignored)
```

## Event Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | UUID | Auto | Unique event identifier |
| agent_id | String | Yes | AI agent identifier |
| action_type | String | Yes | Type of action (e.g., llm_call, tool_use) |
| tool_name | String | No | Name of tool used |
| timestamp | DateTime | Auto | When event was recorded |
| environment | String | No | Environment (production, staging, etc.) |
| model_version | String | No | AI model version |
| prompt_version | String | No | Prompt template version |
| input_hash | String(64) | Yes | SHA-256 hash of input |
| output_hash | String(64) | Yes | SHA-256 hash of output |
| previous_event_hash | String(64) | Auto | Hash of previous event (chain link) |
| event_hash | String(64) | Auto | Hash of this event |

## Hash Chain Logic

Each event's hash is computed as:

```
event_hash = SHA256(canonical_json({
  event_id,
  agent_id,
  action_type,
  tool_name,
  timestamp,
  environment,
  model_version,
  prompt_version,
  input_hash,
  output_hash,
  previous_event_hash
}))
```

### Determinism Guarantees

The canonical JSON format ensures identical events always produce identical hashes:

| Concern | Solution |
|---------|----------|
| Key ordering | `sort_keys=True` - alphabetical order |
| Whitespace | `separators=(',', ':')` - no spaces |
| Timestamps | Normalized to UTC: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` |
| Null values | Python `None` → JSON `null` (consistent) |
| Encoding | UTF-8 |

### Chain Properties

- The first event for an agent has `previous_event_hash = null`
- Each subsequent event includes the hash of the previous event
- This creates a per-agent chain that detects any tampering
- `event_id` and `timestamp` are server-generated (not client-provided)

### What This Proves

This system proves **integrity of recorded events** - no silent edits after recording.

It does **not** prove **completeness** - that all events were recorded. That's a separate problem requiring trusted client SDKs or attestation.

## Commands Reference

```bash
# Start services
docker-compose up --build -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Rebuild after code changes
docker-compose up --build

# Access database directly
docker-compose exec db psql -U ledger -d action_ledger
```

## Future Enhancements (v2+)

- [ ] S3 archive backend
- [ ] Multiple API keys with scopes
- [ ] Webhooks for new events
- [ ] Event batching
- [ ] Prometheus metrics
- [ ] SDK packages (Python, TypeScript)

## License

MIT
