# AI Action Ledger

**A tamper-evident audit log for AI agent actions.**

⚠️ Early-stage project. See [LIMITATIONS.md](./LIMITATIONS.md) before use.

👉 New here? Start with [LANDINGPAGE.md](./LANDINGPAGE.md)

---

## Quickstart (5 minutes)

**1. Clone and start:**

```bash
git clone https://github.com/Jreamr/ai-action-ledger.git
cd ai-action-ledger
cp .env.example .env
docker compose up --build
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

**2. Check health:**

```bash
curl http://localhost:8000/health
```

**3. Log an event:**

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-change-me" \
  -d '{"agent_id":"test","action_type":"llm_call","input_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","output_hash":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}'
```

**4. Verify the chain:**

```bash
curl "http://localhost:8000/verify?agent_id=test" \
  -H "X-API-Key: dev-api-key-change-me"
```

**5. View dashboard:**

Open http://localhost:3000

---

## LangChain Integration (3 minutes)

```python
from action_ledger import LedgerClient, ActionLedgerCallback
from langchain.llms import OpenAI

# Set up callback
callback = ActionLedgerCallback(
    ledger_url="http://localhost:8000",
    api_key="dev-api-key-change-me",
    agent_id="my-langchain-agent"
)

# Use with any LangChain LLM
llm = OpenAI(callbacks=[callback])
llm.invoke("What is 2+2?")
# Automatically logged!
```

See [EXAMPLES.md](./EXAMPLES.md) for more integration patterns.

---

## Screenshots

### Dashboard — Events List
![Dashboard](./screenshots/dashboard.png)

### Chain Verification
![Verify](./screenshots/verify.png)

---

## What This Does

- Records AI actions (LLM calls, tool use, chain steps) to an append-only log
- Cryptographically hash-chains each event
- Detects if any logged event was modified after the fact
- Stores hashes + metadata by default — not raw prompts or outputs

**If an event is logged, its integrity can be independently verified later.**

---

## What This Does NOT Do

- Does not prevent AI actions — only records what happened
- Does not guarantee completeness — we only log what's sent to us
- Does not store raw content by default — only hashes
- Does not have compliance certifications (SOC2, HIPAA, etc.)

See [LIMITATIONS.md](./LIMITATIONS.md) for full details.

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [LANDINGPAGE.md](./LANDINGPAGE.md) | Product overview |
| [START_HERE.md](./START_HERE.md) | Getting started guide |
| [EXAMPLES.md](./EXAMPLES.md) | Integration code samples |
| [FAQ.md](./FAQ.md) | Common questions |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Technical deep-dive |
| [LIMITATIONS.md](./LIMITATIONS.md) | What it doesn't do |

---

## Early Access

Want to try it? We're looking for early users building AI agents.

**[→ Request Early Access](https://github.com/Jreamr/ai-action-ledger/discussions)**

Or self-host now using the Quickstart above.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/events` | POST | Log an event |
| `/events` | GET | List events (with filters) |
| `/verify` | GET | Verify chain integrity |
| `/export` | GET | Export as JSON or CSV |

All endpoints except `/health` require `X-API-Key` header.

---

## License

MIT

---

*Built for developers who want to know what their AI actually did.*
