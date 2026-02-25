"""
NexusOps Agents - Git Agent Handler

nexusops.git: Git repository operations, branch management, PR/MR handling
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
import string

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class GitAgentHandler(BaseAgentHandler):
    """Git agent handler for repository operations"""

    # Mock branch names
    MOCK_BRANCHES = [
        "main",
        "develop",
        "feature/user-auth",
        "feature/api-v2",
        "bugfix/login-crash",
        "hotfix/security-patch",
        "release/v1.2.0",
        "release/v1.3.0",
    ]

    # Mock commit authors
    MOCK_AUTHORS = [
        "alice@example.com",
        "bob@example.com",
        "charlie@example.com",
        "diana@example.com",
        "eve@example.com",
    ]

    @property
    def agent_id(self) -> str:
        return "nexusops.git"

    @property
    def capabilities(self) -> List[str]:
        return [
            "git_status",
            "git_branch",
            "git_tag",
            "git_pr",
            "git_diff",
            "git_commit",
            "create_branch",
            "delete_branch",
            "create_pull_request",
        ]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle Git requests"""
        await asyncio.sleep(0.2)

        query = request.query.lower()
        context = request.request_context

        # Route to appropriate handler based on query keywords
        if "status" in query or "info" in query:
            return self._handle_repo_status(context)
        elif "branch" in query:
            if "create" in query or "new" in query:
                return self._handle_create_branch(context)
            elif "delete" in query or "remove" in query:
                return self._handle_delete_branch(context)
            elif "list" in query or "show" in query or "all" in query:
                return self._handle_list_branches(context)
            else:
                return self._handle_list_branches(context)
        elif "tag" in query:
            if "create" in query or "new" in query:
                return self._handle_create_tag(context)
            elif "delete" in query or "remove" in query:
                return self._handle_delete_tag(context)
            else:
                return self._handle_list_tags(context)
        elif "pr" in query or "pull request" in query or "merge request" in query or "mr" in query:
            if "create" in query or "new" in query or "open" in query:
                return self._handle_create_pr(context)
            elif "list" in query or "show" in query:
                return self._handle_list_prs(context)
            else:
                return self._handle_list_prs(context)
        elif "diff" in query or "compare" in query:
            return self._handle_diff(context)
        elif "commit" in query or "history" in query or "log" in query:
            return self._handle_commit_history(context)
        else:
            return self._handle_repo_status(context)

    def _generate_commit_sha(self) -> str:
        """Generate a mock commit SHA"""
        chars = string.hexdigits.lower()[:16]
        return ''.join(random.choices(chars, k=8))

    def _handle_repo_status(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle repository status query"""
        repo = context.get("resource_name", "nexusops/backend")

        return self._success(
            text=f"""## Repository Status

**Repository:** {repo}
**Default Branch:** main
**Current Branch:** develop

### Summary
- **Branches:** 8
- **Tags:** 12
- **Open PRs:** 5
- **Last Commit:** abc123def - "Add new feature" (2 hours ago)

### Working Directory Status
```
On branch develop
Your branch is up to date with 'origin/develop'.

nothing to commit, working tree clean
```

### Remote
- **Origin:** git@github.com:company/nexusops.git
- **Upstream:** git@github.com:upstream/nexusops.git
""",
            structured_output={
                "type": "git_status",
                "repo": repo,
                "current_branch": "develop",
                "default_branch": "main",
                "branch_count": 8,
                "tag_count": 12,
                "open_pr_count": 5,
                "last_commit": {
                    "sha": "abc123def",
                    "message": "Add new feature",
                    "author": "alice@example.com",
                    "date": (datetime.now() - timedelta(hours=2)).isoformat(),
                },
                "working_tree_clean": True,
            },
            suggested_actions=[
                self._action(
                    "view-branches",
                    "invoke",
                    "View Branches",
                    {"agent_id": "nexusops.git", "query": "list branches"},
                ),
                self._action(
                    "create-branch",
                    "invoke",
                    "Create Branch",
                    {"agent_id": "nexusops.git", "query": "create branch feature/new-feature"},
                ),
                self._action(
                    "view-prs",
                    "invoke",
                    "View Pull Requests",
                    {"agent_id": "nexusops.git", "query": "list pull requests"},
                ),
            ],
            metadata={"operation": "repo_status"},
        )

    def _handle_list_branches(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle list branches request"""
        repo = context.get("resource_name", "nexusops/backend")

        branches = []
        for branch_name in self.MOCK_BRANCHES:
            branches.append({
                "name": branch_name,
                "sha": self._generate_commit_sha(),
                "last_commit": {
                    "message": f"Update {branch_name.split('/')[-1] if '/' in branch_name else branch_name}",
                    "author": random.choice(self.MOCK_AUTHORS),
                    "date": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                },
                "protected": branch_name in ["main", "develop"],
                "ahead": random.randint(0, 5),
                "behind": random.randint(0, 3),
            })

        return self._success(
            text=f"""## Branches

**Repository:** {repo}
**Total Branches:** {len(branches)}

| Branch | Last Commit | Protected | Ahead/Behind |
|--------|-------------|-----------|--------------|
{self._format_branch_table(branches)}

### Branch Types
- **main:** Production-ready code
- **develop:** Integration branch
- **feature/*:** New features
- **bugfix/*:** Bug fixes
- **hotfix/*:** Critical production fixes
- **release/*:** Release preparation
""",
            structured_output={
                "type": "branch_list",
                "repo": repo,
                "branches": branches,
                "total_count": len(branches),
            },
            suggested_actions=[
                self._action(
                    "create-branch",
                    "invoke",
                    "Create New Branch",
                    {"agent_id": "nexusops.git", "query": "create branch feature/my-feature"},
                ),
                self._action(
                    "compare-branches",
                    "invoke",
                    "Compare Branches",
                    {"agent_id": "nexusops.git", "query": "diff main..develop"},
                ),
            ],
            metadata={"operation": "list_branches"},
        )

    def _handle_create_branch(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle create branch request"""
        branch_name = context.get("resource_name", "feature/new-feature")
        base_branch = context.get("base_branch", "develop")
        repo = context.get("repo", "nexusops/backend")

        return self._success(
            text=f"""## Branch Created

**Repository:** {repo}
**New Branch:** `{branch_name}`
**Base Branch:** `{base_branch}`
**Created At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Branch Information
- **Head Commit:** {self._generate_commit_sha()}
- **Author:** current-user@example.com
- **Status:** Ready for development

### Next Steps
1. Checkout the branch: `git checkout {branch_name}`
2. Make your changes
3. Push to remote: `git push -u origin {branch_name}`
4. Create a Pull Request when ready
""",
            structured_output={
                "type": "branch_created",
                "repo": repo,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "sha": self._generate_commit_sha(),
                "created_at": datetime.now().isoformat(),
                "author": "current-user@example.com",
            },
            suggested_actions=[
                self._action(
                    "create-pr",
                    "invoke",
                    "Create Pull Request",
                    {"agent_id": "nexusops.git", "query": f"create pr {branch_name} -> {base_branch}"},
                ),
                self._action(
                    "view-branch",
                    "invoke",
                    "View Branch Status",
                    {"agent_id": "nexusops.git", "query": f"status {branch_name}"},
                ),
            ],
            metadata={"operation": "create_branch"},
        )

    def _handle_delete_branch(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle delete branch request"""
        branch_name = context.get("resource_name", "feature/old-feature")
        repo = context.get("repo", "nexusops/backend")

        return self._success(
            text=f"""## Branch Deleted

**Repository:** {repo}
**Deleted Branch:** `{branch_name}`
**Deleted At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Deletion Details
- **Reason:** User requested
- **Last Commit:** {self._generate_commit_sha()}
- **Merged:** Yes

### Note
The branch has been deleted from both local and remote repositories.
If this was a mistake, you can restore it using:
```
git checkout -b {branch_name} origin/{branch_name}
```
""",
            structured_output={
                "type": "branch_deleted",
                "repo": repo,
                "branch_name": branch_name,
                "deleted_at": datetime.now().isoformat(),
                "can_restore": True,
            },
            suggested_actions=[
                self._action(
                    "list-branches",
                    "invoke",
                    "View Remaining Branches",
                    {"agent_id": "nexusops.git", "query": "list branches"},
                ),
            ],
            metadata={"operation": "delete_branch"},
        )

    def _handle_list_tags(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle list tags request"""
        repo = context.get("resource_name", "nexusops/backend")

        tags = []
        for i in range(12):
            version = f"v1.{i // 4}.{i % 4}"
            tags.append({
                "name": version,
                "sha": self._generate_commit_sha(),
                "message": f"Release {version}",
                "author": random.choice(self.MOCK_AUTHORS),
                "date": (datetime.now() - timedelta(days=i * 7)).isoformat(),
            })

        return self._success(
            text=f"""## Tags

**Repository:** {repo}
**Total Tags:** {len(tags)}

| Tag | Commit | Date | Message |
|-----|--------|------|---------|
{self._format_tag_table(tags[:10])}

### Tag Information
- **Latest:** v1.2.3
- **Oldest:** v1.0.0
""",
            structured_output={
                "type": "tag_list",
                "repo": repo,
                "tags": tags,
                "total_count": len(tags),
            },
            suggested_actions=[
                self._action(
                    "create-tag",
                    "invoke",
                    "Create Tag",
                    {"agent_id": "nexusops.git", "query": "create tag v1.3.0"},
                ),
            ],
            metadata={"operation": "list_tags"},
        )

    def _handle_create_tag(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle create tag request"""
        tag_name = context.get("resource_name", "v1.3.0")
        commit_sha = context.get("commit", "HEAD")
        message = context.get("message", f"Release {tag_name}")
        repo = context.get("repo", "nexusops/backend")

        return self._success(
            text=f"""## Tag Created

**Repository:** {repo}
**Tag:** `{tag_name}`
**Commit:** `{commit_sha}`
**Message:** {message}
**Created At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Tag Details
- **Type:** Annotated
- **Author:** current-user@example.com
- **GPG Signed:** No

### Next Steps
- Push to remote: `git push origin {tag_name}`
- Create GitHub release
""",
            structured_output={
                "type": "tag_created",
                "repo": repo,
                "tag_name": tag_name,
                "commit_sha": commit_sha,
                "message": message,
                "created_at": datetime.now().isoformat(),
                "author": "current-user@example.com",
            },
            suggested_actions=[
                self._action(
                    "push-tag",
                    "invoke",
                    "Push Tag to Remote",
                    {"agent_id": "nexusops.git", "query": f"push tag {tag_name}"},
                ),
            ],
            metadata={"operation": "create_tag"},
        )

    def _handle_delete_tag(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle delete tag request"""
        tag_name = context.get("resource_name", "v1.0.0-beta")
        repo = context.get("repo", "nexusops/backend")

        return self._success(
            text=f"""## Tag Deleted

**Repository:** {repo}
**Deleted Tag:** `{tag_name}`
**Deleted At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Note
The tag has been deleted from both local and remote repositories.
""",
            structured_output={
                "type": "tag_deleted",
                "repo": repo,
                "tag_name": tag_name,
                "deleted_at": datetime.now().isoformat(),
            },
            metadata={"operation": "delete_tag"},
        )

    def _handle_create_pr(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle create pull request request"""
        head_branch = context.get("resource_name", "feature/new-feature")
        base_branch = context.get("base_branch", "develop")
        title = context.get("title", f"Feature: {head_branch.split('/')[-1]}")
        repo = context.get("repo", "nexusops/backend")
        pr_number = random.randint(100, 999)

        return self._success(
            text=f"""## Pull Request Created

**Repository:** {repo}
**PR Number:** #{pr_number}
**Title:** {title}

### Branch Information
- **Head:** `{head_branch}`
- **Base:** `{base_branch}`
- **Status:** Open

### PR Details
- **Author:** current-user@example.com
- **Created At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Labels:** enhancement, needs-review
- **Reviewers:** @alice, @bob

### Changes
- **Commits:** 3
- **Files Changed:** 5
- **Additions:** +150
- **Deletions:** -25

### URL
https://github.com/company/nexusops/pull/{pr_number}
""",
            structured_output={
                "type": "pr_created",
                "repo": repo,
                "pr_number": pr_number,
                "title": title,
                "head_branch": head_branch,
                "base_branch": base_branch,
                "status": "open",
                "author": "current-user@example.com",
                "url": f"https://github.com/company/nexusops/pull/{pr_number}",
                "created_at": datetime.now().isoformat(),
            },
            suggested_actions=[
                self._action(
                    "view-pr",
                    "navigate",
                    "View Pull Request",
                    {"url": f"https://github.com/company/nexusops/pull/{pr_number}"},
                ),
                self._action(
                    "request-review",
                    "invoke",
                    "Request Review",
                    {"agent_id": "nexusops.git", "query": f"request review for PR #{pr_number}"},
                ),
            ],
            metadata={"operation": "create_pr"},
        )

    def _handle_list_prs(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle list pull requests request"""
        repo = context.get("resource_name", "nexusops/backend")

        prs = [
            {
                "number": 125,
                "title": "Add user authentication",
                "head": "feature/user-auth",
                "base": "develop",
                "status": "open",
                "author": "alice@example.com",
                "created_at": (datetime.now() - timedelta(hours=24)).isoformat(),
                "reviews": 2,
                "approved": True,
            },
            {
                "number": 124,
                "title": "Fix login crash on mobile",
                "head": "bugfix/login-crash",
                "base": "main",
                "status": "open",
                "author": "bob@example.com",
                "created_at": (datetime.now() - timedelta(hours=48)).isoformat(),
                "reviews": 1,
                "approved": False,
            },
            {
                "number": 123,
                "title": "Update API to v2",
                "head": "feature/api-v2",
                "base": "develop",
                "status": "open",
                "author": "charlie@example.com",
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "reviews": 0,
                "approved": False,
            },
            {
                "number": 122,
                "title": "Security patch for XSS",
                "head": "hotfix/security-patch",
                "base": "main",
                "status": "merged",
                "author": "diana@example.com",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "reviews": 3,
                "approved": True,
            },
            {
                "number": 121,
                "title": "Add unit tests for auth",
                "head": "feature/auth-tests",
                "base": "develop",
                "status": "open",
                "author": "eve@example.com",
                "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "reviews": 1,
                "approved": False,
            },
        ]

        return self._success(
            text=f"""## Pull Requests

**Repository:** {repo}
**Open PRs:** {len([p for p in prs if p['status'] == 'open'])}

| # | Title | Author | Status | Reviews |
|---|-------|--------|--------|---------|
{self._format_pr_table(prs)}

### Summary
- **Open:** 4
- **Merged:** 1
- **Needs Review:** 2
- **Approved:** 2
""",
            structured_output={
                "type": "pr_list",
                "repo": repo,
                "prs": prs,
                "open_count": len([p for p in prs if p['status'] == 'open']),
            },
            suggested_actions=[
                self._action(
                    "create-pr",
                    "invoke",
                    "Create Pull Request",
                    {"agent_id": "nexusops.git", "query": "create pr from current branch"},
                ),
            ],
            metadata={"operation": "list_prs"},
        )

    def _handle_diff(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle diff request"""
        base = context.get("base_branch", "main")
        head = context.get("head_branch", context.get("resource_name", "develop"))
        repo = context.get("repo", "nexusops/backend")

        mock_diff = f"""diff --git a/src/api/auth.py b/src/api/auth.py
index 1234567..abcdefg 100644
--- a/src/api/auth.py
+++ b/src/api/auth.py
@@ -1,5 +1,10 @@
 import hashlib
+import jwt
+from datetime import datetime, timedelta

 def authenticate(username, password):
+    \"\"\"Authenticate user with credentials\"\"\"
+    if not username or not password:
+        raise ValueError("Missing credentials")
     user = get_user(username)
     if user and verify_password(password, user.password_hash):
         return create_token(user)
@@ -15,6 +20,15 @@
     return hashlib.sha256(password.encode()).hexdigest()

 def create_token(user):
+    \"\"\"Create JWT token for authenticated user\"\"\"
+    payload = {{
+        'user_id': user.id,
+        'exp': datetime.utcnow() + timedelta(hours=24)
+    }}
+    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
+
+def verify_token(token):
+    \"\"\"Verify and decode JWT token\"\"\"
+    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
"""

        return self._success(
            text=f"""## Diff: {base}..{head}

**Repository:** {repo}
**Base:** `{base}`
**Head:** `{head}`

### Summary
- **Files Changed:** 3
- **Additions:** +45
- **Deletions:** -12
- **Commits Ahead:** 5

### Diff
```diff
{mock_diff}
```

### Changed Files
1. `src/api/auth.py` (+25, -5)
2. `src/models/user.py` (+15, -5)
3. `tests/test_auth.py` (+5, -2)
""",
            structured_output={
                "type": "diff_result",
                "repo": repo,
                "base": base,
                "head": head,
                "files_changed": 3,
                "additions": 45,
                "deletions": 12,
                "commits_ahead": 5,
                "diff": mock_diff,
            },
            suggested_actions=[
                self._action(
                    "create-pr",
                    "invoke",
                    "Create Pull Request",
                    {"agent_id": "nexusops.git", "query": f"create pr {head} -> {base}"},
                ),
                self._action(
                    "view-commits",
                    "invoke",
                    "View Commits",
                    {"agent_id": "nexusops.git", "query": f"commit history {base}..{head}"},
                ),
            ],
            metadata={"operation": "diff"},
        )

    def _handle_commit_history(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle commit history request"""
        branch = context.get("resource_name", "main")
        repo = context.get("repo", "nexusops/backend")
        limit = context.get("limit", 10)

        commits = []
        for i in range(min(limit, 10)):
            commit_time = datetime.now() - timedelta(hours=i * 4)
            commits.append({
                "sha": self._generate_commit_sha(),
                "short_sha": self._generate_commit_sha()[:7],
                "message": random.choice([
                    "Add new feature for user authentication",
                    "Fix bug in payment processing",
                    "Update dependencies to latest versions",
                    "Refactor database connection handling",
                    "Add unit tests for API endpoints",
                    "Improve error handling in worker",
                    "Update documentation",
                    "Optimize query performance",
                ]),
                "author": random.choice(self.MOCK_AUTHORS),
                "date": commit_time.isoformat(),
                "relative_date": self._relative_time(commit_time),
            })

        return self._success(
            text=f"""## Commit History

**Repository:** {repo}
**Branch:** `{branch}`
**Total Commits:** 1,234

### Recent Commits
| SHA | Message | Author | Date |
|-----|---------|--------|------|
{self._format_commit_table(commits)}

### Statistics
- **Contributors:** 12
- **Commits this week:** 34
- **Commits this month:** 156
""",
            structured_output={
                "type": "commit_history",
                "repo": repo,
                "branch": branch,
                "commits": commits,
                "total_count": 1234,
            },
            suggested_actions=[
                self._action(
                    "view-commit",
                    "invoke",
                    "View Commit Details",
                    {"agent_id": "nexusops.git", "query": f"show commit {commits[0]['sha']}"},
                ),
                self._action(
                    "search-commits",
                    "invoke",
                    "Search Commits",
                    {"agent_id": "nexusops.git", "query": "search commits by author"},
                ),
            ],
            metadata={"operation": "commit_history"},
        )

    def _format_branch_table(self, branches: List[Dict[str, Any]]) -> str:
        """Format branches as markdown table"""
        rows = []
        for b in branches:
            protected = "Yes" if b.get("protected") else "No"
            ahead_behind = f"+{b.get('ahead', 0)}/-{b.get('behind', 0)}"
            rows.append(f"| {b['name']} | {b['sha'][:7]} | {protected} | {ahead_behind} |")
        return "\n".join(rows)

    def _format_tag_table(self, tags: List[Dict[str, Any]]) -> str:
        """Format tags as markdown table"""
        rows = []
        for t in tags:
            date = t.get("date", "")[:10]
            rows.append(f"| {t['name']} | {t['sha'][:7]} | {date} | {t.get('message', '')[:30]} |")
        return "\n".join(rows)

    def _format_pr_table(self, prs: List[Dict[str, Any]]) -> str:
        """Format PRs as markdown table"""
        rows = []
        for p in prs:
            status_emoji = {"open": "OPEN", "merged": "DONE", "closed": "CLOSED"}.get(p["status"], p["status"])
            approved = "Yes" if p.get("approved") else "No"
            rows.append(f"| #{p['number']} | {p['title'][:30]} | {p['author'].split('@')[0]} | {status_emoji} | {p['reviews']}/3 |")
        return "\n".join(rows)

    def _format_commit_table(self, commits: List[Dict[str, Any]]) -> str:
        """Format commits as markdown table"""
        rows = []
        for c in commits:
            rows.append(f"| {c['short_sha']} | {c['message'][:40]} | {c['author'].split('@')[0]} | {c['relative_date']} |")
        return "\n".join(rows)

    def _relative_time(self, dt: datetime) -> str:
        """Convert datetime to relative time string"""
        delta = datetime.now() - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago"

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for this agent"""
        return [
            {
                "name": "get_repo_status",
                "description": "Get repository status and information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository path or URL"},
                    },
                },
            },
            {
                "name": "list_branches",
                "description": "List all branches in the repository",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository path or URL"},
                        "filter": {"type": "string", "description": "Filter branches by pattern"},
                    },
                },
            },
            {
                "name": "create_branch",
                "description": "Create a new branch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch_name": {"type": "string", "description": "Name for the new branch"},
                        "base_branch": {"type": "string", "default": "develop", "description": "Base branch to create from"},
                        "repo": {"type": "string", "description": "Repository path"},
                    },
                    "required": ["branch_name"],
                },
            },
            {
                "name": "delete_branch",
                "description": "Delete a branch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch_name": {"type": "string", "description": "Branch to delete"},
                        "force": {"type": "boolean", "default": False, "description": "Force delete unmerged branch"},
                    },
                    "required": ["branch_name"],
                },
            },
            {
                "name": "create_pull_request",
                "description": "Create a pull request",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "PR title"},
                        "head_branch": {"type": "string", "description": "Source branch"},
                        "base_branch": {"type": "string", "default": "main", "description": "Target branch"},
                        "body": {"type": "string", "description": "PR description"},
                    },
                    "required": ["title", "head_branch"],
                },
            },
            {
                "name": "get_commit_history",
                "description": "Get commit history for a branch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "branch": {"type": "string", "default": "main", "description": "Branch to get history for"},
                        "limit": {"type": "integer", "default": 20, "description": "Maximum commits to return"},
                        "author": {"type": "string", "description": "Filter by author"},
                    },
                },
            },
            {
                "name": "get_diff",
                "description": "Get diff between branches or commits",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {"type": "string", "description": "Base branch or commit"},
                        "head": {"type": "string", "description": "Head branch or commit"},
                    },
                    "required": ["base", "head"],
                },
            },
            {
                "name": "create_tag",
                "description": "Create a new tag",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tag_name": {"type": "string", "description": "Tag name (e.g., v1.0.0)"},
                        "commit": {"type": "string", "default": "HEAD", "description": "Commit to tag"},
                        "message": {"type": "string", "description": "Tag message"},
                    },
                    "required": ["tag_name"],
                },
            },
        ]
