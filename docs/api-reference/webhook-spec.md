# Webhook Specification

## Overview

NexusOps supports webhooks for event-driven integrations. This document describes the webhook specification, event types, and implementation guidelines.

---

## Webhook Events

### Event Types

| Event | Description |
|-------|-------------|
| `invocation.completed` | Agent invocation completed |
| `invocation.failed` | Agent invocation failed |
| `agent.installed` | Agent installed |
| `agent.uninstalled` | Agent uninstalled |
| `agent.activated` | Agent activated |
| `agent.deactivated` | Agent deactivated |
| `deployment.created` | Deployment created |
| `deployment.completed` | Deployment completed |
| `deployment.failed` | Deployment failed |
| `alert.triggered` | Alert triggered |

---

## Webhook Configuration

### Register Webhook

**Endpoint**: `POST /api/v1/webhooks`

**Request Body**:

```json
{
  "name": "My Webhook",
  "url": "https://your-server.com/webhooks/nexusops",
  "events": ["invocation.completed", "deployment.failed"],
  "secret": "your-webhook-secret",
  "active": true,
  "headers": {
    "X-Custom-Header": "value"
  }
}
```

**Response**:

```json
{
  "id": "wh-123",
  "name": "My Webhook",
  "url": "https://your-server.com/webhooks/nexusops",
  "events": ["invocation.completed", "deployment.failed"],
  "secret": "whsec_xxx",
  "active": true,
  "created_at": "2026-02-25T00:00:00Z"
}
```

### List Webhooks

**Endpoint**: `GET /api/v1/webhooks`

**Response**:

```json
{
  "webhooks": [
    {
      "id": "wh-123",
      "name": "My Webhook",
      "url": "https://your-server.com/webhooks/nexusops",
      "events": ["invocation.completed"],
      "active": true,
      "created_at": "2026-02-25T00:00:00Z"
    }
  ]
}
```

### Update Webhook

**Endpoint**: `PUT /api/v1/webhooks/{webhook_id}`

### Delete Webhook

**Endpoint**: `DELETE /api/v1/webhooks/{webhook_id}`

---

## Webhook Payload

### Headers

```http
Content-Type: application/json
X-NexusOps-Event: invocation.completed
X-NexusOps-Signature: sha256=xxxxx
X-NexusOps-Delivery: delivery-uuid
X-NexusOps-Timestamp: 1708838400
```

| Header | Description |
|--------|-------------|
| `X-NexusOps-Event` | Event type |
| `X-NexusOps-Signature` | HMAC signature |
| `X-NexusOps-Delivery` | Unique delivery ID |
| `X-NexusOps-Timestamp` | Unix timestamp |

### Payload Structure

```json
{
  "id": "evt-123",
  "event": "invocation.completed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    // Event-specific data
  }
}
```

---

## Event Payloads

### invocation.completed

```json
{
  "id": "evt-123",
  "event": "invocation.completed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "invocation_id": "inv-456",
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "agent_id": "nexusops.chat",
    "status": "success",
    "query": "What is the status?",
    "latency_ms": 250,
    "tokens_used": {
      "input": 100,
      "output": 50
    },
    "user_id": "user-123",
    "project_id": "proj-456"
  }
}
```

### invocation.failed

```json
{
  "id": "evt-123",
  "event": "invocation.failed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "invocation_id": "inv-456",
    "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
    "agent_id": "nexusops.k8s",
    "status": "error",
    "error": {
      "code": "EXEC_TIMEOUT",
      "message": "Execution timed out"
    },
    "user_id": "user-123",
    "project_id": "proj-456"
  }
}
```

### deployment.created

```json
{
  "id": "evt-123",
  "event": "deployment.created",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "deployment_id": "deploy-456",
    "codename": "v1.2.3",
    "region": "us-east",
    "status": "pending",
    "triggered_by": "user-123",
    "project_id": "proj-456"
  }
}
```

### deployment.completed

```json
{
  "id": "evt-123",
  "event": "deployment.completed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "deployment_id": "deploy-456",
    "codename": "v1.2.3",
    "region": "us-east",
    "status": "completed",
    "duration_seconds": 180,
    "triggered_by": "user-123",
    "project_id": "proj-456"
  }
}
```

### deployment.failed

```json
{
  "id": "evt-123",
  "event": "deployment.failed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "deployment_id": "deploy-456",
    "codename": "v1.2.3",
    "region": "us-east",
    "status": "failed",
    "error": {
      "code": "HEALTH_CHECK_FAILED",
      "message": "Health check failed after 5 attempts"
    },
    "triggered_by": "user-123",
    "project_id": "proj-456"
  }
}
```

### agent.installed

```json
{
  "id": "evt-123",
  "event": "agent.installed",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "agent_id": "third-party.analytics",
    "name": "Analytics Agent",
    "version": "1.0.0",
    "installed_by": "user-123",
    "project_id": "proj-456"
  }
}
```

### alert.triggered

```json
{
  "id": "evt-123",
  "event": "alert.triggered",
  "timestamp": "2026-02-25T00:00:00Z",
  "data": {
    "alert_id": "alert-456",
    "alert_name": "High Error Rate",
    "severity": "critical",
    "message": "Error rate exceeded 5% threshold",
    "metric": {
      "name": "error_rate",
      "value": 7.5,
      "threshold": 5.0
    },
    "project_id": "proj-456"
  }
}
```

---

## Signature Verification

### HMAC Signature

NexusOps signs webhook payloads using HMAC-SHA256. The signature is included in the `X-NexusOps-Signature` header.

**Format**: `sha256=<hex_digest>`

### Verification (Python)

```python
import hmac
import hashlib

def verify_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Extract hash from signature header
    signature_hash = signature.replace("sha256=", "")

    return hmac.compare_digest(expected, signature_hash)

# Usage
@app.route("/webhooks/nexusops", methods=["POST"])
def handle_webhook():
    signature = request.headers.get("X-NexusOps-Signature")
    secret = "your-webhook-secret"

    if not verify_signature(request.data, signature, secret):
        return "Invalid signature", 401

    event = request.json
    # Process event...
    return "OK", 200
```

### Verification (Node.js)

```javascript
const crypto = require('crypto');

function verifySignature(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  const signatureHash = signature.replace('sha256=', '');

  return crypto.timingSafeEqual(
    Buffer.from(expected, 'hex'),
    Buffer.from(signatureHash, 'hex')
  );
}

// Express middleware
app.post('/webhooks/nexusops', (req, res) => {
  const signature = req.headers['x-nexusops-signature'];
  const secret = 'your-webhook-secret';

  // Get raw body
  const payload = JSON.stringify(req.body);

  if (!verifySignature(payload, signature, secret)) {
    return res.status(401).send('Invalid signature');
  }

  const event = req.body;
  // Process event...
  res.status(200).send('OK');
});
```

---

## Webhook Handler Implementation

### Python (FastAPI)

```python
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from enum import Enum

app = FastAPI()

class EventType(str, Enum):
    INVOCATION_COMPLETED = "invocation.completed"
    INVOCATION_FAILED = "invocation.failed"
    DEPLOYMENT_CREATED = "deployment.created"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"

@app.post("/webhooks/nexusops")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    # Verify signature
    signature = request.headers.get("X-NexusOps-Signature")
    body = await request.body()

    if not verify_signature(body, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = await request.json()
    event_type = event["event"]

    # Process in background
    background_tasks.add_task(process_event, event)

    return {"status": "received"}

async def process_event(event: dict):
    event_type = event["event"]
    data = event["data"]

    if event_type == "invocation.completed":
        await handle_invocation_completed(data)
    elif event_type == "deployment.failed":
        await handle_deployment_failed(data)
    # ... other handlers

async def handle_invocation_completed(data: dict):
    # Process invocation completed event
    pass

async def handle_deployment_failed(data: dict):
    # Process deployment failed event
    # Send alert, etc.
    pass
```

### Node.js (Express)

```javascript
const express = require('express');
const app = express();

// Raw body parser for signature verification
app.use('/webhooks', express.raw({ type: 'application/json' }));

app.post('/webhooks/nexusops', async (req, res) => {
  const signature = req.headers['x-nexusops-signature'];

  // Verify signature
  if (!verifySignature(req.body, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.body.toString());

  try {
    await processEvent(event);
    res.status(200).send('OK');
  } catch (error) {
    console.error('Error processing webhook:', error);
    res.status(500).send('Error');
  }
});

async function processEvent(event) {
  const { event: eventType, data } = event;

  switch (eventType) {
    case 'invocation.completed':
      await handleInvocationCompleted(data);
      break;
    case 'deployment.failed':
      await handleDeploymentFailed(data);
      break;
    default:
      console.log(`Unhandled event: ${eventType}`);
  }
}

async function handleInvocationCompleted(data) {
  // Process event
}

async function handleDeploymentFailed(data) {
  // Send alert, etc.
}
```

---

## Retry Policy

### Delivery Attempts

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 15 minutes |
| 5 | 1 hour |

### Response Requirements

Your webhook endpoint must:

1. Return HTTP 200 within 10 seconds
2. Return any 2xx status code for success
3. Return 4xx for permanent failures (no retry)
4. Return 5xx for temporary failures (will retry)

### Timeout

- Connection timeout: 5 seconds
- Response timeout: 10 seconds

---

## Testing Webhooks

### Using ngrok

```bash
# Start ngrok
ngrok http 3000

# Register webhook with ngrok URL
curl -X POST https://api.nexusops.io/api/v1/webhooks \
  -H "Authorization: Bearer your-token" \
  -d '{
    "name": "Test Webhook",
    "url": "https://xxx.ngrok.io/webhooks/nexusops",
    "events": ["invocation.completed"]
  }'
```

### Manual Testing

**Endpoint**: `POST /api/v1/webhooks/{webhook_id}/test`

**Response**:

```json
{
  "success": true,
  "delivery_id": "delivery-123",
  "event": {
    "id": "evt-test",
    "event": "invocation.completed",
    "data": {
      "test": true
    }
  }
}
```

---

## Best Practices

### 1. Verify Signatures

Always verify webhook signatures to prevent forgery:

```python
if not verify_signature(payload, signature, secret):
    raise HTTPException(401)
```

### 2. Handle Idempotency

Webhooks may be delivered multiple times. Use the event ID for deduplication:

```python
if await is_event_processed(event["id"]):
    return {"status": "already_processed"}

await process_event(event)
await mark_event_processed(event["id"])
```

### 3. Process Asynchronously

Process webhook events in the background to respond quickly:

```python
@app.post("/webhooks/nexusops")
async def handle(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_event, event)
    return {"status": "received"}
```

### 4. Log Events

Log all webhook events for debugging:

```python
logger.info(
    "webhook_received",
    event_id=event["id"],
    event_type=event["event"],
    delivery_id=request.headers.get("X-NexusOps-Delivery")
)
```

### 5. Handle Unknown Events

Gracefully handle unknown event types:

```python
if event_type not in HANDLERS:
    logger.warning(f"Unknown event type: {event_type}")
    return {"status": "ignored"}
```

---

## Next Steps

- [Gateway API](./gateway-api.md) - Full API reference
- [SDK Reference](./sdk-reference.md) - SDK documentation
- [Troubleshooting](../best-practices/troubleshooting.md) - Debug webhook issues
