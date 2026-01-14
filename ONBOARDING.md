# Early Access Onboarding

Welcome to AI Action Ledger early access. This doc explains what you're getting, how to use it, and what to expect.

---

## What You're Getting

- A dedicated instance of AI Action Ledger running on our infrastructure
- API access with your own API key
- Dashboard access to view and verify your events
- Direct support via email

---

## Your Credentials

We'll provide:

| Item | Value |
|------|-------|
| API URL | `https://[your-instance].actionledger.io` |
| API Key | `[provided separately]` |
| Dashboard | `https://[your-instance].actionledger.io:3000` |

Keep your API key secure. Don't commit it to public repos.

---

## Quick Start

**1. Test the connection:**

```bash
curl https://[your-instance].actionledger.io/health
```

Expected: `{"status":"healthy","database":"healthy","archive":"healthy"}`

**2. Log your first event:**

```bash
curl -X POST https://[your-instance].actionledger.io/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: [your-api-key]" \
  -d '{
    "agent_id": "test-agent",
    "action_type": "test",
    "input_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "output_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  }'
```

**3. Verify the chain:**

```bash
curl "https://[your-instance].actionledger.io/verify?agent_id=test-agent" \
  -H "X-API-Key: [your-api-key]"
```

**4. View in dashboard:**

Open `https://[your-instance].actionledger.io:3000` in your browser.

---

## Using the SDK

Install:

```bash
pip install requests
```

Use:

```python
from action_ledger import LedgerClient

client = LedgerClient(
    ledger_url="https://[your-instance].actionledger.io",
    api_key="[your-api-key]"
)

client.log_event(
    agent_id="my-agent",
    action_type="llm_call",
    input_hash=client.hash_content("What is 2+2?"),
    output_hash=client.hash_content("4")
)
```

We'll provide the SDK files separately, or you can copy from the examples.

---

## What Data We Store

By default:

| Stored | Not Stored |
|--------|------------|
| Agent ID | Raw prompts |
| Action type | Raw outputs |
| Timestamps | User data |
| Hashes (input/output) | Your LLM API keys |
| Event chain hashes | |

We only see hashes unless you explicitly send raw content.

---

## Support

During early access:

- Email: [your-email]
- Response time: Best effort, typically within 24 hours
- No SLA guarantees (see Early Access Disclaimer)

---

## Next Steps

1. Test the health endpoint
2. Log a few test events
3. Verify the chain works
4. Integrate into your application
5. Let us know what's working and what's not

We want your feedback. This is early access — your input shapes the product.
