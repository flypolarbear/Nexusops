"""
NexusOps Backend - Projects API Integration Tests

Tests for the Projects CRUD API endpoints:
- List projects (with pagination)
- Create project
- Get project details
- Update project
- Delete project
- Error handling (not found)

Run with: pytest -m integration backend/tests/integration/test_projects_api.py -v
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
import uuid


# ============================================
# SQLite JSONB Compatibility
# ============================================

def _jsonb_to_json_for_sqlite(dbapi_connection, connection_record):
    """
    Convert JSONB to JSON for SQLite compatibility.

    This is needed because SQLite doesn't support PostgreSQL's JSONB type.
    """
    cursor = dbapi_connection.cursor()
    # This is handled at the SQLAlchemy type level, not SQLite level


def get_json_type():
    """Get the appropriate JSON type for the current database."""
    # For SQLite testing, we use JSON instead of JSONB
    return JSON


# ============================================
# Test Fixtures
# ============================================

@pytest_asyncio.fixture(scope="function")
async def test_engine() -> "AsyncEngine":
    """Create a test database engine using SQLite in-memory."""
    from sqlalchemy import MetaData
    from sqlalchemy.orm import DeclarativeBase

    # Create a custom base with JSON instead of JSONB for SQLite
    class TestBase(DeclarativeBase):
        pass

    # Import and patch models to use JSON instead of JSONB
    # We need to temporarily replace JSONB with JSON in the column types
    from app.models import database as db_module

    # Store original types
    original_types = {}

    # Patch JSONB columns to use JSON for SQLite testing
    jsonb_columns = [
        ('Project', 'extra_data'),
        ('Version', 'deployed_regions'),
        ('DeploymentStep', 'details'),
        ('AgentState', 'state_value'),
        ('AgentInvocation', 'request'),
        ('AgentInvocation', 'response'),
        ('AgentRegistration', 'manifest'),
    ]

    for table_name, col_name in jsonb_columns:
        if hasattr(db_module, table_name):
            table_class = getattr(db_module, table_name)
            if hasattr(table_class, col_name):
                col = getattr(table_class, col_name)
                original_types[(table_name, col_name)] = col.property.columns[0].type
                # Replace JSONB with JSON
                col.property.columns[0].type = JSON()

    # Create engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables using the original Base (now with patched JSON types)
    from app.models.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Restore original types
    for (table_name, col_name), original_type in original_types.items():
        table_class = getattr(db_module, table_name)
        col = getattr(table_class, col_name)
        col.property.columns[0].type = original_type


@pytest_asyncio.fixture(scope="function")
async def client(test_engine: AsyncEngine) -> "AsyncClient":
    """
    Create a test client with database dependency override.

    This fixture creates an in-memory SQLite database and overrides
    the get_db dependency to use the test database session.
    """
    from app.main import app
    from app.core.database import get_db

    # Create session factory for test database
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db():
        """Override get_db to use test database."""
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for testing."""
    return {
        "name": f"test-project-{uuid.uuid4().hex[:8]}",
        "description": "Test project for unit testing",
        "git_repo": "https://github.com/example/test-project.git",
    }


@pytest.fixture
def sample_version_data() -> dict:
    """Sample version data for testing."""
    return {
        "codename": f"v1.0.0-{uuid.uuid4().hex[:4]}",
        "version": "1.0.0",
        "git_branch": "main",
        "git_commit": "abc123def456",
    }


# ============================================
# Test: List Projects Empty
# ============================================

class TestListProjectsEmpty:
    """Test listing projects when the database is empty."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_projects_empty(self, client: AsyncClient):
        """CT-PROJ-001: Empty database should return empty list with pagination info."""
        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()

        # Verify paginated response structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        # Verify empty state
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 0


# ============================================
# Test: Create Project
# ============================================

class TestCreateProject:
    """Test creating new projects."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_project(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-002: Create a new project with valid data."""
        response = await client.post("/api/v1/projects", json=sample_project_data)

        assert response.status_code == 201
        data = response.json()

        # Verify response contains project data
        assert "id" in data
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert data["git_repo"] == sample_project_data["git_repo"]
        assert data["status"] == "active"
        assert "created_at" in data
        assert "updated_at" in data

        # Verify ID format (proj-{8 hex chars})
        assert data["id"].startswith("proj-")
        assert len(data["id"]) == 13  # "proj-" + 8 hex chars

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_project_minimal(self, client: AsyncClient):
        """CT-PROJ-003: Create project with only required fields (name)."""
        project_data = {"name": f"minimal-project-{uuid.uuid4().hex[:8]}"}
        response = await client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == project_data["name"]
        assert data["description"] is None
        assert data["git_repo"] is None
        assert data["status"] == "active"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_project_duplicate_name_fails(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-004: Creating project with duplicate name should fail."""
        # Create first project
        response1 = await client.post("/api/v1/projects", json=sample_project_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await client.post("/api/v1/projects", json=sample_project_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_project_missing_name_fails(self, client: AsyncClient):
        """CT-PROJ-005: Creating project without name should fail validation."""
        response = await client.post("/api/v1/projects", json={})
        assert response.status_code == 422  # Validation error


# ============================================
# Test: Get Project
# ============================================

class TestGetProject:
    """Test retrieving project details."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_project(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-006: Get project details by ID."""
        # Create a project first
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Get the project
        response = await client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify ProjectDetail structure (includes versions)
        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert data["git_repo"] == sample_project_data["git_repo"]
        assert data["status"] == "active"
        assert "versions" in data
        assert "version_count" in data
        assert data["version_count"] == 0
        assert data["versions"] == []

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_project_with_versions(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-007: Get project details including associated versions."""
        # Create a project
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Create a version for the project (VersionCreate requires project_id)
        version_data = {
            "project_id": project_id,
            "codename": f"v1.0.0-{uuid.uuid4().hex[:4]}",
            "version": "1.0.0",
            "git_branch": "main",
            "git_commit": "abc123def456",
        }
        version_response = await client.post(f"/api/v1/projects/{project_id}/versions", json=version_data)
        assert version_response.status_code == 201

        # Get project details
        response = await client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["version_count"] == 1
        assert len(data["versions"]) == 1
        assert data["versions"][0]["codename"] == version_data["codename"]


# ============================================
# Test: Update Project
# ============================================

class TestUpdateProject:
    """Test updating projects."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_project(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-008: Update project with partial data."""
        # Create a project first
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Update the project
        update_data = {
            "description": "Updated description",
            "status": "archived"
        }
        response = await client.patch(f"/api/v1/projects/{project_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        # Verify updates applied
        assert data["description"] == "Updated description"
        assert data["status"] == "archived"
        # Original data should remain
        assert data["name"] == sample_project_data["name"]
        assert data["git_repo"] == sample_project_data["git_repo"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_project_name(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-009: Update project name."""
        # Create a project first
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Update name
        new_name = f"updated-name-{uuid.uuid4().hex[:8]}"
        response = await client.patch(f"/api/v1/projects/{project_id}", json={"name": new_name})

        assert response.status_code == 200
        assert response.json()["name"] == new_name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_project_empty_patch(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-010: Update project with empty patch should succeed."""
        # Create a project first
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        original_data = create_response.json()

        # Empty patch
        response = await client.patch(f"/api/v1/projects/{project_id}", json={})

        assert response.status_code == 200
        data = response.json()
        # Data should remain unchanged
        assert data["name"] == original_data["name"]
        assert data["description"] == original_data["description"]


# ============================================
# Test: Delete Project
# ============================================

class TestDeleteProject:
    """Test deleting projects."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_project(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-011: Delete an existing project."""
        # Create a project first
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Delete the project
        delete_response = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 204

        # Verify project no longer exists
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_project_removes_from_list(self, client: AsyncClient, sample_project_data: dict):
        """CT-PROJ-012: Deleted project should not appear in list."""
        # Create a project
        create_response = await client.post("/api/v1/projects", json=sample_project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Verify it appears in list
        list_response = await client.get("/api/v1/projects")
        assert list_response.json()["total"] >= 1

        # Delete the project
        delete_response = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 204

        # Verify count decreased
        list_response_after = await client.get("/api/v1/projects")
        assert list_response_after.json()["total"] == list_response.json()["total"] - 1


# ============================================
# Test: Project Not Found
# ============================================

class TestProjectNotFound:
    """Test error handling for non-existent projects."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_project_not_found(self, client: AsyncClient):
        """CT-PROJ-013: Get non-existent project should return 404."""
        fake_id = f"proj-{uuid.uuid4().hex[:8]}"
        response = await client.get(f"/api/v1/projects/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_project_not_found(self, client: AsyncClient):
        """CT-PROJ-014: Update non-existent project should return 404."""
        fake_id = f"proj-{uuid.uuid4().hex[:8]}"
        response = await client.patch(f"/api/v1/projects/{fake_id}", json={"name": "new-name"})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_project_not_found(self, client: AsyncClient):
        """CT-PROJ-015: Delete non-existent project should return 404."""
        fake_id = f"proj-{uuid.uuid4().hex[:8]}"
        response = await client.delete(f"/api/v1/projects/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ============================================
# Test: Pagination
# ============================================

class TestPagination:
    """Test pagination functionality."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pagination(self, client: AsyncClient):
        """CT-PROJ-016: Verify pagination works correctly."""
        # Create multiple projects
        num_projects = 25
        created_ids = []
        for i in range(num_projects):
            project_data = {
                "name": f"pagination-test-{i}-{uuid.uuid4().hex[:8]}",
                "description": f"Project {i} for pagination testing"
            }
            response = await client.post("/api/v1/projects", json=project_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # Test first page (default page_size=20)
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= num_projects
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["items"]) == 20
        assert data["total_pages"] >= 2

        # Test second page
        response_page2 = await client.get("/api/v1/projects?page=2")
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()

        assert data_page2["page"] == 2
        assert data_page2["total"] == data["total"]
        # Ensure items on page 2 are different from page 1
        page1_ids = {item["id"] for item in data["items"]}
        page2_ids = {item["id"] for item in data_page2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pagination_custom_page_size(self, client: AsyncClient):
        """CT-PROJ-017: Verify custom page_size works correctly."""
        # Create multiple projects
        for i in range(10):
            project_data = {"name": f"pagesize-test-{i}-{uuid.uuid4().hex[:8]}"}
            await client.post("/api/v1/projects", json=project_data)

        # Test with page_size=5
        response = await client.get("/api/v1/projects?page_size=5")
        assert response.status_code == 200
        data = response.json()

        assert data["page_size"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pagination_page_boundaries(self, client: AsyncClient):
        """CT-PROJ-018: Verify page parameter validation."""
        # Test page=0 should fail (ge=1 constraint)
        response = await client.get("/api/v1/projects?page=0")
        assert response.status_code == 422

        # Test negative page should fail
        response = await client.get("/api/v1/projects?page=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pagination_page_size_boundaries(self, client: AsyncClient):
        """CT-PROJ-019: Verify page_size parameter validation."""
        # Test page_size=0 should fail (ge=1 constraint)
        response = await client.get("/api/v1/projects?page_size=0")
        assert response.status_code == 422

        # Test page_size > 100 should fail (le=100 constraint)
        response = await client.get("/api/v1/projects?page_size=101")
        assert response.status_code == 422

        # Test valid max page_size
        response = await client.get("/api/v1/projects?page_size=100")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pagination_with_status_filter(self, client: AsyncClient):
        """CT-PROJ-020: Verify pagination works with status filter."""
        # Create projects with different statuses
        for i in range(5):
            project_data = {"name": f"status-filter-test-{i}-{uuid.uuid4().hex[:8]}"}
            response = await client.post("/api/v1/projects", json=project_data)
            if i < 2 and response.status_code == 201:
                # Archive first two projects
                project_id = response.json()["id"]
                await client.patch(f"/api/v1/projects/{project_id}", json={"status": "archived"})

        # Filter by active status
        response = await client.get("/api/v1/projects?status=active")
        assert response.status_code == 200
        data = response.json()

        # All returned items should have status=active
        for item in data["items"]:
            assert item["status"] == "active"


# ============================================
# Test: Full CRUD Workflow
# ============================================

class TestFullCRUDWorkflow:
    """Test complete CRUD workflow in sequence."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_crud_workflow(self, client: AsyncClient):
        """CT-PROJ-021: Complete CRUD workflow: Create -> Read -> Update -> Delete."""
        # CREATE
        project_data = {
            "name": f"crud-workflow-{uuid.uuid4().hex[:8]}",
            "description": "Original description",
            "git_repo": "https://github.com/example/original.git"
        }
        create_response = await client.post("/api/v1/projects", json=project_data)
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        assert create_response.json()["status"] == "active"

        # READ
        read_response = await client.get(f"/api/v1/projects/{project_id}")
        assert read_response.status_code == 200
        assert read_response.json()["name"] == project_data["name"]
        assert read_response.json()["description"] == project_data["description"]

        # UPDATE
        update_data = {
            "description": "Updated description",
            "git_repo": "https://github.com/example/updated.git",
            "status": "archived"
        }
        update_response = await client.patch(f"/api/v1/projects/{project_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated description"
        assert update_response.json()["git_repo"] == "https://github.com/example/updated.git"
        assert update_response.json()["status"] == "archived"

        # Verify update persisted
        read_again_response = await client.get(f"/api/v1/projects/{project_id}")
        assert read_again_response.json()["description"] == "Updated description"

        # DELETE
        delete_response = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        read_deleted_response = await client.get(f"/api/v1/projects/{project_id}")
        assert read_deleted_response.status_code == 404


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
