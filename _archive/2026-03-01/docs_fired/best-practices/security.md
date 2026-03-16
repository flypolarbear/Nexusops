# Security Best Practices

## Overview

This document outlines security best practices for developing and deploying NexusOps agents. Following these guidelines helps protect your systems, data, and users.

---

## Authentication

### API Keys

API keys should be treated as sensitive credentials:

```python
# Good: Load from environment
import os
api_key = os.environ.get("NEXUSOPS_API_KEY")

# Bad: Hardcode in source
api_key = "sk-xxx"  # Never do this!
```

**Best Practices**:
- Store API keys in environment variables or secure vault
- Rotate keys regularly (every 90 days recommended)
- Use different keys for different environments
- Never commit keys to version control

### Token Management

```python
# Implement token refresh
class TokenManager:
    def __init__(self, refresh_threshold_seconds: int = 300):
        self._token = None
        self._expires_at = None
        self._refresh_threshold = refresh_threshold_seconds

    async def get_token(self) -> str:
        if self._should_refresh():
            await self._refresh_token()
        return self._token

    def _should_refresh(self) -> bool:
        if not self._token or not self._expires_at:
            return True
        return time.time() > (self._expires_at - self._refresh_threshold)

    async def _refresh_token(self):
        # Refresh token from auth service
        pass
```

---

## Authorization

### Project-Level Permissions

Always verify user permissions before processing requests:

```python
class SecureAgentHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        context = request.request_context
        user_id = context.get("user_id")
        project_id = context.get("project_id")

        # Verify permission
        if not await self._check_permission(user_id, project_id, "read"):
            return self._error(
                code="AUTH_PERMISSION_DENIED",
                message="You don't have permission to access this project",
                details={"project_id": project_id}
            )

        # Process request
        return await self._process(request)

    async def _check_permission(
        self,
        user_id: str,
        project_id: str,
        action: str
    ) -> bool:
        # Check against permission service
        return await permission_service.check(user_id, project_id, action)
```

### Role-Based Access Control

```python
from enum import Enum

class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    Role.VIEWER: ["read"],
    Role.EDITOR: ["read", "write", "deploy"],
    Role.ADMIN: ["read", "write", "deploy", "admin"],
}

def has_permission(role: Role, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role, [])
```

---

## Input Validation

### Validate All Inputs

Never trust user input. Always validate:

```python
from pydantic import BaseModel, validator, constr

class DeploymentRequest(BaseModel):
    codename: constr(min_length=1, max_length=100, regex=r"^[a-zA-Z0-9_-]+$")
    region: constr(min_length=1, max_length=50)
    replicas: int

    @validator("replicas")
    def validate_replicas(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Replicas must be between 1 and 100")
        return v

class SecureDeployHandler(BaseAgentHandler):
    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        try:
            # Parse and validate input
            deploy_request = self._parse_request(request.query)
            return await self._deploy(deploy_request)
        except ValidationError as e:
            return self._error(
                code="INPUT_SCHEMA_VIOLATION",
                message="Invalid request parameters",
                details={"errors": e.errors()}
            )

    def _parse_request(self, query: str) -> DeploymentRequest:
        # Parse query into structured request
        params = self._extract_params(query)
        return DeploymentRequest(**params)
```

### Sanitize Output

```python
import html
import re

def sanitize_output(text: str) -> str:
    """Sanitize output to prevent XSS."""
    # Escape HTML
    text = html.escape(text)

    # Remove potential script injections
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    return text
```

---

## Secrets Management

### Never Log Secrets

```python
# Good: Mask sensitive data
def safe_log(data: dict) -> dict:
    sensitive_keys = {"password", "api_key", "token", "secret"}
    return {
        k: "***MASKED***" if k in sensitive_keys else v
        for k, v in data.items()
    }

logger.info("Request data", extra={"data": safe_log(request_data)})
```

### Use Environment Variables

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    database_url: str
    api_key: str
    secret_key: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            api_key=os.environ["API_KEY"],
            secret_key=os.environ["SECRET_KEY"]
        )
```

### Use Secret Managers

```python
# AWS Secrets Manager
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> dict:
    client = boto4.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret: {e}")

# HashiCorp Vault
import hvac

def get_secret_from_vault(path: str) -> dict:
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
    response = client.secrets.kv.v2.read_secret_version(path=path)
    return response["data"]["data"]
```

---

## Network Security

### TLS/HTTPS

Always use HTTPS for external communication:

```python
import httpx

# Good: Verify SSL
client = httpx.AsyncClient(verify=True)

# For development only: Disable verification (never in production!)
# client = httpx.AsyncClient(verify=False)
```

### Request Timeouts

Always set timeouts to prevent hanging:

```python
import httpx

# Set reasonable timeouts
client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=5.0,     # Connection timeout
        read=30.0,       # Read timeout
        write=10.0,      # Write timeout
        pool=5.0         # Pool timeout
    )
)
```

### Allowlists

Use allowlists for external endpoints:

```python
ALLOWED_DOMAINS = {
    "api.kubernetes.io",
    "api.aws.amazon.com",
    "logs.example.com"
}

def is_allowed_url(url: str) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.hostname in ALLOWED_DOMAINS

async def safe_request(url: str, **kwargs):
    if not is_allowed_url(url):
        raise ValueError(f"URL not in allowlist: {url}")
    async with httpx.AsyncClient() as client:
        return await client.get(url, **kwargs)
```

---

## Data Protection

### Encrypt Sensitive Data

```python
from cryptography.fernet import Fernet

class DataEncryptor:
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> bytes:
        return self.fernet.encrypt(data.encode())

    def decrypt(self, encrypted: bytes) -> str:
        return self.fernet.decrypt(encrypted).decode()

# Usage
encryptor = DataEncryptor(SECRET_KEY)
encrypted = encryptor.encrypt("sensitive data")
decrypted = encryptor.decrypt(encrypted)
```

### Data Masking

```python
def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only last N characters."""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return "*" * (len(data) - visible_chars) + data[-visible_chars:]

# Examples
mask_sensitive_data("sk-1234567890")  # "*******7890"
mask_sensitive_data("user@example.com")  # "************.com"
```

### Audit Logging

```python
import structlog

audit_logger = structlog.get_logger("audit")

async def log_audit_event(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    details: dict = None
):
    await audit_logger.ainfo(
        "audit_event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        timestamp=datetime.utcnow().isoformat()
    )

# Usage
await log_audit_event(
    action="deploy",
    user_id="user-123",
    resource_type="deployment",
    resource_id="deploy-456",
    details={"region": "us-east", "version": "v1.2.3"}
)
```

---

## Rate Limiting

### Implement Rate Limiting

```python
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = datetime.utcnow()
        # Clean old requests
        self.requests[key] = [
            t for t in self.requests[key]
            if now - t < self.window
        ]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

    def retry_after(self, key: str) -> int:
        if not self.requests[key]:
            return 0
        oldest = min(self.requests[key])
        return int((oldest + self.window - datetime.utcnow()).total_seconds())

# Usage
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

if not rate_limiter.is_allowed(user_id):
    return self._error(
        code="AUTH_QUOTA_EXCEEDED",
        message="Rate limit exceeded",
        retry_after=rate_limiter.retry_after(user_id)
    )
```

---

## Error Handling

### Don't Expose Internal Details

```python
# Good: Generic error message
try:
    await process_request(request)
except DatabaseError as e:
    logger.error("Database error", exc_info=True)
    return self._error(
        code="SYSTEM_INTERNAL_ERROR",
        message="An internal error occurred. Please try again."
    )

# Bad: Exposes internal details
except DatabaseError as e:
    return self._error(
        code="SYSTEM_INTERNAL_ERROR",
        message=f"Database error: {e}"  # Don't do this!
    )
```

---

## Dependency Security

### Pin Dependencies

```txt
# requirements.txt
httpx==0.25.0
pydantic==2.5.0
fastapi==0.109.0
```

### Regular Updates

```bash
# Check for vulnerabilities
pip install safety
safety check

# Or with pip-audit
pip install pip-audit
pip-audit
```

### Dependency Scanning

```yaml
# GitHub Actions
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: snyk/actions/python@master
        with:
          args: --severity-threshold=high
```

---

## Security Checklist

### Development

- [ ] All inputs are validated
- [ ] Secrets are loaded from environment
- [ ] TLS is used for external communication
- [ ] Timeouts are set on all requests
- [ ] Error messages don't expose internals
- [ ] Audit logging is implemented

### Deployment

- [ ] Secrets are stored in secret manager
- [ ] Network policies are configured
- [ ] Rate limiting is enabled
- [ ] Logging doesn't include sensitive data
- [ ] Dependencies are scanned
- [ ] Security headers are set

### Runtime

- [ ] Monitoring alerts are configured
- [ ] Access logs are retained
- [ ] Regular security audits scheduled
- [ ] Incident response plan is documented

---

## Next Steps

- [Performance Best Practices](./performance.md) - Optimize performance
- [Troubleshooting](./troubleshooting.md) - Debug issues
- [Error Handling](../agent-development/error-handling.md) - Handle errors properly
