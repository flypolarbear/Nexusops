# NexusOps - AI Native Operations Platform

This file provides guidance for agentic coding agents working in this repository.

## Project Overview

NexusOps is an AI-native operations platform for multi-modal conversational systems. It consists of:
- **Backend**: FastAPI (Python 3.11+) with async SQLAlchemy, Pydantic v2
- **Frontend**: React 18 + TypeScript with Vite, Ant Design, Tailwind CSS, Zustand

---

## Build / Lint / Test Commands

### Backend (Python)

```bash
# Start development server
cd backend && uvicorn app.main:app --reload --port 8000

# Run all tests
cd backend && pytest tests/ -v

# Run single test file
cd backend && pytest tests/unit/test_gateway_contract.py -v

# Run single test function
cd backend && pytest tests/unit/test_gateway_contract.py::TestRequestContext::test_empty_request_context -v

# Run tests by marker
cd backend && pytest tests/ -v -m unit           # Unit tests only
cd backend && pytest tests/ -v -m integration    # Integration tests only
cd backend && pytest tests/ -v -m "not slow"     # Skip slow tests

# Lint and format
cd backend && ruff check . --fix && black . && mypy app/

# Run mypy only
cd backend && mypy app/
```

### Frontend (TypeScript/React)

```bash
# Install dependencies
cd frontend && npm install

# Start development server (http://localhost:3000)
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Lint
cd frontend && npm run lint

# Type check
cd frontend && npx tsc --noEmit
```

### Infrastructure

```bash
# Start Docker services (PostgreSQL, Redis)
cd docker && docker-compose -f docker-compose.middleware.yml up -d

# Stop Docker services
cd docker && docker-compose -f docker-compose.middleware.yml down

# Initialize database
cd docker && PGPASSWORD=nexusops psql -h localhost -U nexusops -d nexusops -f scripts/init-db.sql
```

### Makefile Shortcuts

```bash
make dev          # Start full development environment
make backend      # Start FastAPI backend only
make frontend     # Start frontend only
make test         # Run all tests (backend + frontend)
make lint         # Run all linters
make docker-up    # Start Docker services
make docker-down  # Stop Docker services
```

---

## Code Style Guidelines

### Backend (Python)

#### Formatting & Linting
- **Line length**: 100 characters
- **Formatter**: Black (line-length=100)
- **Linter**: Ruff (target-version=py311)
- **Type checker**: mypy (strict mode enabled)

#### Imports
```python
# Standard library first
import asyncio
from typing import AsyncGenerator, Optional

# Third-party packages second
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports last (use explicit relative or absolute)
from app.core.config import settings
from app.models.database import Base
```

#### Naming Conventions
- **Functions/variables**: `snake_case` (e.g., `get_overview`, `user_id`)
- **Classes**: `PascalCase` (e.g., `OverviewStats`, `InvokeRequest`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_PREFIX`, `SECRET_KEY`)
- **Private methods**: `_leading_underscore` (e.g., `_patch_jsonb_for_sqlite`)

#### Type Annotations
```python
# Always use type annotations
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    ...

def process_request(request: InvokeRequest) -> InvokeResponse:
    ...

# Use Optional for nullable types
from typing import Optional
name: Optional[str] = None

# Use list/dict generics directly (Python 3.11+)
items: list[str] = []
data: dict[str, Any] = {}
```

#### Docstrings
```python
def function_name(param: str) -> dict:
    """
    Brief description of function.

    More detailed description if needed.

    Args:
        param: Description of parameter.

    Returns:
        Description of return value.
    """
    ...
```

#### Error Handling
```python
# Use Pydantic for validation errors
from pydantic import ValidationError

# Use HTTPException for API errors
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Resource not found")

# Use custom error codes in contracts
error = ErrorDetail(code="AGENT_NOT_FOUND", message="Agent not found")
```

### Frontend (TypeScript/React)

#### Formatting
- **TypeScript**: Strict mode enabled (`strict: true`)
- **No unused locals/parameters**: Enforced by tsconfig
- **Path alias**: Use `@/` for `src/` imports

#### Imports
```typescript
// React imports first
import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

// External packages second
import { create } from 'zustand'
import axios from 'axios'

// Local imports last with @ alias
import { useAuthStore } from '@/stores/authStore'
import { User } from '@/types'
import MainLayout from '@/components/layout/MainLayout'
```

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `Dashboard`, `MainLayout`)
- **Functions/variables**: `camelCase` (e.g., `useAuthStore`, `handleLogin`)
- **Files**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **CSS classes**: Use Tailwind utility classes

#### Component Structure
```typescript
// Functional components with hooks
function ComponentName() {
  const [state, setState] = useState(initialState)
  const { data } = useStore()

  useEffect(() => {
    // Side effects
  }, [])

  return (
    // JSX
  )
}

export default ComponentName
```

#### State Management
```typescript
// Use Zustand for global state
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  user: User | null
  login: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      login: (user) => set({ user }),
      logout: () => set({ user: null }),
    }),
    { name: 'storage-key' }
  )
)
```

#### API Calls
```typescript
// Use axios with interceptors
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
})

// Add auth token automatically
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

---

## Testing Guidelines

### Backend Tests

#### Test Structure
```
backend/tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, isolated unit tests
├── integration/         # Tests with DB/external services
└── sdk/                 # SDK-specific tests
```

#### Test Markers
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests with database/external services
@pytest.mark.e2e           # Full workflow tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.agent         # Agent-related tests
@pytest.mark.api           # API endpoint tests
@pytest.mark.llm           # LLM integration tests
@pytest.mark.k8s           # Kubernetes integration tests
```

#### Writing Tests
```python
import pytest
from pydantic import ValidationError

class TestModelName:
    """Test ModelName functionality"""

    def test_basic_case(self):
        """Test description"""
        # Arrange
        data = {"key": "value"}

        # Act
        result = ModelName(**data)

        # Assert
        assert result.key == "value"

    def test_error_case(self):
        """Test that invalid input raises error"""
        with pytest.raises(ValidationError):
            ModelName(invalid_field="value")
```

#### Fixtures (conftest.py)
```python
@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for testing."""
    return {
        "name": "test-project",
        "description": "Test description",
    }

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
```

---

## Project Structure

```
NexusOps/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers
│   │   ├── core/          # Config, database setup
│   │   ├── gateway/       # Agent gateway contracts
│   │   ├── llm/           # LLM integrations
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic
│   │   ├── stores/        # Data stores (agent store)
│   │   └── main.py        # FastAPI app entry
│   ├── tests/             # Test files
│   ├── pyproject.toml     # Project config (ruff, black, mypy)
│   ├── pytest.ini         # pytest configuration
│   └── requirements.txt   # Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── stores/        # Zustand stores
│   │   ├── services/      # API services
│   │   ├── hooks/         # Custom hooks
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker/                # Docker Compose files
├── agentic_pact/          # Multi-agent workflow specs
│   ├── PACT.md            # Collaboration rules
│   ├── templates/         # Document templates
│   ├── state/             # Lock registry, task list
│   └── specs/             # Feature specifications
└── Makefile               # Development commands
```

---

## Important Rules

1. **Never suppress type errors**: No `as any`, `@ts-ignore`, or `@ts-expect-error`
2. **Never use empty catch blocks**: Always handle or re-raise exceptions
3. **Follow existing patterns**: Check similar files before creating new ones
4. **Use path aliases**: `@/` in frontend, explicit imports in backend
5. **Async first**: Use async/await patterns in both backend and frontend
6. **Pydantic v2**: Use `model_dump()` instead of `dict()`, `model_validate()` instead of `parse_obj()`
7. **Docstrings required**: For all public functions and classes

---

## Agentic Pact Workflow

Before starting any task:
1. Read `agentic_pact/PACT.md` for collaboration rules
2. Check `agentic_pact/state/lock_registry.json` for active work
3. Follow spec-driven workflow in `agentic_pact/specs/SPEC-*.md`

If rules conflict, defer to `agentic_pact/PACT.md`.

---

## OMO × Spec-Kit Bridge

This repo uses Spec-Kit for **spec/plan/tasks artifacts** and OMO for **execution**.
Use the bridge rules to avoid workflow conflicts:

- **Bridge Contract**: `OMO_SPEC_KIT_BRIDGE.md`
- **Spec-Kit Output**: `specs/<feature>/{spec.md,plan.md,tasks.md,...}` (source of truth)
- **OMO Execution**: read `tasks.md` only; do not mutate spec/plan/tasks directly

### Agent Mapping (自动分派)

Sisyphus 在执行 Spec‑Kit 命令时自动分派到专业 Agent：

| 命令 | 阶段 | 分派到 |
|------|------|--------|
| `/speckit.specify` | 澄清 | metis |
| `/speckit.plan` | 研究 | librarian |
| `/speckit.plan` | 架构 | oracle |
| `/speckit.plan` | 任务规划 | prometheus |
| `/speckit.plan` | 审查 | momus |
| `/speckit.plan` | 文档 | writing |
| `/speckit.tasks` | 分析 | momus |
| `/speckit.implement` | 前端 | visual-engineering |
| `/speckit.implement` | 复杂逻辑 | ultrabrain |

### 魔法命令 `/spec`

一键启动完整 Spec‑Kit 工作流：

```
/spec 我想在顶部 tab 栏添加一个小狗 icon
```

自动执行：`/speckit.specify` → `/speckit.plan` → `/speckit.tasks`

**调度脚本**: `.specify/scripts/bash/agent-dispatch.sh`

## Active Technologies
- Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI 0.100+, SQLAlchemy 2.0+ (async), Pydantic v2, React 18, Zustand 4 (001-agent-market-gateway)
- PostgreSQL 15+, Redis 7+ (for rate limiting/caching) (001-agent-market-gateway)

## Recent Changes
- 001-agent-market-gateway: Added Python 3.11+ (backend), TypeScript 5+ (frontend) + FastAPI 0.100+, SQLAlchemy 2.0+ (async), Pydantic v2, React 18, Zustand 4
