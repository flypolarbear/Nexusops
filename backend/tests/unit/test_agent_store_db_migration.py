"""
Test Agent Store Database Migration

Tests that verify the database-backed agent store functionality.
"""

import pytest
from datetime import datetime

from app.stores.agent_store import (
    # Database models
    InstalledAgent,
    AgentReview,
    # Async functions
    async_get_agent,
    async_save_agent,
    async_delete_agent,
    async_list_agents,
    async_is_agent_installed,
    async_get_install_status,
    async_install_agent,
    async_uninstall_agent,
    async_disable_agent,
    async_enable_agent,
    async_list_installed_agents,
    async_get_agent_reviews,
    async_add_review,
    # Legacy sync functions
    clear_all,
    agent_store,
    installed_agents,
)


@pytest.mark.asyncio
class TestAgentStoreDatabase:
    """Test database-backed agent store operations"""

    async def test_save_and_get_agent(self, db_session):
        """Test saving and retrieving an agent from database"""
        agent_id = "com.test.db-agent"
        agent_data = {
            "id": agent_id,
            "agent_id": agent_id,
            "name": "Test DB Agent",
            "version": "1.0.0",
            "manifest": {
                "name": "Test DB Agent",
                "version": "1.0.0",
                "category": "test",
            },
            "status": "active",
            "category": "test",
            "tags": ["test"],
            "capabilities": ["test"],
            "tools": [],
        }

        # Save agent
        await async_save_agent(agent_id, agent_data, db_session)
        await db_session.commit()

        # Get agent
        result = await async_get_agent(agent_id, db_session)

        assert result is not None
        assert result["agent_id"] == agent_id
        assert result["name"] == "Test DB Agent"
        assert result["version"] == "1.0.0"

    async def test_delete_agent(self, db_session):
        """Test deleting an agent from database"""
        agent_id = "com.test.delete-agent"
        agent_data = {
            "id": agent_id,
            "agent_id": agent_id,
            "name": "Delete Test Agent",
            "version": "1.0.0",
            "manifest": {},
            "status": "active",
        }

        # Save and verify
        await async_save_agent(agent_id, agent_data, db_session)
        await db_session.commit()

        result = await async_get_agent(agent_id, db_session)
        assert result is not None

        # Delete
        deleted = await async_delete_agent(agent_id, db_session)
        await db_session.commit()

        assert deleted is True

        # Verify deleted
        result = await async_get_agent(agent_id, db_session)
        assert result is None

    async def test_list_agents(self, db_session):
        """Test listing agents from database"""
        # Save multiple agents
        for i in range(3):
            agent_id = f"com.test.list-agent-{i}"
            agent_data = {
                "id": agent_id,
                "agent_id": agent_id,
                "name": f"List Test Agent {i}",
                "version": "1.0.0",
                "manifest": {"category": "test"},
                "status": "active",
                "category": "test",
                "tags": [],
                "capabilities": [],
                "tools": [],
            }
            await async_save_agent(agent_id, agent_data, db_session)

        await db_session.commit()

        # List all agents
        agents = await async_list_agents(db=db_session)
        assert len(agents) >= 3

        # Filter by category
        test_agents = await async_list_agents(category="test", db=db_session)
        assert len(test_agents) >= 3


@pytest.mark.asyncio
class TestInstalledAgentDatabase:
    """Test installed agent database operations"""

    async def test_install_agent(self, db_session):
        """Test installing an agent"""
        agent_id = "com.test.install-agent"

        # Initially not installed
        is_installed = await async_is_agent_installed(agent_id, db_session)
        assert is_installed is False

        status = await async_get_install_status(agent_id, db_session)
        assert status == "not_installed"

        # Install
        result = await async_install_agent(agent_id, "test-user", db_session)
        await db_session.commit()

        assert result["install_status"] == "installed"
        assert result["installed_by"] == "test-user"

        # Verify installed
        is_installed = await async_is_agent_installed(agent_id, db_session)
        assert is_installed is True

        status = await async_get_install_status(agent_id, db_session)
        assert status == "installed"

    async def test_uninstall_agent(self, db_session):
        """Test uninstalling an agent"""
        agent_id = "com.test.uninstall-agent"

        # Install first
        await async_install_agent(agent_id, "test-user", db_session)
        await db_session.commit()

        # Verify installed
        assert await async_is_agent_installed(agent_id, db_session) is True

        # Uninstall
        result = await async_uninstall_agent(agent_id, db_session)
        await db_session.commit()

        assert result is True

        # Verify uninstalled
        assert await async_is_agent_installed(agent_id, db_session) is False

    async def test_disable_enable_agent(self, db_session):
        """Test disabling and enabling an agent"""
        agent_id = "com.test.disable-agent"

        # Install
        await async_install_agent(agent_id, "test-user", db_session)
        await db_session.commit()

        # Disable
        result = await async_disable_agent(agent_id, db_session)
        await db_session.commit()

        assert result is True
        status = await async_get_install_status(agent_id, db_session)
        assert status == "disabled"

        # Enable
        result = await async_enable_agent(agent_id, db_session)
        await db_session.commit()

        assert result is True
        status = await async_get_install_status(agent_id, db_session)
        assert status == "installed"

    async def test_list_installed_agents(self, db_session):
        """Test listing installed agents"""
        # Install multiple agents
        for i in range(3):
            agent_id = f"com.test.installed-{i}"
            await async_install_agent(agent_id, f"user-{i}", db_session)

        await db_session.commit()

        # List installed
        installed = await async_list_installed_agents(db_session)
        assert len(installed) >= 3

        # Verify data structure
        for item in installed:
            assert "agent_id" in item
            assert "install_status" in item
            assert "installed_at" in item


@pytest.mark.asyncio
class TestAgentReviewDatabase:
    """Test agent review database operations"""

    async def test_add_and_get_reviews(self, db_session):
        """Test adding and getting reviews"""
        agent_id = "com.test.review-agent"

        # Add review
        review = await async_add_review(
            agent_id=agent_id,
            user_id="test-user",
            rating=4.5,
            comment="Great agent!",
            db=db_session,
        )
        await db_session.commit()

        assert review["agent_id"] == agent_id
        assert review["user_id"] == "test-user"
        assert review["rating"] == 4.5
        assert review["comment"] == "Great agent!"

        # Get reviews
        reviews = await async_get_agent_reviews(agent_id, db_session)
        assert len(reviews) == 1
        assert reviews[0]["rating"] == 4.5

    async def test_multiple_reviews(self, db_session):
        """Test multiple reviews for an agent"""
        agent_id = "com.test.multi-review-agent"

        # Add multiple reviews
        for i in range(3):
            await async_add_review(
                agent_id=agent_id,
                user_id=f"user-{i}",
                rating=3.0 + i,
                comment=f"Review {i}",
                db=db_session,
            )

        await db_session.commit()

        # Get all reviews
        reviews = await async_get_agent_reviews(agent_id, db_session)
        assert len(reviews) == 3


# Run tests with: pytest backend/tests/unit/test_agent_store_db_migration.py -v
