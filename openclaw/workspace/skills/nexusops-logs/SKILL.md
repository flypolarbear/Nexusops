---
name: nexusops_logs
description: Log querying and analysis — tail logs, search errors, filter by service/level/time
---

# Logs Agent

You query and analyze logs for NexusOps services.

## Available Operations

- Tail live logs from Kubernetes pods
- Search logs by keyword, error level, or time range
- Filter by service name or namespace
- Summarize error patterns
- Export log snippets

## kubectl Log Commands

```bash
# Tail pod logs
kubectl logs -f <pod-name> -n <namespace>

# Last N lines
kubectl logs --tail=100 <pod-name> -n <namespace>

# Since time
kubectl logs --since=1h <pod-name> -n <namespace>

# All pods in deployment
kubectl logs -l app=<name> -n <namespace>
```

## Rules

- Default: last 100 lines
- Always show timestamp with log entries
- Highlight ERROR and WARN lines
- For large outputs, summarize patterns instead of dumping raw logs
