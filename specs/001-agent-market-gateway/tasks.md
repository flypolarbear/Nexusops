# Tasks: Agent Market and Gateway

**Input**: Design documents from `/specs/001-agent-market-gateway/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are included for critical components (health monitoring, rate limiting, circuit breaker).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/`
- **Frontend**: `frontend/src/`
- **Tests**: `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create database migration for agent_health table in backend/app/models/database.py
- [ ] T002 Create database migration for invocations logging table in backend/app/models/database.py
- [ ] T003 [P] Create database migration for rate_limit_configs table in backend/app/models/database.py
- [ ] T004 [P] Add Redis connection configuration in backend/app/core/config.py
- [ ] T005 Create frontend agent components directory structure at frontend/src/components/agents/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create AgentHealth SQLAlchemy model in backend/app/models/database.py
- [ ] T007 Create InvocationLog SQLAlchemy model in backend/app/models/database.py
- [ ] T008 Create RateLimitConfig SQLAlchemy model in backend/app/models/database.py
- [ ] T009 [P] Create HealthStatus Pydantic schema in backend/app/models/schemas.py
- [ ] T010 [P] Create RateLimit Pydantic schema in backend/app/models/schemas.py
- [ ] T011 [P] Create CircuitState Pydantic schema in backend/app/models/schemas.py
- [ ] T012 Create AgentMarketStore Zustand store in frontend/src/stores/agentMarketStore.ts
- [ ] T013 [P] Create agentMarketService API client in frontend/src/services/agentMarketService.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Invoke Built-in Agents (Priority: P1) 🎯 MVP

**Goal**: DevOps engineers can invoke diagnostic agents through unified interface with health status visibility

**Independent Test**: Invoke each built-in agent via Gateway API, verify structured responses with trace IDs

### Tests for User Story 1

- [ ] T014 [P] [US1] Create test for health check service in backend/tests/unit/test_health_monitor.py
- [ ] T015 [P] [US1] Create integration test for agent invocation with health status in backend/tests/integration/test_agent_invoke_health.py

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create HealthMonitor service in backend/app/gateway/health.py
- [ ] T017 [US1] Implement health check loop with FastAPI lifespan in backend/app/gateway/health.py
- [ ] T018 [US1] Add health status endpoint to Agent Market API in backend/app/api/agent_market.py
- [ ] T019 [US1] Integrate health status into existing agent detail response in backend/app/api/agent_market.py
- [ ] T020 [US1] Update executor router to check health before routing in backend/app/gateway/executor/router.py
- [ ] T021 [US1] Add health status to invocation metadata in backend/app/gateway/response.py

**Checkpoint**: At this point, User Story 1 should be fully functional - agents can be invoked with health status visibility

---

## Phase 4: User Story 2 - Register and Invoke Third-party Agents (Priority: P1) 🎯 MVP

**Goal**: Platform engineers can register third-party agents with health monitoring and circuit breaker protection

**Independent Test**: Register a test agent via manifest, invoke it, verify circuit breaker protects on failures

### Tests for User Story 2

- [ ] T022 [P] [US2] Create test for circuit breaker in backend/tests/unit/test_circuit_breaker.py
- [ ] T023 [P] [US2] Create integration test for third-party agent registration and invocation in backend/tests/integration/test_third_party_agent.py

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create CircuitBreaker class in backend/app/gateway/circuit_breaker.py
- [ ] T025 [US2] Implement circuit breaker state machine (closed/open/half_open) in backend/app/gateway/circuit_breaker.py
- [ ] T026 [US2] Integrate circuit breaker into RemoteExecutor in backend/app/gateway/executor/remote.py
- [ ] T027 [US2] Add circuit breaker status to agent health endpoint in backend/app/api/agent_market.py
- [ ] T028 [US2] Create CIRCUIT_OPEN error response in backend/app/gateway/errors.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - MVP complete!

---

## Phase 5: User Story 3 - Discover and Install Agents from Store (Priority: P2)

**Goal**: Team leads can browse agents in a catalog, preview capabilities, and install for their team

**Independent Test**: Browse store, install an agent, verify it appears in installed list and is invokable

### Implementation for User Story 3

- [ ] T029 [P] [US3] Create AgentCard component in frontend/src/components/agents/AgentCard.tsx
- [ ] T030 [P] [US3] Create AgentDetail component in frontend/src/components/agents/AgentDetail.tsx
- [ ] T031 [P] [US3] Create AgentList component in frontend/src/components/agents/AgentList.tsx
- [ ] T032 [US3] Create AgentMarketPage in frontend/src/pages/AgentMarketPage.tsx
- [ ] T033 [US3] Add search functionality to agentMarketStore in frontend/src/stores/agentMarketStore.ts
- [ ] T034 [US3] Add install/uninstall actions to agentMarketStore in frontend/src/stores/agentMarketStore.ts
- [ ] T035 [US3] Add category filter UI to AgentMarketPage in frontend/src/pages/AgentMarketPage.tsx
- [ ] T036 [US3] Add agent route to React Router in frontend/src/App.tsx
- [ ] T037 [US3] Add navigation link to sidebar for Agent Market in frontend/src/components/layout/MainLayout.tsx

**Checkpoint**: Agent Store UI complete - users can discover and install agents

---

## Phase 6: User Story 4 - Manage Agent Versions and Health (Priority: P2)

**Goal**: Platform administrators can view agent health status and set default versions

**Independent Test**: View agent health dashboard, verify health issues are highlighted

### Implementation for User Story 4

- [ ] T038 [P] [US4] Create HealthStatusBadge component in frontend/src/components/agents/HealthStatusBadge.tsx
- [ ] T039 [US4] Add health dashboard section to AgentMarketPage in frontend/src/pages/AgentMarketPage.tsx
- [ ] T040 [US4] Create health status API endpoint for dashboard in backend/app/api/agent_market.py
- [ ] T041 [US4] Add default version selection to agent detail endpoint in backend/app/api/agent_market.py

**Checkpoint**: Health management features complete

---

## Phase 7: User Story 5 - Stream Agent Responses (Priority: P3)

**Goal**: DevOps engineers can receive streaming responses from long-running agents

**Independent Test**: Invoke streaming-capable agent, verify chunks received progressively

### Implementation for User Story 5

- [ ] T042 [P] [US5] Add streaming flag to InvokeRequest schema in backend/app/gateway/contract.py
- [ ] T043 [US5] Implement streaming response in WebSocket endpoint in backend/app/api/ws_endpoint.py
- [ ] T044 [US5] Add streaming UI component in frontend/src/components/agents/StreamingResponse.tsx
- [ ] T045 [US5] Handle stream chunks in chatStore in frontend/src/stores/chatStore.ts

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Create test for rate limiter in backend/tests/unit/test_rate_limiter.py
- [ ] T047 [P] Implement RateLimiter service in backend/app/gateway/rate_limiter.py
- [ ] T048 Integrate rate limiter into Gateway invoke endpoint in backend/app/api/agents.py
- [ ] T049 [P] Add rate limit headers to responses in backend/app/gateway/response.py
- [ ] T050 [P] Create frontend test for AgentMarketPage in frontend/tests/AgentMarket.test.tsx
- [ ] T051 Run quickstart.md validation scenarios
- [ ] T052 [P] Update API documentation with new endpoints
- [ ] T053 Add performance logging for agent invocations in backend/app/gateway/trace.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (both P1)
  - US3, US4, US5 depend on US1/US2 for backend stability
- **Polish (Phase 8)**: Depends on user stories being complete

### User Story Dependencies

- **US1 (Invoke Built-in)**: Can start after Foundational - No dependencies on other stories
- **US2 (Third-party Agents)**: Can start after Foundational - Independent of US1
- **US3 (Store UI)**: Can start after Foundational - Frontend only, uses existing backend
- **US4 (Health Management)**: Can start after US1 (needs health data)
- **US5 (Streaming)**: Can start after Foundational - Independent enhancement

### Within Each User Story

- Tests can run in parallel (marked [P])
- Implementation tasks run sequentially within the story
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks (T001-T005) can run in parallel
- All Foundational schema tasks (T009-T011, T013) can run in parallel
- US1 and US2 can be developed in parallel by different developers
- US3 frontend components (T029-T031) can run in parallel
- All Polish test tasks (T046, T050) can run in parallel

---

## Parallel Example: MVP (US1 + US2)

```bash
# Launch US1 health monitoring tasks in parallel:
Task: "T014 [P] [US1] Create test for health check service"
Task: "T015 [P] [US1] Create integration test"

# Launch US2 circuit breaker tasks in parallel:
Task: "T022 [P] [US2] Create test for circuit breaker"
Task: "T023 [P] [US2] Create integration test"

# After tests, implement sequentially within each story
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 - Health Monitoring
4. Complete Phase 4: US2 - Circuit Breaker
5. **STOP and VALIDATE**: Test agent invocation with health + circuit breaker
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 → Test independently → Deploy (MVP!)
3. Add US3 → Store UI available → Deploy
4. Add US4 → Health dashboard → Deploy
5. Add US5 → Streaming support → Deploy
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Health Monitoring)
   - Developer B: US2 (Circuit Breaker)
   - Developer C: US3 (Store UI - frontend only)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
