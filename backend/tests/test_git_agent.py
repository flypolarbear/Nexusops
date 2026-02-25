"""
Git Agent Unit Tests

Test cases for nexusops.git agent handler.
"""

import pytest
import asyncio

from app.agents.git import GitAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorContext, ExecutorResult


@pytest.fixture
def agent():
    """Create GitAgentHandler instance"""
    return GitAgentHandler()


@pytest.fixture
def context():
    """Create ExecutorContext for testing"""
    return ExecutorContext(
        trace_id="test-trace-12345678901234567890",
        request_id="test-request-001",
        agent_id="nexusops.git",
    )


@pytest.fixture
def make_request(context):
    """Factory to create ExecutorRequest"""
    def _make(query: str, request_context: dict = None):
        return ExecutorRequest(
            context=context,
            query=query,
            request_context=request_context or {},
        )
    return _make


class TestGitAgentBasics:
    """Basic agent property tests"""

    def test_agent_id(self, agent):
        """Agent ID should be nexusops.git"""
        assert agent.agent_id == "nexusops.git"

    def test_capabilities(self, agent):
        """Agent should have all required capabilities"""
        expected_capabilities = [
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
        assert set(agent.capabilities) == set(expected_capabilities)

    def test_manifest(self, agent):
        """Manifest should contain correct metadata"""
        manifest = agent.get_manifest()
        assert manifest["agent_id"] == "nexusops.git"
        assert manifest["name"] == "Git Agent"
        assert manifest["version"] == "1.0.0"
        assert manifest["category"] == "git"
        assert len(manifest["tools"]) == 8

    def test_get_tools(self, agent):
        """Should return 8 tool definitions"""
        tools = agent.get_tools()
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "get_repo_status",
            "list_branches",
            "create_branch",
            "delete_branch",
            "create_pull_request",
            "get_commit_history",
            "get_diff",
            "create_tag",
        ]
        assert set(tool_names) == set(expected_tools)


class TestRepoStatus:
    """Tests for repository status"""

    @pytest.mark.asyncio
    async def test_status_query_returns_success(self, agent, make_request):
        """Status query should return success"""
        request = make_request("status")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_status_query_has_structured_output(self, agent, make_request):
        """Status query should return structured output"""
        request = make_request("repo status")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "git_status"

    @pytest.mark.asyncio
    async def test_status_query_has_branch_info(self, agent, make_request):
        """Status query should return branch info"""
        request = make_request("show repo info")
        result = await agent.handle(request)
        assert "current_branch" in result.structured_output
        assert "default_branch" in result.structured_output

    @pytest.mark.asyncio
    async def test_status_query_has_suggested_actions(self, agent, make_request):
        """Status query should return suggested actions"""
        request = make_request("status")
        result = await agent.handle(request)
        assert len(result.suggested_actions) >= 2


class TestBranchOperations:
    """Tests for branch operations"""

    @pytest.mark.asyncio
    async def test_list_branches_returns_success(self, agent, make_request):
        """List branches should return success"""
        request = make_request("list branches")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_list_branches_has_structured_output(self, agent, make_request):
        """List branches should return structured output"""
        request = make_request("show all branches")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "branch_list"

    @pytest.mark.asyncio
    async def test_list_branches_has_branches_array(self, agent, make_request):
        """List branches should return branches array"""
        request = make_request("list branches")
        result = await agent.handle(request)
        assert "branches" in result.structured_output
        assert len(result.structured_output["branches"]) > 0

    @pytest.mark.asyncio
    async def test_create_branch_returns_success(self, agent, make_request):
        """Create branch should return success"""
        request = make_request("create branch feature/test")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_branch_has_structured_output(self, agent, make_request):
        """Create branch should return structured output"""
        request = make_request("new branch feature/my-feature")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "branch_created"
        assert "branch_name" in result.structured_output

    @pytest.mark.asyncio
    async def test_delete_branch_returns_success(self, agent, make_request):
        """Delete branch should return success"""
        request = make_request("delete branch feature/old")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_branch_has_structured_output(self, agent, make_request):
        """Delete branch should return structured output"""
        request = make_request("remove branch feature/test")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "branch_deleted"


class TestTagOperations:
    """Tests for tag operations"""

    @pytest.mark.asyncio
    async def test_list_tags_returns_success(self, agent, make_request):
        """List tags should return success"""
        request = make_request("list tags")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_list_tags_has_structured_output(self, agent, make_request):
        """List tags should return structured output"""
        request = make_request("show tags")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "tag_list"

    @pytest.mark.asyncio
    async def test_create_tag_returns_success(self, agent, make_request):
        """Create tag should return success"""
        request = make_request("create tag v1.0.0")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_tag_has_structured_output(self, agent, make_request):
        """Create tag should return structured output"""
        request = make_request("new tag v1.2.0")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "tag_created"

    @pytest.mark.asyncio
    async def test_delete_tag_returns_success(self, agent, make_request):
        """Delete tag should return success"""
        request = make_request("delete tag v1.0.0-beta")
        result = await agent.handle(request)
        assert result.success is True


class TestPullRequestOperations:
    """Tests for PR/MR operations"""

    @pytest.mark.asyncio
    async def test_list_prs_returns_success(self, agent, make_request):
        """List PRs should return success"""
        request = make_request("list pull requests")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_list_prs_has_structured_output(self, agent, make_request):
        """List PRs should return structured output"""
        request = make_request("show prs")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pr_list"

    @pytest.mark.asyncio
    async def test_list_prs_has_prs_array(self, agent, make_request):
        """List PRs should return prs array"""
        request = make_request("list prs")
        result = await agent.handle(request)
        assert "prs" in result.structured_output
        assert len(result.structured_output["prs"]) > 0

    @pytest.mark.asyncio
    async def test_create_pr_returns_success(self, agent, make_request):
        """Create PR should return success"""
        request = make_request("create pull request feature/test -> main")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_pr_has_structured_output(self, agent, make_request):
        """Create PR should return structured output"""
        request = make_request("new pr from feature/test")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "pr_created"
        assert "pr_number" in result.structured_output

    @pytest.mark.asyncio
    async def test_create_mr_returns_success(self, agent, make_request):
        """Create MR (merge request) should return success"""
        request = make_request("create merge request feature/test")
        result = await agent.handle(request)
        assert result.success is True


class TestDiffOperations:
    """Tests for diff operations"""

    @pytest.mark.asyncio
    async def test_diff_returns_success(self, agent, make_request):
        """Diff should return success"""
        request = make_request("diff main..develop")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_diff_has_structured_output(self, agent, make_request):
        """Diff should return structured output"""
        # Use explicit "diff" keyword
        request = make_request("diff main develop")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "diff_result"

    @pytest.mark.asyncio
    async def test_diff_has_diff_content(self, agent, make_request):
        """Diff should return diff content"""
        request = make_request("diff main..develop")
        result = await agent.handle(request)
        assert "diff" in result.structured_output
        assert "files_changed" in result.structured_output


class TestCommitHistory:
    """Tests for commit history"""

    @pytest.mark.asyncio
    async def test_commit_history_returns_success(self, agent, make_request):
        """Commit history should return success"""
        request = make_request("commit history")
        result = await agent.handle(request)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_commit_history_has_structured_output(self, agent, make_request):
        """Commit history should return structured output"""
        request = make_request("show commit log")
        result = await agent.handle(request)
        assert result.structured_output is not None
        assert result.structured_output["type"] == "commit_history"

    @pytest.mark.asyncio
    async def test_commit_history_has_commits_array(self, agent, make_request):
        """Commit history should return commits array"""
        request = make_request("log")
        result = await agent.handle(request)
        assert "commits" in result.structured_output
        assert len(result.structured_output["commits"]) > 0

    @pytest.mark.asyncio
    async def test_commit_history_entries_have_required_fields(self, agent, make_request):
        """Each commit should have required fields"""
        request = make_request("commit history")
        result = await agent.handle(request)
        for commit in result.structured_output["commits"]:
            assert "sha" in commit
            assert "message" in commit
            assert "author" in commit
            assert "date" in commit


# Run tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
