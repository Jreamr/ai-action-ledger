# AI Action Ledger v1.1 — Known Limitations

## Concurrency

**Single-writer per agent_id recommended.**

If two requests write events for the same `agent_id` simultaneously, both may read the same "previous" hash before either commits, resulting in a forked chain.

**Workarounds:**
- Use unique `agent_id` per writer/process
- Serialize writes at the application layer
- v2 will add row-level locking

## Completeness

This system proves **integrity** (events weren't modified after recording), not **completeness** (that all events were recorded). A malicious client could simply not log some actions.

## Archive Storage

Local filesystem archive is not truly immutable — files can be edited. The system *detects* tampering via `/verify/archive`, but doesn't *prevent* it. For production, use S3 with object lock or similar.
```

Save it.

---

## P1 — Config Consistency

**File: `.env`** (verify it says):
```
POSTGRES_USER=ledger
POSTGRES_PASSWORD=ledger_secret
POSTGRES_DB=ledger
API_KEY=dev-api-key-change-me
ARCHIVE_PATH=/archive