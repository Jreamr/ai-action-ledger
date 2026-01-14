# AI Action Ledger

**A tamper-evident audit log for AI agent actions.**

---

## What AI Action Ledger Does

- Records AI actions (LLM calls, tool use, chain steps) to an append-only log
- Cryptographically hash-chains each event to the previous one
- Detects if any logged event was modified after the fact
- Stores hashes + metadata by default — not raw prompts or outputs
- Provides a simple SDK for LangChain and custom agents
- Includes a dashboard to view, filter, and verify event chains

If an event is logged, its integrity can be independently verified later.

---

## What It's Useful For

**Debugging agents** — See exactly what your agent did, in order, with timestamps.

**Incident review** — When something goes wrong, trace the chain of actions that led there.

**Internal accountability** — Know what your AI systems did, and prove it wasn't altered later.

**Customer trust** — Show customers a verifiable log of what your AI did on their behalf.

---

## What It Does NOT Do

This is important. AI Action Ledger:

- **Does not prevent** AI from taking actions — it only records what happened
- **Does not guarantee completeness** — we can only log what's sent to us
- **Does not store raw prompts/outputs** by default — only hashes (opt-in for full content)
- **Does not have compliance certifications** — no SOC2, HIPAA, or similar claims
- **Does not enforce alignment** — this is an audit trail, not a safety system

If an event is logged, we can prove it wasn't silently changed. We cannot prove that all events were logged.

---

## How It Works

```
Your Agent → SDK → API → Database + Archive → Dashboard
                           ↓
                    Hash chain verified
```

1. Your agent calls the SDK (or API directly) when it takes an action
2. Logging is explicit and opt-in — only events your agent sends are recorded
3. The SDK hashes the input/output and sends metadata to the API
4. The API chains this event to the previous one and stores it
5. You can view events in the dashboard or verify the chain via API

Each event includes:
- Agent ID, action type, timestamp
- SHA-256 hashes of input and output
- Hash of the previous event (creating the chain)
- Computed hash of the current event

---

## Privacy & Data Model

By default, we store:
- **Hashes** of inputs and outputs (64-character hex strings)
- **Metadata** (agent ID, action type, tool name, timestamps)

We do **not** store raw prompts or outputs unless you explicitly send them.

This means:
- You can prove *that* an action happened and *what* it contained (via hash)
- You can prove the log wasn't tampered with
- You don't have to send us sensitive data

If you need full content logging, that's opt-in on your side.

---

## Who This Is For

**Good fit:**
- Teams building AI agents who want an audit trail
- Developers who need to debug agent behavior in production
- Products where customers ask "what did the AI actually do?"
- Anyone who wants tamper-evident logs without building it themselves

**Not a fit:**
- Teams looking for AI safety enforcement or guardrails
- Organizations requiring compliance certifications today
- Use cases where completeness (logging every action) must be guaranteed

---

## Current Status

AI Action Ledger is **early and working**.

- Self-hosted version: available now (Docker Compose)
- Python SDK: available now (LangChain callback included)
- Hosted version: available to early users on request

This is intended for early users who want to try it, give feedback, and help shape what comes next.

---

## Get Started

**Self-host now:**
```bash
git clone https://github.com/[your-repo]/ai-action-ledger
cd ai-action-ledger
docker compose up --build
```

**Read the docs:** [START_HERE.md](./START_HERE.md)

**Questions?** Open an issue on GitHub

**[→ Request Early Access](https://github.com/Jreamr/ai-action-ledger/discussions/1)**

---

*Built for developers who want to know what their AI actually did.*