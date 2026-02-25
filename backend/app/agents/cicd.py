"""
NexusOps Agents - CI/CD Agent Handler

nexusops.cicd: CI/CD pipeline operations (Jenkins, ArgoCD)
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
import string

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class CICDAgentHandler(BaseAgentHandler):
    """CI/CD agent handler for pipeline operations"""

    # Mock pipeline names
    MOCK_PIPELINES = [
        "frontend-build",
        "backend-api-build",
        "backend-worker-build",
        "integration-tests",
        "deploy-staging",
        "deploy-production",
        "security-scan",
        "performance-tests",
    ]

    # Pipeline status types
    STATUS_TYPES = ["pending", "running", "success", "failed", "cancelled"]

    @property
    def agent_id(self) -> str:
        return "nexusops.cicd"

    @property
    def capabilities(self) -> List[str]:
        return [
            "pipeline_trigger",
            "pipeline_status",
            "pipeline_cancel",
            "build_logs",
            "pipeline_list",
            "jenkins_trigger",
            "argocd_sync",
        ]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle CI/CD requests"""
        await asyncio.sleep(0.2)

        query = request.query.lower()
        context = request.request_context

        # Route to appropriate handler based on query keywords
        if "jenkins" in query or "build" in query:
            if "trigger" in query or "start" in query:
                return self._handle_trigger_jenkins(context)
            elif "log" in query:
                return self._handle_get_build_logs(context)
            else:
                return self._handle_pipeline_status(context)
        elif "argocd" in query or "sync" in query:
            return self._handle_argocd_sync(context)
        elif "cancel" in query or "abort" in query or "stop" in query:
            return self._handle_cancel_pipeline(context)
        elif "list" in query or "show" in query or "all" in query:
            return self._handle_list_pipelines(context)
        elif "status" in query or "check" in query:
            return self._handle_pipeline_status(context)
        elif "log" in query:
            return self._handle_get_build_logs(context)
        elif "trigger" in query or "run" in query or "start" in query:
            return self._handle_trigger_pipeline(context)
        else:
            return self._handle_general_query(context)

    def _generate_build_id(self) -> str:
        """Generate a mock build ID"""
        chars = string.ascii_lowercase + string.digits
        return f"build-{''.join(random.choices(chars, k=8))}"

    def _generate_pipeline_id(self) -> str:
        """Generate a mock pipeline ID"""
        return f"pipeline-{random.randint(100, 999)}"

    def _handle_general_query(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle general CI/CD query"""
        # Show overview of pipelines
        pipelines = self._get_mock_pipeline_statuses()

        return self._success(
            text=f"""## CI/CD Overview

### Pipeline Status Summary
| Pipeline | Last Build | Status |
|----------|------------|--------|
{self._format_pipeline_table(pipelines[:5])}

### Quick Actions
- Trigger a build: `trigger pipeline <name>`
- Check status: `status <pipeline_id>`
- View logs: `logs <build_id>`
- Sync ArgoCD: `argocd sync <app>`
""",
            structured_output={
                "type": "cicd_overview",
                "pipelines": pipelines,
            },
            suggested_actions=[
                self._action(
                    "trigger-build",
                    "invoke",
                    "Trigger Build",
                    {"agent_id": "nexusops.cicd", "query": "trigger pipeline frontend-build"},
                ),
                self._action(
                    "argocd-sync",
                    "invoke",
                    "Sync ArgoCD",
                    {"agent_id": "nexusops.cicd", "query": "argocd sync production"},
                ),
                self._action(
                    "view-logs",
                    "invoke",
                    "View Recent Logs",
                    {"agent_id": "nexusops.cicd", "query": "logs recent"},
                ),
            ],
            metadata={"operation": "cicd_overview"},
        )

    def _handle_trigger_pipeline(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle pipeline trigger request"""
        pipeline_name = context.get("resource_name", "frontend-build")
        branch = context.get("branch", "main")
        build_id = self._generate_build_id()

        return self._success(
            text=f"""## Pipeline Triggered

**Pipeline:** {pipeline_name}
**Branch:** {branch}
**Build ID:** `{build_id}`
**Status:** Pending

The pipeline has been queued and will start shortly.

### Build Steps
1. Checkout code
2. Install dependencies
3. Run tests
4. Build artifacts
5. Deploy (if applicable)
""",
            structured_output={
                "type": "pipeline_triggered",
                "pipeline_id": self._generate_pipeline_id(),
                "build_id": build_id,
                "pipeline_name": pipeline_name,
                "branch": branch,
                "status": "pending",
                "triggered_at": datetime.now().isoformat(),
            },
            suggested_actions=[
                self._action(
                    "view-status",
                    "invoke",
                    "View Build Status",
                    {"agent_id": "nexusops.cicd", "query": f"status {build_id}"},
                ),
                self._action(
                    "view-logs",
                    "invoke",
                    "View Build Logs",
                    {"agent_id": "nexusops.cicd", "query": f"logs {build_id}"},
                ),
                self._action(
                    "cancel-build",
                    "invoke",
                    "Cancel Build",
                    {"agent_id": "nexusops.cicd", "query": f"cancel {build_id}"},
                    confirm_required=True,
                    danger=True,
                ),
            ],
            metadata={"operation": "trigger_pipeline"},
        )

    def _handle_trigger_jenkins(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle Jenkins build trigger"""
        job_name = context.get("resource_name", "frontend-build")
        branch = context.get("branch", "main")
        build_id = self._generate_build_id()

        return self._success(
            text=f"""## Jenkins Build Triggered

**Job:** {job_name}
**Branch:** {branch}
**Build Number:** #{random.randint(100, 999)}
**Build ID:** `{build_id}`
**Status:** Queued

The Jenkins job has been triggered and is now in the build queue.

### Job Configuration
- **Jenkins Server:** jenkins.internal.company.com
- **Executor:** Any available
- **Estimated Duration:** ~5 minutes
""",
            structured_output={
                "type": "jenkins_build_triggered",
                "pipeline_id": self._generate_pipeline_id(),
                "build_id": build_id,
                "job_name": job_name,
                "branch": branch,
                "status": "pending",
                "jenkins_url": f"https://jenkins.internal.company.com/job/{job_name}",
                "triggered_at": datetime.now().isoformat(),
            },
            suggested_actions=[
                self._action(
                    "view-status",
                    "invoke",
                    "View Build Status",
                    {"agent_id": "nexusops.cicd", "query": f"status {build_id}"},
                ),
                self._action(
                    "view-logs",
                    "invoke",
                    "View Console Output",
                    {"agent_id": "nexusops.cicd", "query": f"logs {build_id}"},
                ),
            ],
            metadata={"operation": "trigger_jenkins"},
        )

    def _handle_argocd_sync(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle ArgoCD sync request"""
        app_name = context.get("resource_name", "production-app")
        revision = context.get("revision", "HEAD")
        sync_id = f"sync-{random.randint(10000, 99999)}"

        return self._success(
            text=f"""## ArgoCD Sync Triggered

**Application:** {app_name}
**Revision:** {revision}
**Sync ID:** `{sync_id}`
**Status:** Syncing

ArgoCD sync has been initiated for the application.

### Sync Details
- **Strategy:** Rolling Update
- **Prune Resources:** No
- **Dry Run:** No
- **Target Revision:** {revision}

### Sync Progress
```
[=====>    ] 50% Syncing resources...
```
""",
            structured_output={
                "type": "argocd_sync_triggered",
                "sync_id": sync_id,
                "app_name": app_name,
                "revision": revision,
                "status": "syncing",
                "sync_strategy": "rolling_update",
                "argocd_url": f"https://argocd.internal.company.com/applications/{app_name}",
                "triggered_at": datetime.now().isoformat(),
            },
            suggested_actions=[
                self._action(
                    "view-status",
                    "invoke",
                    "View Sync Status",
                    {"agent_id": "nexusops.cicd", "query": f"status {sync_id}"},
                ),
                self._action(
                    "view-app",
                    "navigate",
                    "View in ArgoCD",
                    {"url": f"https://argocd.internal.company.com/applications/{app_name}"},
                ),
            ],
            metadata={"operation": "argocd_sync"},
        )

    def _handle_pipeline_status(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle pipeline status query"""
        pipeline_id = context.get("resource_name", self._generate_pipeline_id())
        status = random.choice(["success", "running", "success", "success", "failed"])

        duration_seconds = random.randint(120, 600)
        duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"

        stages = [
            {"name": "Checkout", "status": "success", "duration": "5s"},
            {"name": "Install Dependencies", "status": "success", "duration": "45s"},
            {"name": "Run Tests", "status": "success" if status != "failed" else "failed", "duration": "2m 30s"},
            {"name": "Build", "status": "success" if status == "success" else ("running" if status == "running" else "skipped"), "duration": "3m 15s"},
            {"name": "Deploy", "status": status if status in ["success", "running"] else "skipped", "duration": "1m 20s"},
        ]

        return self._success(
            text=f"""## Pipeline Status

**Pipeline ID:** `{pipeline_id}`
**Status:** {status.upper()}
**Duration:** {duration_str}

### Build Stages
| Stage | Status | Duration |
|-------|--------|----------|
{self._format_stages_table(stages)}

### Build Information
- **Triggered By:** user@example.com
- **Branch:** main
- **Commit:** abc123def456
- **Message:** "Fix bug in authentication flow"
""",
            structured_output={
                "type": "pipeline_status",
                "pipeline_id": pipeline_id,
                "status": status,
                "duration_seconds": duration_seconds,
                "stages": stages,
                "triggered_by": "user@example.com",
                "branch": "main",
                "commit": "abc123def456",
            },
            suggested_actions=[
                self._action(
                    "view-logs",
                    "invoke",
                    "View Build Logs",
                    {"agent_id": "nexusops.cicd", "query": f"logs {pipeline_id}"},
                ),
                self._action(
                    "rerun-build",
                    "invoke",
                    "Re-run Build",
                    {"agent_id": "nexusops.cicd", "query": f"trigger pipeline {pipeline_id}"},
                ),
            ] + ([
                self._action(
                    "cancel-build",
                    "invoke",
                    "Cancel Build",
                    {"agent_id": "nexusops.cicd", "query": f"cancel {pipeline_id}"},
                    confirm_required=True,
                    danger=True,
                ),
            ] if status == "running" else []),
            metadata={"operation": "pipeline_status"},
        )

    def _handle_cancel_pipeline(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle pipeline cancellation"""
        pipeline_id = context.get("resource_name", self._generate_pipeline_id())

        return self._success(
            text=f"""## Pipeline Cancelled

**Pipeline ID:** `{pipeline_id}`
**Status:** Cancelled
**Cancelled At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

The pipeline has been successfully cancelled.

### Cancellation Details
- **Reason:** User requested
- **Running Step:** Build (interrupted)
- **Cleanup:** Completed
""",
            structured_output={
                "type": "pipeline_cancelled",
                "pipeline_id": pipeline_id,
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "reason": "User requested",
            },
            suggested_actions=[
                self._action(
                    "rerun-build",
                    "invoke",
                    "Re-run Pipeline",
                    {"agent_id": "nexusops.cicd", "query": f"trigger pipeline {pipeline_id}"},
                ),
            ],
            metadata={"operation": "cancel_pipeline"},
        )

    def _handle_get_build_logs(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle build logs request"""
        build_id = context.get("resource_name", self._generate_build_id())

        mock_logs = [
            f"[{datetime.now().strftime('%H:%M:%S')}] Starting build {build_id}",
            f"[{datetime.now().strftime('%H:%M:%S')}] Checking out code...",
            f"[{datetime.now().strftime('%H:%M:%S')}] Fetching origin/main",
            f"[{datetime.now().strftime('%H:%M:%S')}] HEAD is now at abc123d Fix bug",
            f"[{datetime.now().strftime('%H:%M:%S')}] Installing dependencies...",
            f"[{datetime.now().strftime('%H:%M:%S')}] npm install completed in 45s",
            f"[{datetime.now().strftime('%H:%M:%S')}] Running tests...",
            f"[{datetime.now().strftime('%H:%M:%S')}] Test suite: 125 passed, 0 failed",
            f"[{datetime.now().strftime('%H:%M:%S')}] Building application...",
            f"[{datetime.now().strftime('%H:%M:%S')}] Build completed successfully",
            f"[{datetime.now().strftime('%H:%M:%S')}] Uploading artifacts...",
            f"[{datetime.now().strftime('%H:%M:%S')}] Build finished in 5m 30s",
        ]

        return self._success(
            text=f"""## Build Logs

**Build ID:** `{build_id}`
**Status:** Success
**Duration:** 5m 30s

### Console Output
```
{chr(10).join(mock_logs)}
```

### Log Statistics
- Total lines: {len(mock_logs)}
- Errors: 0
- Warnings: 0
""",
            structured_output={
                "type": "build_logs",
                "build_id": build_id,
                "status": "success",
                "logs": mock_logs,
                "log_count": len(mock_logs),
            },
            suggested_actions=[
                self._action(
                    "download-logs",
                    "invoke",
                    "Download Full Logs",
                    {"agent_id": "nexusops.cicd", "query": f"download logs {build_id}"},
                ),
                self._action(
                    "view-status",
                    "invoke",
                    "View Build Status",
                    {"agent_id": "nexusops.cicd", "query": f"status {build_id}"},
                ),
            ],
            metadata={"operation": "get_build_logs"},
        )

    def _handle_list_pipelines(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle list pipelines request"""
        pipelines = self._get_mock_pipeline_statuses()

        return self._success(
            text=f"""## Available Pipelines

Found **{len(pipelines)}** pipelines.

| Pipeline | Status | Last Run | Duration |
|----------|--------|----------|----------|
{self._format_pipeline_table(pipelines)}

### Pipeline Categories
- **Build:** frontend-build, backend-api-build, backend-worker-build
- **Test:** integration-tests, security-scan, performance-tests
- **Deploy:** deploy-staging, deploy-production
""",
            structured_output={
                "type": "pipeline_list",
                "pipelines": pipelines,
                "total_count": len(pipelines),
            },
            suggested_actions=[
                self._action(
                    "trigger-build",
                    "invoke",
                    "Trigger Build",
                    {"agent_id": "nexusops.cicd", "query": "trigger pipeline"},
                ),
                self._action(
                    "view-status",
                    "invoke",
                    "Check All Status",
                    {"agent_id": "nexusops.cicd", "query": "status all"},
                ),
            ],
            metadata={"operation": "list_pipelines"},
        )

    def _get_mock_pipeline_statuses(self) -> List[Dict[str, Any]]:
        """Get mock pipeline statuses"""
        statuses = []
        for i, name in enumerate(self.MOCK_PIPELINES):
            status = random.choice(self.STATUS_TYPES[:-1])  # Exclude 'cancelled'
            last_run = datetime.now() - timedelta(hours=random.randint(1, 48))
            duration = random.randint(120, 600)

            statuses.append({
                "name": name,
                "status": status,
                "last_run": last_run.strftime("%Y-%m-%d %H:%M"),
                "duration_seconds": duration,
                "duration": f"{duration // 60}m {duration % 60}s",
                "build_number": random.randint(100, 999),
            })
        return statuses

    def _format_pipeline_table(self, pipelines: List[Dict[str, Any]]) -> str:
        """Format pipelines as markdown table"""
        rows = []
        for p in pipelines:
            status_emoji = {"success": "OK", "running": "...", "failed": "ERR", "pending": "WAIT"}.get(p["status"], p["status"])
            rows.append(f"| {p['name']} | {status_emoji} | {p['last_run']} | {p['duration']} |")
        return "\n".join(rows)

    def _format_stages_table(self, stages: List[Dict[str, Any]]) -> str:
        """Format stages as markdown table"""
        rows = []
        for s in stages:
            rows.append(f"| {s['name']} | {s['status'].upper()} | {s['duration']} |")
        return "\n".join(rows)

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for this agent"""
        return [
            {
                "name": "trigger_jenkins_build",
                "description": "Trigger a Jenkins build job",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_name": {"type": "string", "description": "Jenkins job name"},
                        "branch": {"type": "string", "default": "main", "description": "Git branch to build"},
                        "parameters": {"type": "object", "description": "Build parameters"},
                    },
                    "required": ["job_name"],
                },
            },
            {
                "name": "trigger_argocd_sync",
                "description": "Trigger ArgoCD application sync",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "ArgoCD application name"},
                        "revision": {"type": "string", "default": "HEAD", "description": "Git revision to sync"},
                        "prune": {"type": "boolean", "default": False, "description": "Prune resources"},
                    },
                    "required": ["app_name"],
                },
            },
            {
                "name": "get_pipeline_status",
                "description": "Get pipeline or build status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pipeline_id": {"type": "string", "description": "Pipeline or build ID"},
                    },
                    "required": ["pipeline_id"],
                },
            },
            {
                "name": "cancel_pipeline",
                "description": "Cancel a running pipeline",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pipeline_id": {"type": "string", "description": "Pipeline ID to cancel"},
                    },
                    "required": ["pipeline_id"],
                },
            },
            {
                "name": "get_build_logs",
                "description": "Get build console logs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "build_id": {"type": "string", "description": "Build ID"},
                        "tail_lines": {"type": "integer", "default": 100, "description": "Number of lines to return"},
                    },
                    "required": ["build_id"],
                },
            },
            {
                "name": "list_pipelines",
                "description": "List all available pipelines",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filter": {"type": "string", "description": "Filter pipelines by name or status"},
                    },
                },
            },
        ]
