# AI Action Ledger — Start Here

A tamper-evident logging system for AI actions. If an event is logged, you can prove it wasn't silently changed later.

## What This Does (and Doesn't)

**Does:**
- Records AI actions with cryptographic hashes
- Detects if any logged event was modified after the fact
- Chains events per agent so tampering breaks the chain

**Does NOT:**
- Prove that all events were logged (completeness)
- Prevent AI from taking actions
- Store raw prompts/outputs (hashes only by default)

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed

### 2. Start the Services
```bash
cd ai-action-ledger
cp .env.example .env
mkdir -p archive
docker-compose up --build
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

### 3. Check Health
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"healthy","database":"healthy","archive":"healthy"}
```

### 4. Log Your First Event
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-change-me" \
  -d '{
    "agent_id": "my-agent",
    "action_type": "llm_call",
    "input_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "output_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }'
```

You'll get back the event with `event_id`, `timestamp`, and `event_hash`.

### 5. Verify the Chain
```bash
curl "http://localhost:8000/verify?agent_id=my-agent" \
  -H "X-API-Key: dev-api-key-change-me"
```

Expected:
```json
{"agent_id":"my-agent","is_valid":true,"events_checked":1,...}
```

### 6. View the Dashboard

Open in browser: `http://localhost:3000`

## Using the Python SDK
```python
from action_ledger import LedgerClient

client = LedgerClient("http://localhost:8000", "dev-api-key-change-me")

client.log_event(
    agent_id="my-agent",
    action_type="llm_call",
    input_hash=client.hash_content("What is 2+2?"),
    output_hash=client.hash_content("4")
)

result = client.verify_chain("my-agent")
print(result)  # {"is_valid": true, ...}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/events` | POST | Log a new event |
| `/events` | GET | List events (with filters) |
| `/events/{id}` | GET | Get single event |
| `/verify` | GET | Verify chain integrity |
| `/export` | GET | Export as JSON or CSV |

All endpoints except `/health` require `X-API-Key` header.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `dev-api-key-change-me` | API authentication key |
| `POSTGRES_DB` | `ledger` | Database name |
| `CORS_ALLOW_ORIGINS` | `*` | Allowed CORS origins |

## Next Steps

- Read `ARCHITECTURE.md` to understand how it works
- Read `LIMITATIONS.md` for known constraints
- Deploy to a server for real use