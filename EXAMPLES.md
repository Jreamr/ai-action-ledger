# Integration Examples

Practical examples for integrating AI Action Ledger into your application.

---

## Example 1: Plain Python (No SDK)

If you don't want to use the SDK, you can call the API directly.

```python
import hashlib
import requests

LEDGER_URL = "http://localhost:8000"
API_KEY = "dev-api-key-change-me"

def sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def log_action(agent_id: str, action_type: str, input_text: str, output_text: str):
    response = requests.post(
        f"{LEDGER_URL}/events",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "agent_id": agent_id,
            "action_type": action_type,
            "input_hash": sha256(input_text),
            "output_hash": sha256(output_text)
        }
    )
    response.raise_for_status()
    return response.json()

# Usage
event = log_action(
    agent_id="my-agent",
    action_type="llm_call",
    input_text="What is the capital of France?",
    output_text="The capital of France is Paris."
)
print(f"Logged event: {event['event_id']}")
```

---

## Example 2: Using the SDK

The SDK handles hashing and API calls for you.

```python
from action_ledger import LedgerClient

client = LedgerClient(
    ledger_url="http://localhost:8000",
    api_key="dev-api-key-change-me"
)

# Log an action
event = client.log_event(
    agent_id="my-agent",
    action_type="llm_call",
    input_hash=client.hash_content("What is 2+2?"),
    output_hash=client.hash_content("4")
)
print(f"Logged: {event['event_id']}")

# Verify the chain
result = client.verify_chain("my-agent")
print(f"Chain valid: {result['is_valid']}")
```

---

## Example 3: Minimal Agent with Logging

A simple agent loop that logs every action.

```python
from action_ledger import LedgerClient

client = LedgerClient(
    ledger_url="http://localhost:8000",
    api_key="dev-api-key-change-me"
)

AGENT_ID = "simple-agent"

def call_llm(prompt: str) -> str:
    # Replace with your actual LLM call
    response = f"Response to: {prompt}"
    return response

def agent_step(prompt: str) -> str:
    # Call the LLM
    response = call_llm(prompt)
    
    # Log the action
    client.log_event(
        agent_id=AGENT_ID,
        action_type="llm_call",
        input_hash=client.hash_content(prompt),
        output_hash=client.hash_content(response)
    )
    
    return response

# Run the agent
tasks = [
    "What is the weather today?",
    "Summarize this document.",
    "Send an email to the team."
]

for task in tasks:
    result = agent_step(task)
    print(f"Task: {task}")
    print(f"Result: {result}\n")

# Verify at the end
verification = client.verify_chain(AGENT_ID)
print(f"All actions logged. Chain valid: {verification['is_valid']}")
print(f"Total events: {verification['events_checked']}")
```

---

## Example 4: LangChain Integration

If you're using LangChain, use the callback handler.

```python
from langchain.llms import OpenAI
from action_ledger import ActionLedgerCallback

# Set up the callback
ledger_callback = ActionLedgerCallback(
    ledger_url="http://localhost:8000",
    api_key="dev-api-key-change-me",
    agent_id="langchain-agent",
    environment="development"
)

# Use with any LangChain LLM
llm = OpenAI(
    temperature=0,
    callbacks=[ledger_callback]
)

# Every call is automatically logged
response = llm.invoke("What is the capital of France?")
print(response)
```

**Note:** Requires `pip install langchain openai`

---

## Verifying Your Integration

After logging events, verify the chain is intact:

```bash
curl "http://localhost:8000/verify?agent_id=my-agent" \
  -H "X-API-Key: dev-api-key-change-me"
```

Expected response:
```json
{
  "agent_id": "my-agent",
  "is_valid": true,
  "events_checked": 3,
  "first_invalid_event_id": null,
  "error_message": null
}
```

---

## What Gets Logged

Each event contains:

| Field | Source | Description |
|-------|--------|-------------|
| `event_id` | Server | Unique ID (UUID) |
| `agent_id` | You | Which agent |
| `action_type` | You | What kind of action |
| `timestamp` | Server | When (UTC) |
| `input_hash` | You | SHA-256 of input |
| `output_hash` | You | SHA-256 of output |
| `previous_event_hash` | Server | Links to prior event |
| `event_hash` | Server | Hash of this event |

**Privacy note:** Raw inputs/outputs are never stored unless you explicitly include them.
