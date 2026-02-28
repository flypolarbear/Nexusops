<!--
============================================================================
SYNC IMPACT REPORT
============================================================================
Version change: Template → 1.0.0
Modified principles: N/A (initial creation)
Added sections: All (7 Core Principles, Tech Stack, Development Workflow, Governance)
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - Constitution Check section verified compatible
  ✅ spec-template.md - Requirements alignment verified
  ✅ tasks-template.md - Task categorization verified compatible
Follow-up TODOs: None
============================================================================
-->

# NexusOps Constitution

## Core Principles

### I. API-First Design

Every feature MUST expose well-defined REST or WebSocket APIs with complete OpenAPI specifications.

- All endpoints MUST be documented with request/response schemas
- API contracts MUST be defined before implementation begins
- Breaking changes require version increment and migration plan
- WebSocket events follow the same documentation standards as REST APIs

**Rationale**: API-first ensures consistent interfaces between frontend, backend, and third-party integrations. OpenAPI specs enable automatic client generation and contract testing.

### II. Async-First Architecture

All I/O operations MUST use async/await patterns throughout the stack.

- Backend: FastAPI async handlers, SQLAlchemy async sessions
- Frontend: Async data fetching with TanStack Query
- External integrations: Async HTTP clients (httpx, aiohttp)
- Database operations: Never block the event loop

**Rationale**: Async patterns enable efficient handling of concurrent requests and external service calls, critical for an operations platform managing multiple integrations.

### III. Type Safety (NON-NEGOTIABLE)

Strict typing MUST be enforced at all layers with zero type errors.

- Backend: Pydantic v2 for all data models, mypy strict mode
- Frontend: TypeScript strict mode, no `any` types, no `@ts-ignore`
- API contracts: Typed request/response schemas shared between frontend and backend
- Runtime validation: Pydantic validation on all API inputs

**Rationale**: Type safety catches bugs at compile time, improves IDE support, and serves as executable documentation. Zero tolerance prevents type debt accumulation.

### IV. Contract-Based Agent Interface

All agents MUST communicate via unified request/response contracts defined in the Gateway specification.

- Request schema: `request_id`, `agent_id`, `query`, `context`, `auth_context`
- Response schema: `status`, `content`, `structured_output`, `error`, `metadata`
- Built-in and third-party agents use identical contract formats
- Contract changes require Gateway version update

**Rationale**: Unified contracts enable consistent agent invocation, observability, and allow seamless integration of third-party agents without platform changes.

### V. Test Coverage

Unit tests MUST exist for all services; integration tests MUST exist for external integrations.

- Unit tests: pytest for backend, Vitest for frontend
- Integration tests: Required for Jenkins, ArgoCD, DNS providers, cloud services
- Contract tests: Validate agent request/response schemas
- Coverage target: 70% minimum for new features

**Rationale**: Operations platforms cannot afford regressions. Tests provide confidence for refactoring and ensure integrations remain functional.

### VI. Component-Based Frontend

Frontend MUST use React functional components with hooks; Zustand for global state.

- No class components
- Custom hooks for reusable logic
- Zustand stores for cross-component state
- Ant Design components with Tailwind CSS for styling
- Component file structure: `ComponentName.tsx` with co-located styles

**Rationale**: Functional components with hooks provide cleaner code, better testability, and consistent patterns across the team. Zustand offers simple, type-safe state management.

### VII. Infrastructure as Code

All infrastructure MUST be defined declaratively and version-controlled.

- Local development: Docker Compose for all services
- Production: Kubernetes manifests, ArgoCD for GitOps deployments
- Database: Migration scripts in version control
- Secrets: Environment variables, never committed to repo

**Rationale**: IaC enables reproducible environments, disaster recovery, and eliminates "works on my machine" issues. GitOps provides audit trail and rollback capabilities.

## Tech Stack Constraints

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ (async) |
| Validation | Pydantic | 2.0+ |
| Database | PostgreSQL | 15+ |
| Cache | Redis | 7+ |
| Testing | pytest | 7+ |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18+ |
| Language | TypeScript | 5+ |
| Build | Vite | 5+ |
| UI Library | Ant Design | 5+ |
| Styling | Tailwind CSS | 3+ |
| State | Zustand | 4+ |
| Data Fetching | TanStack Query | 5+ |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Container Runtime | Docker |
| Orchestration | Kubernetes |
| GitOps | ArgoCD |
| CI/CD | Jenkins |
| Registry | Harbor |
| Monitoring | Prometheus + Grafana |

## Development Workflow

### Code Quality Gates

1. **Pre-commit**: Linting (ruff, ESLint), formatting (Black, Prettier)
2. **Type Check**: mypy (backend), tsc (frontend) - zero errors required
3. **Tests**: Unit tests must pass, coverage >= 70%
4. **Review**: At least one approval required for merge

### Branch Strategy

- `master`: Production-ready code
- `feat/###-feature-name`: Feature branches from spec-kit workflow
- `fix/###-bug-name`: Bug fix branches
- Direct commits to master prohibited

### Commit Convention

```
<type>(<scope>): <description> [<task-id>]

type: feat|fix|refactor|docs|test|chore
```

### File Organization

```
backend/
├── app/
│   ├── api/           # Route handlers
│   ├── core/          # Config, database
│   ├── gateway/       # Agent gateway contracts
│   ├── llm/           # LLM integrations
│   ├── models/        # SQLAlchemy models
│   ├── services/      # Business logic
│   └── stores/        # Data stores
└── tests/

frontend/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   ├── stores/        # Zustand stores
│   ├── services/      # API services
│   ├── hooks/         # Custom hooks
│   └── types/         # TypeScript types
└── tests/
```

## Governance

### Amendment Process

1. Propose amendment via pull request to constitution.md
2. Document rationale and impact on existing code
3. Require team review and approval
4. Update version number per semantic versioning:
   - MAJOR: Backward incompatible principle changes
   - MINOR: New principles or expanded guidance
   - PATCH: Clarifications and typo fixes

### Compliance

- All pull requests must verify compliance with constitution principles
- Constitution supersedes conflicting practices
- Complexity beyond defined patterns must be justified in plan.md

### Guidance Files

- **AGENTS.md**: Entry point for AI coding agents (OpenCode)
- **README.md**: Project overview and quick start
- **.specify/memory/constitution.md**: This document (highest authority)

---

**Version**: 1.0.0 | **Ratified**: 2026-03-01 | **Last Amended**: 2026-03-01
