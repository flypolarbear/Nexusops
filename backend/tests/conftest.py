"""
NexusOps Backend - Test Configuration

Shared fixtures for pytest testing.
Provides:
- Async test client
- In-memory SQLite database for testing
- Sample data fixtures
- Event loop configuration
"""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, JSON
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set test environment before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "development"  # Must be one of: development, staging, production
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"


# ============================================
# SQLite JSONB Compatibility
# ============================================

# Monkey-patch JSONB to JSON for SQLite compatibility
def _patch_jsonb_for_sqlite():
    """
    Replace PostgreSQL JSONB type with JSON for SQLite compatibility.

    This is needed because SQLite doesn't support PostgreSQL's JSONB type.
    """
    try:
        from sqlalchemy.dialects import postgresql
        from sqlalchemy import JSON as _JSON

        # Replace JSONB with JSON for SQLite testing
        postgresql.JSONB = _JSON
        postgresql.base.JSONB = _JSON
    except ImportError:
        pass


_patch_jsonb_for_sqlite()


# ============================================
# Event Loop Fixtures
# ============================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================
# Database Fixtures
# ============================================

@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine using SQLite in-memory."""
    from app.models.database import Base
    from app.stores.agent_store import InstalledAgent, AgentReview

    # Use SQLite in-memory for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables (including new agent store models)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================
# Client Fixtures
# ============================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client with database support."""
    from app.main import app
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

    # Create a sync engine for testing with SQLite
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sync_engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
    )

    # Import Base and create tables
    from app.models.database import Base
    from app.stores.agent_store import InstalledAgent, AgentReview

    Base.metadata.create_all(sync_engine)

    # Create sync session factory
    SyncSession = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)

    # For async endpoints with sync TestClient, we need to use the sync session
    # The issue is FastAPI's Depends with async generators doesn't work well with TestClient
    # So we need to use a workaround

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def client_with_sync_db() -> Generator[TestClient, None, None]:
    """
    Create a synchronous test client with a real SQLite database.
    This fixture sets up an in-memory SQLite database and configures
    the app to use it for testing.
    """
    import asyncio
    from app.main import app
    from app.core.database import get_db

    # Create a new event loop for this fixture
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Create async engine
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )

        # Import Base and create tables
        from app.models.database import Base
        from app.stores.agent_store import InstalledAgent, AgentReview

        async def create_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        loop.run_until_complete(create_tables())

        # Create session factory
        async_session_maker = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async def override_get_db():
            async with async_session_maker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        # Override the dependency
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client

    finally:
        # Clean up
        app.dependency_overrides.clear()
        loop.run_until_complete(engine.dispose())
        loop.close()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def client_with_db(test_engine: AsyncEngine) -> AsyncGenerator[TestClient, None]:
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

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
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


# ============================================
# Sample Data Fixtures
# ============================================

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


@pytest.fixture
def sample_deployment_data() -> dict:
    """Sample deployment data for testing."""
    return {
        "region": "us-east-1",
        "namespace": "default",
    }


@pytest.fixture
def sample_agent_request() -> dict:
    """Sample agent request data for testing."""
    return {
        "request_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "agent_id": "nexusops.chat",
        "query": "What is the status of my deployment?",
        "context": {
            "user_id": "test-user",
            "tenant_id": "test-tenant",
            "project_id": "test-project",
        },
    }


@pytest.fixture
def sample_agent_manifest() -> dict:
    """Sample agent manifest for testing."""
    return {
        "agent_id": f"com.test.agent-{uuid.uuid4().hex[:8]}",
        "name": "Test Agent",
        "version": "1.0.0",
        "description": "A test agent for unit testing",
        "category": "test",
        "capabilities": ["query", "action"],
        "tools": [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        ],
    }


# ============================================
# User Fixtures
# ============================================

@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers() -> dict:
    """Mock authentication headers for testing."""
    # In demo mode, auth is not enforced
    return {}


# ============================================
# Store Reset Fixtures
# ============================================

@pytest.fixture(autouse=True)
def reset_agent_stores():
    """Reset agent stores before and after each test."""
    try:
        from app.stores.agent_store import clear_all
        clear_all()
    except ImportError:
        pass

    yield

    try:
        from app.stores.agent_store import clear_all
        clear_all()
    except ImportError:
        pass


# ============================================
# Mock Fixtures
# ============================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session for testing without actual DB."""
    mock = AsyncMock(spec=AsyncSession)
    mock.execute = AsyncMock()
    mock.scalar = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.close = AsyncMock()
    return mock


# ============================================
# Test Utilities
# ============================================

def generate_trace_id() -> str:
    """Generate a 32-character hex trace ID."""
    return uuid.uuid4().hex


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


# ============================================
# Pytest Configuration
# ============================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests - fast, isolated tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - tests with external services"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests - full workflow tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "agent: Agent-related tests"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    # Add timeout marker to slow tests
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.timeout(60))
