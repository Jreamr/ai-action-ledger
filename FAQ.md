# Common Questions

Answers to questions early users typically ask.

---

## What data do you store exactly?

By default, we store:

| Stored | Example |
|--------|---------|
| `agent_id` | `"my-agent"` |
| `action_type` | `"llm_call"` |
| `tool_name` | `"search"` (optional) |
| `timestamp` | `"2026-01-13T19:34:21.862142Z"` |
| `environment` | `"production"` (optional) |
| `input_hash` | `"a]3f2..."` (64 hex chars) |
| `output_hash` | `"b7c1..."` (64 hex chars) |
| `event_hash` | `"d4e5..."` (64 hex chars) |
| `previous_event_hash` | `"c2b1..."` (64 hex chars) |

**We do NOT store:**
- Raw prompts
- Raw outputs
- User data
- API keys used in your LLM calls

The hashes let you prove what content was processed without exposing it.

---

## What happens if the API is down?

Your application should handle this gracefully:

```python
try:
    client.log_event(...)
except Exception as e:
    # Log locally, alert, or continue without logging
    print(f"Ledger unavailable: {e}")
```

**Recommendation:** Don't let logging failures break your application. Log errors locally and continue.

---

## What happens if I log the same event twice?

Each event gets a unique `event_id` and `timestamp` from the server. Duplicate content will create separate events with different hashes (because the timestamp differs).

This is by design — we record what happened, when.

---

## Can I delete events?

No. The log is append-only. This is intentional — if events could be deleted, the audit trail would be meaningless.

If you need to "retract" something, log a new event indicating the retraction.

---

## Can I update events?

No. Events are immutable. If you logged incorrect data, log a correction event.

---

## What if my agent doesn't log an action?

We can't detect that. AI Action Ledger proves **integrity** (logged events weren't changed), not **completeness** (all actions were logged).

If your agent skips a log call, we have no way to know.

---

## How do I know the chain is valid?

Call the verify endpoint:

```bash
curl "http://localhost:8000/verify?agent_id=my-agent" \
  -H "X-API-Key: your-api-key"
```

This checks:
1. Each event's hash matches its content
2. Each event correctly references the previous event's hash

If either check fails, you'll get details about the first invalid event.

---

## What breaks the chain?

The chain is broken if:
- An event's content was modified (hash won't match)
- An event was deleted (next event's `previous_event_hash` won't match anything)
- An event was inserted (hashes won't align)
- Events were reordered (chain links break)

All of these are detected by `/verify`.

---

## Is this a blockchain?

No. It's a hash chain, which is simpler:
- Single append-only log (not distributed)
- No consensus mechanism
- No tokens or mining
- Just cryptographic linking of events

Think of it as a tamper-evident audit log, not a blockchain.

---

## Can I self-host this?

Yes. The self-hosted version is available now:

```bash
git clone https://github.com/[your-repo]/ai-action-ledger
cd ai-action-ledger
docker compose up --build
```

You control the data, the infrastructure, and the backups.

---

## Is there a hosted version?

A hosted version is available to early users on request. Contact us if you're interested.

---

## What about compliance (SOC2, HIPAA, etc.)?

We make no compliance claims at this stage. If you need certified compliance, you should:
- Self-host and apply your own controls
- Wait until we have formal certifications (not yet planned)

---

## What's the performance impact?

Each logged event is:
- One HTTP POST (~1-5ms on local network)
- One database insert
- One file append

For most applications, this is negligible. If you're logging thousands of events per second, contact us to discuss.

---

## Can I filter or search events?

Yes. The `/events` endpoint supports:
- `agent_id` — filter by agent
- `action_type` — filter by action type
- `start_time` / `end_time` — filter by time range
- `page` / `page_size` — pagination

The dashboard also provides a visual interface for browsing events.

---

## What if I have more questions?

Open an issue on GitHub or email [your-email@example.com].
