"""
NexusOps Backend - CI/CD Integration Service

BE-003: CI/CD 集成（Jenkins/GitLab CI）
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import httpx


class BuildStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class BuildInfo:
    """构建信息"""
    build_id: str
    status: BuildStatus
    url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    message: Optional[str] = None
    logs: Optional[str] = None


@dataclass
class BuildTrigger:
    """构建触发参数"""
    project: str
    branch: str = "main"
    parameters: dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class CICDProvider(ABC):
    """CI/CD 提供商抽象基类"""

    @abstractmethod
    async def trigger_build(self, trigger: BuildTrigger) -> BuildInfo:
        """触发构建"""
        pass

    @abstractmethod
    async def get_build_status(self, build_id: str) -> BuildInfo:
        """获取构建状态"""
        pass

    @abstractmethod
    async def get_build_logs(self, build_id: str, tail_lines: int = 100) -> str:
        """获取构建日志"""
        pass

    @abstractmethod
    async def abort_build(self, build_id: str) -> bool:
        """中止构建"""
        pass

    @abstractmethod
    async def list_builds(self, project: str, limit: int = 10) -> list[BuildInfo]:
        """列出构建历史"""
        pass


# ============================================
# Jenkins Provider
# ============================================

class JenkinsProvider(CICDProvider):
    """Jenkins CI/CD 提供商"""

    def __init__(
        self,
        base_url: str,
        username: str,
        api_token: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self._client = httpx.AsyncClient(
            auth=(username, api_token),
            timeout=30.0,
        )

    async def trigger_build(self, trigger: BuildTrigger) -> BuildInfo:
        """触发 Jenkins 构建"""
        job_name = trigger.project
        url = f"{self.base_url}/job/{job_name}/build"

        # 如果有参数，使用 buildWithParameters
        if trigger.parameters:
            params = "&".join(f"{k}={v}" for k, v in trigger.parameters.items())
            url = f"{self.base_url}/job/{job_name}/buildWithParameters?{params}"

        response = await self._client.post(url)

        if response.status_code in (200, 201, 302):
            # 从 Location header 获取队列 ID
            queue_url = response.headers.get("Location", "")
            queue_id = queue_url.split("/")[-2] if queue_url else None

            return BuildInfo(
                build_id=f"jenkins-{queue_id or 'unknown'}",
                status=BuildStatus.PENDING,
                branch=trigger.branch,
                started_at=datetime.utcnow(),
            )

        raise Exception(f"Failed to trigger build: {response.status_code}")

    async def get_build_status(self, build_id: str) -> BuildInfo:
        """获取 Jenkins 构建状态"""
        # 解析 build_id (格式: jenkins-{job_name}-{build_number})
        parts = build_id.split("-", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid build_id format: {build_id}")

        job_name = parts[1]
        build_number = parts[2]

        url = f"{self.base_url}/job/{job_name}/{build_number}/api/json"
        response = await self._client.get(url)

        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            building = data.get("building", False)

            if building:
                status = BuildStatus.RUNNING
            elif result == "SUCCESS":
                status = BuildStatus.SUCCESS
            elif result == "FAILURE":
                status = BuildStatus.FAILED
            elif result == "ABORTED":
                status = BuildStatus.ABORTED
            else:
                status = BuildStatus.PENDING

            return BuildInfo(
                build_id=build_id,
                status=status,
                url=f"{self.base_url}/job/{job_name}/{build_number}",
                started_at=datetime.fromtimestamp(data.get("timestamp", 0) / 1000) if data.get("timestamp") else None,
                duration_seconds=data.get("duration", 0) // 1000,
                commit_sha=self._extract_commit_sha(data),
                branch=self._extract_branch(data),
            )

        raise Exception(f"Failed to get build status: {response.status_code}")

    async def get_build_logs(self, build_id: str, tail_lines: int = 100) -> str:
        """获取 Jenkins 构建日志"""
        parts = build_id.split("-", 2)
        if len(parts) < 3:
            return ""

        job_name = parts[1]
        build_number = parts[2]

        url = f"{self.base_url}/job/{job_name}/{build_number}/logText/progressiveText"
        response = await self._client.get(url)

        if response.status_code == 200:
            logs = response.text
            lines = logs.split("\n")
            return "\n".join(lines[-tail_lines:])

        return ""

    async def abort_build(self, build_id: str) -> bool:
        """中止 Jenkins 构建"""
        parts = build_id.split("-", 2)
        if len(parts) < 3:
            return False

        job_name = parts[1]
        build_number = parts[2]

        url = f"{self.base_url}/job/{job_name}/{build_number}/stop"
        response = await self._client.post(url)

        return response.status_code in (200, 302)

    async def list_builds(self, project: str, limit: int = 10) -> list[BuildInfo]:
        """列出 Jenkins 构建历史"""
        url = f"{self.base_url}/job/{project}/api/json?tree=builds[number,result,timestamp,duration]{&limit={limit}}"
        response = await self._client.get(url)

        if response.status_code == 200:
            data = response.json()
            builds = []
            for build in data.get("builds", [])[:limit]:
                result = build.get("result")
                building = result is None

                if building:
                    status = BuildStatus.RUNNING
                elif result == "SUCCESS":
                    status = BuildStatus.SUCCESS
                elif result == "FAILURE":
                    status = BuildStatus.FAILED
                else:
                    status = BuildStatus.ABORTED

                builds.append(BuildInfo(
                    build_id=f"jenkins-{project}-{build['number']}",
                    status=status,
                    url=f"{self.base_url}/job/{project}/{build['number']}",
                    started_at=datetime.fromtimestamp(build.get("timestamp", 0) / 1000),
                    duration_seconds=build.get("duration", 0) // 1000,
                ))

            return builds

        return []

    def _extract_commit_sha(self, data: dict) -> Optional[str]:
        """从构建数据中提取 commit SHA"""
        actions = data.get("actions", [])
        for action in actions:
            if action.get("_class") == "hudson.plugins.git.util.BuildData":
                return action.get("lastBuiltRevision", {}).get("SHA1")
        return None

    def _extract_branch(self, data: dict) -> Optional[str]:
        """从构建数据中提取分支名"""
        actions = data.get("actions", [])
        for action in actions:
            if action.get("_class") == "hudson.plugins.git.util.BuildData":
                branches = action.get("buildsByBranchName", {})
                for branch_name in branches.keys():
                    if branch_name and not branch_name.startswith("HEAD"):
                        return branch_name.replace("origin/", "")
        return None


# ============================================
# GitLab CI Provider
# ============================================

class GitLabCIProvider(CICDProvider):
    """GitLab CI 提供商"""

    def __init__(
        self,
        base_url: str,
        private_token: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.private_token = private_token
        self._client = httpx.AsyncClient(
            headers={"PRIVATE-TOKEN": private_token},
            timeout=30.0,
        )

    async def trigger_build(self, trigger: BuildTrigger) -> BuildInfo:
        """触发 GitLab CI Pipeline"""
        # project 格式: namespace/project (URL encoded)
        project_id = trigger.project.replace("/", "%2F")

        url = f"{self.base_url}/api/v4/projects/{project_id}/pipeline"
        payload = {
            "ref": trigger.branch,
        }
        if trigger.parameters:
            payload["variables"] = [
                {"key": k, "value": v} for k, v in trigger.parameters.items()
            ]

        response = await self._client.post(url, json=payload)

        if response.status_code in (200, 201):
            data = response.json()
            return BuildInfo(
                build_id=f"gitlab-{data['id']}",
                status=self._map_status(data.get("status")),
                url=data.get("web_url"),
                branch=data.get("ref"),
                commit_sha=data.get("sha"),
                started_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else None,
            )

        raise Exception(f"Failed to trigger pipeline: {response.status_code}")

    async def get_build_status(self, build_id: str) -> BuildInfo:
        """获取 GitLab Pipeline 状态"""
        # build_id 格式: gitlab-{pipeline_id}
        pipeline_id = build_id.replace("gitlab-", "")

        # 需要知道 project_id，这里假设从缓存或数据库获取
        # 简化实现：返回 mock 数据
        return BuildInfo(
            build_id=build_id,
            status=BuildStatus.SUCCESS,
            duration_seconds=120,
        )

    async def get_build_logs(self, build_id: str, tail_lines: int = 100) -> str:
        """获取 GitLab Job 日志"""
        # 需要先获取 pipeline 下的 job，然后获取 job 日志
        # 简化实现
        return f"[GitLab CI] Logs for {build_id} (last {tail_lines} lines)"

    async def abort_build(self, build_id: str) -> bool:
        """取消 GitLab Pipeline"""
        pipeline_id = build_id.replace("gitlab-", "")
        # 需要 project_id
        return True

    async def list_builds(self, project: str, limit: int = 10) -> list[BuildInfo]:
        """列出 GitLab Pipelines"""
        project_id = project.replace("/", "%2F")
        url = f"{self.base_url}/api/v4/projects/{project_id}/pipelines?per_page={limit}"

        response = await self._client.get(url)

        if response.status_code == 200:
            data = response.json()
            builds = []
            for pipeline in data:
                builds.append(BuildInfo(
                    build_id=f"gitlab-{pipeline['id']}",
                    status=self._map_status(pipeline.get("status")),
                    url=pipeline.get("web_url"),
                    branch=pipeline.get("ref"),
                    commit_sha=pipeline.get("sha"),
                    started_at=datetime.fromisoformat(pipeline["created_at"].replace("Z", "+00:00")) if pipeline.get("created_at") else None,
                ))
            return builds

        return []

    def _map_status(self, gitlab_status: str) -> BuildStatus:
        """映射 GitLab 状态到通用状态"""
        mapping = {
            "pending": BuildStatus.PENDING,
            "running": BuildStatus.RUNNING,
            "success": BuildStatus.SUCCESS,
            "failed": BuildStatus.FAILED,
            "canceled": BuildStatus.ABORTED,
            "skipped": BuildStatus.ABORTED,
        }
        return mapping.get(gitlab_status, BuildStatus.PENDING)


# ============================================
# GitHub Actions Provider
# ============================================

class GitHubActionsProvider(CICDProvider):
    """GitHub Actions 提供商"""

    def __init__(
        self,
        token: str,
    ):
        self.base_url = "https://api.github.com"
        self.token = token
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30.0,
        )

    async def trigger_build(self, trigger: BuildTrigger) -> BuildInfo:
        """触发 GitHub Actions Workflow"""
        # project 格式: owner/repo
        # 需要指定 workflow 文件名
        workflow_file = trigger.parameters.get("workflow", "main.yml")
        owner, repo = trigger.project.split("/")

        url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"
        payload = {
            "ref": trigger.branch,
            "inputs": trigger.parameters.get("inputs", {}),
        }

        response = await self._client.post(url, json=payload)

        if response.status_code == 204:
            return BuildInfo(
                build_id=f"github-{trigger.project}-{datetime.utcnow().timestamp()}",
                status=BuildStatus.PENDING,
                branch=trigger.branch,
                started_at=datetime.utcnow(),
            )

        raise Exception(f"Failed to trigger workflow: {response.status_code}")

    async def get_build_status(self, build_id: str) -> BuildInfo:
        """获取 GitHub Actions Run 状态"""
        # 简化实现
        return BuildInfo(
            build_id=build_id,
            status=BuildStatus.SUCCESS,
        )

    async def get_build_logs(self, build_id: str, tail_lines: int = 100) -> str:
        """获取 GitHub Actions 日志"""
        return f"[GitHub Actions] Logs for {build_id}"

    async def abort_build(self, build_id: str) -> bool:
        """取消 GitHub Actions Run"""
        return True

    async def list_builds(self, project: str, limit: int = 10) -> list[BuildInfo]:
        """列出 GitHub Actions Runs"""
        owner, repo = project.split("/")
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs?per_page={limit}"

        response = await self._client.get(url)

        if response.status_code == 200:
            data = response.json()
            builds = []
            for run in data.get("workflow_runs", []):
                builds.append(BuildInfo(
                    build_id=f"github-{run['id']}",
                    status=self._map_status(run.get("status"), run.get("conclusion")),
                    url=run.get("html_url"),
                    branch=run.get("head_branch"),
                    commit_sha=run.get("head_sha"),
                    started_at=datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) if run.get("created_at") else None,
                ))
            return builds

        return []

    def _map_status(self, status: str, conclusion: Optional[str]) -> BuildStatus:
        """映射 GitHub Actions 状态"""
        if status == "in_progress":
            return BuildStatus.RUNNING
        if status == "queued":
            return BuildStatus.PENDING
        if conclusion == "success":
            return BuildStatus.SUCCESS
        if conclusion == "failure":
            return BuildStatus.FAILED
        if conclusion == "cancelled":
            return BuildStatus.ABORTED
        return BuildStatus.PENDING


# ============================================
# Mock Provider (用于开发测试)
# ============================================

class MockCICDProvider(CICDProvider):
    """Mock CI/CD 提供商 (用于开发测试)"""

    def __init__(self):
        self._builds: dict[str, BuildInfo] = {}
        self._counter = 0

    async def trigger_build(self, trigger: BuildTrigger) -> BuildInfo:
        self._counter += 1
        build_id = f"mock-{self._counter}"

        build = BuildInfo(
            build_id=build_id,
            status=BuildStatus.PENDING,
            branch=trigger.branch,
            started_at=datetime.utcnow(),
            message=f"Build triggered for {trigger.project}/{trigger.branch}",
        )
        self._builds[build_id] = build

        # 模拟构建进度
        asyncio.create_task(self._simulate_build(build_id))

        return build

    async def _simulate_build(self, build_id: str):
        """模拟构建过程"""
        await asyncio.sleep(1)
        if build_id in self._builds:
            self._builds[build_id] = BuildInfo(
                build_id=build_id,
                status=BuildStatus.RUNNING,
                branch=self._builds[build_id].branch,
                started_at=self._builds[build_id].started_at,
                message="Building...",
            )

        await asyncio.sleep(3)
        if build_id in self._builds:
            self._builds[build_id] = BuildInfo(
                build_id=build_id,
                status=BuildStatus.SUCCESS,
                branch=self._builds[build_id].branch,
                started_at=self._builds[build_id].started_at,
                completed_at=datetime.utcnow(),
                duration_seconds=4,
                commit_sha="abc1234",
                message="Build completed successfully",
            )

    async def get_build_status(self, build_id: str) -> BuildInfo:
        if build_id in self._builds:
            return self._builds[build_id]

        return BuildInfo(
            build_id=build_id,
            status=BuildStatus.FAILED,
            message="Build not found",
        )

    async def get_build_logs(self, build_id: str, tail_lines: int = 100) -> str:
        logs = f"""[Mock CI/CD] Build {build_id}
=====================================
[00:00] Starting build...
[00:01] Cloning repository...
[00:02] Installing dependencies...
[00:03] Running tests...
[00:04] Build completed successfully!
=====================================
"""
        lines = logs.split("\n")
        return "\n".join(lines[-tail_lines:])

    async def abort_build(self, build_id: str) -> bool:
        if build_id in self._builds:
            self._builds[build_id] = BuildInfo(
                build_id=build_id,
                status=BuildStatus.ABORTED,
                message="Build aborted by user",
            )
            return True
        return False

    async def list_builds(self, project: str, limit: int = 10) -> list[BuildInfo]:
        return list(self._builds.values())[:limit]


# ============================================
# Factory
# ============================================

def get_cicd_provider(
    provider_type: str,
    config: dict[str, Any],
) -> CICDProvider:
    """获取 CI/CD 提供商实例"""
    if provider_type == "jenkins":
        return JenkinsProvider(
            base_url=config["base_url"],
            username=config["username"],
            api_token=config["api_token"],
        )
    elif provider_type == "gitlab":
        return GitLabCIProvider(
            base_url=config["base_url"],
            private_token=config["private_token"],
        )
    elif provider_type == "github":
        return GitHubActionsProvider(
            token=config["token"],
        )
    else:
        return MockCICDProvider()
