"""
NexusOps Agents - DNS Agent Handler

nexusops.dns: DNS 记录管理、域名生成
"""

import asyncio
import random
import string
from typing import List, Dict, Any

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class DNSAgentHandler(BaseAgentHandler):
    """DNS operations agent handler"""

    @property
    def agent_id(self) -> str:
        return "nexusops.dns"

    @property
    def capabilities(self) -> List[str]:
        return [
            "dns_record_create",
            "dns_record_delete",
            "dns_record_query",
            "random_domain_generate",
        ]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle DNS requests"""
        await asyncio.sleep(0.3)

        query = request.query.lower()
        context = request.request_context

        if "create" in query or "add" in query or "添加" in query:
            return self._create_record(context)
        elif "delete" in query or "remove" in query or "删除" in query:
            return self._delete_record(context)
        elif "query" in query or "lookup" in query or "查询" in query:
            return self._query_record(context)
        elif "random" in query or "generate" in query or "生成" in query:
            return self._generate_domain(context)
        else:
            return self._dns_status(context)

    def _create_record(self, context: Dict[str, Any]) -> ExecutorResult:
        """Create DNS record"""
        zone = context.get("zone_id", "example.com")
        record_name = context.get("resource_name", "www")
        record_type = context.get("resource_type", "A")

        return self._success(
            text=f"""## ✅ DNS Record Created

**Zone:** {zone}
**Record:** {record_name}
**Type:** {record_type}

### Record Details
- **Name:** {record_name}.{zone}
- **Type:** {record_type}
- **Value:** 192.168.1.100
- **TTL:** 300

DNS record has been created successfully.
""",
            structured_output={
                "type": "dns_record_created",
                "zone": zone,
                "record_name": record_name,
                "record_type": record_type,
                "status": "created",
            },
            metadata={"operation": "create_record"},
        )

    def _delete_record(self, context: Dict[str, Any]) -> ExecutorResult:
        """Delete DNS record"""
        zone = context.get("zone_id", "example.com")
        record_name = context.get("resource_name", "www")

        return self._success(
            text=f"""## 🗑️ DNS Record Deleted

**Zone:** {zone}
**Record:** {record_name}

The DNS record has been deleted successfully.
""",
            structured_output={
                "type": "dns_record_deleted",
                "zone": zone,
                "record_name": record_name,
                "status": "deleted",
            },
            metadata={"operation": "delete_record"},
        )

    def _query_record(self, context: Dict[str, Any]) -> ExecutorResult:
        """Query DNS record"""
        domain = context.get("resource_name", "example.com")

        return self._success(
            text=f"""## 🔍 DNS Query Result

**Domain:** {domain}

### Records Found
| Type | Name | Value | TTL |
|------|------|-------|-----|
| A    | {domain} | 192.168.1.100 | 300 |
| AAAA | {domain} | 2001:db8::1 | 300 |
| MX   | {domain} | mail.{domain} | 3600 |
""",
            structured_output={
                "type": "dns_query_result",
                "domain": domain,
                "records": [
                    {"type": "A", "name": domain, "value": "192.168.1.100", "ttl": 300},
                    {"type": "AAAA", "name": domain, "value": "2001:db8::1", "ttl": 300},
                    {"type": "MX", "name": domain, "value": f"mail.{domain}", "ttl": 3600},
                ],
            },
            metadata={"operation": "query_record"},
        )

    def _generate_domain(self, context: Dict[str, Any]) -> ExecutorResult:
        """Generate random domain/subdomain"""
        base_domain = context.get("codename", "test.nexusops.io")
        levels = context.get("namespace", 4)

        # Try to parse levels as int, default to 4
        try:
            levels = int(levels) if isinstance(levels, str) else 4
        except (ValueError, TypeError):
            levels = 4

        # Generate random subdomain parts
        parts = []
        for _ in range(levels):
            part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            parts.append(part)

        random_subdomain = '.'.join(parts)
        full_domain = f"{random_subdomain}.{base_domain}"

        return self._success(
            text=f"""## 🎲 Random Domain Generated

**Base Domain:** {base_domain}
**Levels:** {levels}

### Generated Domain
```
{full_domain}
```

This domain can be used for:
- Test environments
- Temporary services
- Canary deployments
""",
            structured_output={
                "type": "random_domain",
                "base_domain": base_domain,
                "levels": levels,
                "subdomain": random_subdomain,
                "full_domain": full_domain,
            },
            suggested_actions=[
                self._action("create-record", "invoke", "Create DNS Record",
                           {"agent_id": "nexusops.dns", "query": f"create {full_domain}"}),
            ],
            metadata={"operation": "generate_domain"},
        )

    def _dns_status(self, context: Dict[str, Any]) -> ExecutorResult:
        """Show DNS status"""
        return self._success(
            text="""## 📊 DNS Status

### Zones
| Zone | Records | Status |
|------|---------|--------|
| nexusops.io | 45 | Active |
| example.com | 12 | Active |

### Recent Changes
- Added A record for api.nexusops.io (2 hours ago)
- Updated CNAME for www.nexusops.io (1 day ago)

### DNS Provider
- Provider: Cloudflare
- Status: Connected
- Last sync: 5 minutes ago
""",
            metadata={"operation": "status"},
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "create_dns_record",
                "description": "Create a DNS record",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "zone_id": {"type": "string"},
                        "record_type": {"type": "string"},
                        "name": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["zone_id", "record_type", "name", "content"],
                },
            },
            {
                "name": "generate_random_subdomain",
                "description": "Generate a random subdomain",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base_domain": {"type": "string"},
                        "levels": {"type": "integer", "default": 4},
                    },
                    "required": ["base_domain"],
                },
            },
        ]
