"""
NexusOps Agents - Logs Agent Handler

nexusops.logs: Log query and analysis
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class LogsAgentHandler(BaseAgentHandler):
    """Logs agent handler for log query and analysis"""

    # Log levels
    LOG_LEVELS = ["ERROR", "WARN", "INFO", "DEBUG"]

    # Mock services
    MOCK_SERVICES = ["api", "worker", "web", "scheduler", "database", "cache"]

    # Mock log messages by level
    MOCK_MESSAGES = {
        "ERROR": [
            "Connection refused to database",
            "Failed to process request: timeout exceeded",
            "Authentication failed for user",
            "Out of memory error in worker process",
            "SSL certificate verification failed",
        ],
        "WARN": [
            "High memory usage detected: 85%",
            "Slow query detected: 2.5s execution time",
            "Rate limit approaching: 450/500 requests",
            "Deprecated API endpoint called",
            "Retry attempt 3/5 for external service",
        ],
        "INFO": [
            "Service started successfully",
            "Request processed in 150ms",
            "User login successful",
            "Configuration reloaded",
            "Health check passed",
            "Cache hit ratio: 92%",
        ],
        "DEBUG": [
            "Processing request payload",
            "Database query executed",
            "Cache lookup performed",
            "Validating user input",
            "Serializing response object",
        ],
    }

    @property
    def agent_id(self) -> str:
        return "nexusops.logs"

    @property
    def capabilities(self) -> List[str]:
        return ["query_logs", "search_errors", "tail_logs", "filter_by_level", "filter_by_service", "search_keywords", "time_range"]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle logs requests"""
        await asyncio.sleep(0.2)

        query = request.query.lower()
        context = request.request_context

        # Parse query intent
        if "error" in query:
            return self._query_by_level(context, "ERROR")
        elif "warn" in query or "warning" in query:
            return self._query_by_level(context, "WARN")
        elif "debug" in query:
            return self._query_by_level(context, "DEBUG")
        elif "search" in query or "find" in query or "keyword" in query:
            return self._search_logs(context)
        elif "service" in query:
            return self._query_by_service(context)
        elif "recent" in query or "tail" in query:
            return self._query_recent(context)
        elif "range" in query or "between" in query or "from" in query:
            return self._query_time_range(context)
        else:
            return self._query_general(context)

    def _generate_mock_logs(
        self,
        count: int = 10,
        level: Optional[str] = None,
        service: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Generate mock log entries"""
        logs = []

        # Default time range: last hour
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        time_range = (end_time - start_time).total_seconds()

        for i in range(count):
            # Determine log level
            if level:
                log_level = level
            else:
                # Weighted distribution
                weights = [5, 15, 60, 20]  # ERROR, WARN, INFO, DEBUG
                log_level = random.choices(self.LOG_LEVELS, weights=weights)[0]

            # Determine service
            if service:
                log_service = service
            else:
                log_service = random.choice(self.MOCK_SERVICES)

            # Generate timestamp within range
            random_seconds = random.uniform(0, time_range)
            timestamp = start_time + timedelta(seconds=random_seconds)

            # Generate message
            messages = self.MOCK_MESSAGES.get(log_level, self.MOCK_MESSAGES["INFO"])
            message = random.choice(messages)

            # Apply keyword filter if specified
            if keyword and keyword.lower() not in message.lower():
                # Skip or adjust message to include keyword
                message = f"{message} [keyword: {keyword}]"

            log_entry = {
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "level": log_level,
                "service": log_service,
                "message": message,
                "metadata": {
                    "trace_id": f"trace-{random.randint(10000, 99999)}",
                    "span_id": f"span-{random.randint(1000, 9999)}",
                    "host": f"pod-{log_service}-{random.randint(1, 5)}",
                },
            }
            logs.append(log_entry)

        # Sort by timestamp descending
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs

    def _query_general(self, context: Dict[str, Any]) -> ExecutorResult:
        """General log query"""
        service = context.get("resource_name")
        logs = self._generate_mock_logs(count=20, service=service)

        error_count = sum(1 for l in logs if l['level'] == 'ERROR')
        warn_count = sum(1 for l in logs if l['level'] == 'WARN')
        info_count = sum(1 for l in logs if l['level'] == 'INFO')
        debug_count = sum(1 for l in logs if l['level'] == 'DEBUG')

        return self._success(
            text=f"""## Log Query Results

Found **{len(logs)}** log entries.

### Recent Logs
```
{self._format_logs_as_text(logs[:10])}
```

### Summary
| Level | Count |
|-------|-------|
| ERROR | {error_count} |
| WARN  | {warn_count} |
| INFO  | {info_count} |
| DEBUG | {debug_count} |
""",
            structured_output={
                "type": "log_query_result",
                "total_count": len(logs),
                "logs": logs,
                "filters": {
                    "service": service,
                },
            },
            suggested_actions=[
                self._action(
                    "filter-errors",
                    "invoke",
                    "Filter Errors",
                    {"agent_id": "nexusops.logs", "query": "logs level=ERROR"},
                ),
                self._action(
                    "search-keyword",
                    "invoke",
                    "Search Logs",
                    {"agent_id": "nexusops.logs", "query": "search <keyword>"},
                ),
                self._action(
                    "view-service",
                    "invoke",
                    "Filter by Service",
                    {"agent_id": "nexusops.logs", "query": "logs service=api"},
                ),
            ],
            metadata={"operation": "query_general"},
        )

    def _query_by_level(self, context: Dict[str, Any], level: str) -> ExecutorResult:
        """Query logs by level"""
        service = context.get("resource_name")
        logs = self._generate_mock_logs(count=15, level=level, service=service)

        level_emoji = {"ERROR": "red_circle", "WARN": "orange_circle", "INFO": "blue_circle", "DEBUG": "white_circle"}
        emoji = level_emoji.get(level, "white_circle")

        return self._success(
            text=f"""## {level} Logs

Found **{len(logs)}** {level} level log entries.

### {level} Logs
```
{self._format_logs_as_text(logs)}
```

### Affected Services
| Service | Count |
|---------|-------|
{self._format_service_summary(logs)}
""",
            structured_output={
                "type": "log_level_result",
                "level": level,
                "total_count": len(logs),
                "logs": logs,
            },
            suggested_actions=[
                self._action(
                    "view-details",
                    "invoke",
                    "View Full Details",
                    {"agent_id": "nexusops.logs", "query": f"logs level={level} --full"},
                ),
                self._action(
                    "search-related",
                    "invoke",
                    "Search Related",
                    {"agent_id": "nexusops.logs", "query": f"search {level.lower()}"},
                ),
            ],
            metadata={"operation": "query_by_level", "level": level},
        )

    def _query_by_service(self, context: Dict[str, Any]) -> ExecutorResult:
        """Query logs by service"""
        service = context.get("resource_name", "api")
        logs = self._generate_mock_logs(count=20, service=service)

        return self._success(
            text=f"""## Service Logs: {service}

Found **{len(logs)}** log entries for service **{service}**.

### Recent Logs
```
{self._format_logs_as_text(logs[:15])}
```

### Log Level Distribution
| Level | Count |
|-------|-------|
| ERROR | {sum(1 for l in logs if l['level'] == 'ERROR')} |
| WARN  | {sum(1 for l in logs if l['level'] == 'WARN')} |
| INFO  | {sum(1 for l in logs if l['level'] == 'INFO')} |
| DEBUG | {sum(1 for l in logs if l['level'] == 'DEBUG')} |
""",
            structured_output={
                "type": "service_logs_result",
                "service": service,
                "total_count": len(logs),
                "logs": logs,
            },
            suggested_actions=[
                self._action(
                    "view-errors",
                    "invoke",
                    "View Errors",
                    {"agent_id": "nexusops.logs", "query": f"logs service={service} level=ERROR"},
                ),
                self._action(
                    "diagnose",
                    "invoke",
                    "Diagnose Service",
                    {"agent_id": "nexusops.k8s", "query": f"diagnose {service}"},
                ),
            ],
            metadata={"operation": "query_by_service", "service": service},
        )

    def _search_logs(self, context: Dict[str, Any]) -> ExecutorResult:
        """Search logs by keyword"""
        # Extract keyword from context or use default
        keyword = context.get("keyword", context.get("resource_name", "timeout"))
        service = context.get("service")

        logs = self._generate_mock_logs(count=10, keyword=keyword, service=service)

        return self._success(
            text=f"""## Search Results: "{keyword}"

Found **{len(logs)}** log entries matching "{keyword}".

### Matching Logs
```
{self._format_logs_as_text(logs)}
```

### Search Tips
- Use quotes for exact phrases: `"connection refused"`
- Combine with level filter: `search {keyword} level=ERROR`
- Add time range: `search {keyword} from=1h`
""",
            structured_output={
                "type": "search_result",
                "keyword": keyword,
                "total_count": len(logs),
                "logs": logs,
            },
            suggested_actions=[
                self._action(
                    "filter-errors",
                    "invoke",
                    "Filter to Errors",
                    {"agent_id": "nexusops.logs", "query": f"search {keyword} level=ERROR"},
                ),
                self._action(
                    "expand-search",
                    "invoke",
                    "Expand Time Range",
                    {"agent_id": "nexusops.logs", "query": f"search {keyword} from=24h"},
                ),
            ],
            metadata={"operation": "search_logs", "keyword": keyword},
        )

    def _query_recent(self, context: Dict[str, Any]) -> ExecutorResult:
        """Query recent logs (tail)"""
        service = context.get("resource_name")

        # Generate very recent logs
        now = datetime.now()
        logs = self._generate_mock_logs(
            count=20,
            service=service,
            start_time=now - timedelta(minutes=5),
            end_time=now,
        )

        return self._success(
            text=f"""## Recent Logs (Last 5 minutes)

Showing last **{len(logs)}** log entries.

### Live Tail
```
{self._format_logs_as_text(logs)}
```

Use `--tail` flag to follow logs in real-time.
""",
            structured_output={
                "type": "recent_logs_result",
                "total_count": len(logs),
                "logs": logs,
                "time_range": {
                    "start": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                    "end": now.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            suggested_actions=[
                self._action(
                    "follow-logs",
                    "invoke",
                    "Follow Logs",
                    {"agent_id": "nexusops.logs", "query": "logs --tail -f"},
                ),
                self._action(
                    "view-errors",
                    "invoke",
                    "View Errors Only",
                    {"agent_id": "nexusops.logs", "query": "recent level=ERROR"},
                ),
            ],
            metadata={"operation": "query_recent"},
        )

    def _query_time_range(self, context: Dict[str, Any]) -> ExecutorResult:
        """Query logs within time range"""
        # Parse time range from context
        from_time = context.get("from_time", "1 hour ago")
        to_time = context.get("to_time", "now")
        service = context.get("resource_name")

        # Generate logs for time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)

        logs = self._generate_mock_logs(
            count=30,
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        error_rate = sum(1 for l in logs if l['level'] == 'ERROR') / len(logs) * 100

        return self._success(
            text=f"""## Time Range Query

**From:** {start_time.strftime("%Y-%m-%d %H:%M:%S")}
**To:** {end_time.strftime("%Y-%m-%d %H:%M:%S")}

Found **{len(logs)}** log entries.

### Logs
```
{self._format_logs_as_text(logs[:20])}
```

### Statistics
- Total entries: {len(logs)}
- Error rate: {error_rate:.1f}%
- Average logs/min: {len(logs) / 60:.1f}
""",
            structured_output={
                "type": "time_range_result",
                "total_count": len(logs),
                "logs": logs,
                "time_range": {
                    "start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            suggested_actions=[
                self._action(
                    "expand-range",
                    "invoke",
                    "Expand Range",
                    {"agent_id": "nexusops.logs", "query": "logs from=24h"},
                ),
                self._action(
                    "export-logs",
                    "invoke",
                    "Export Logs",
                    {"agent_id": "nexusops.logs", "query": "export logs range"},
                ),
            ],
            metadata={"operation": "query_time_range"},
        )

    def _format_logs_as_text(self, logs: List[Dict[str, Any]]) -> str:
        """Format logs as plain text"""
        lines = []
        for log in logs:
            timestamp = log.get("timestamp", "")
            level = log.get("level", "INFO").ljust(5)
            service = log.get("service", "unknown").ljust(10)
            message = log.get("message", "")
            lines.append(f"{timestamp} {level} [{service}] {message}")
        return "\n".join(lines)

    def _format_service_summary(self, logs: List[Dict[str, Any]]) -> str:
        """Format service summary table"""
        service_counts: Dict[str, int] = {}
        for log in logs:
            service = log.get("service", "unknown")
            service_counts[service] = service_counts.get(service, 0) + 1

        lines = []
        for service, count in sorted(service_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {service} | {count} |")
        return "\n".join(lines)

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "query_logs",
                "description": "Query logs with optional filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "description": "Filter by service name"},
                        "level": {
                            "type": "string",
                            "enum": ["ERROR", "WARN", "INFO", "DEBUG"],
                            "description": "Filter by log level",
                        },
                        "keyword": {"type": "string", "description": "Search keyword"},
                        "from_time": {"type": "string", "description": "Start time (ISO format or relative)"},
                        "to_time": {"type": "string", "description": "End time (ISO format or relative)"},
                        "limit": {"type": "integer", "default": 100, "description": "Maximum number of logs to return"},
                    },
                },
            },
            {
                "name": "search_logs",
                "description": "Full-text search across all logs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "level": {
                            "type": "string",
                            "enum": ["ERROR", "WARN", "INFO", "DEBUG"],
                        },
                        "time_range": {"type": "string", "default": "1h"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_log_stats",
                "description": "Get log statistics and summaries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "time_range": {"type": "string", "default": "1h"},
                    },
                },
            },
        ]
