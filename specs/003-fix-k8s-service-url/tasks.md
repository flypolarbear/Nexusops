# Tasks: Fix K8s Service URL Access

**Input**: Design documents from `/specs/003-fix-k8s-service-url/`

## Path Conventions

- **Backend**: `backend/app/`
- **Tests**: `backend/tests/`

---

## Phase 1: Adapter Enhancement

**Goal**: Enhance `_format_service()` to include access URL info

- [ ] T001 [US1] Enhance `_format_service()` in backend/app/adapters/kubernetes.py to include `node_port` in ports array
- [ ] T002 [US1] Add `external_ips` field to service response for LoadBalancer type
- [ ] T003 [US1] Add `access_urls` computed array to service response
- [ ] T004 [US2] Add `get_service()` method to KubernetesAdapter for detailed service info
- [ ] T005 [US3] Add `list_ingresses()` method to KubernetesAdapter

**Checkpoint**: Adapter returns complete service access info

---

## Phase 2: Handler Enhancement

**Goal**: Add new tools and update formatting

- [ ] T006 [US1] Add `k8s_get_service` tool definition in backend/app/agents/k8s/handler.py
- [ ] T007 [US3] Add `k8s_list_ingresses` tool definition in backend/app/agents/k8s/handler.py
- [ ] T008 [US1] Add `_dispatch_tool` entries for new tools
- [ ] T009 [US1] Update `_format_success_summary()` to show access URLs for services
- [ ] T010 [US3] Add ingress formatting in `_format_success_summary()`

**Checkpoint**: Handler exposes new tools and formats output

---

## Phase 3: Tests

**Goal**: Ensure new functionality is tested

- [ ] T011 [P] [US1] Add unit test for enhanced `_format_service()` in backend/tests/unit/test_k8s_handler.py
- [ ] T012 [P] [US3] Add unit test for `list_ingresses()` in backend/tests/unit/test_k8s_handler.py
- [ ] T013 [US1] Run tests to verify changes

**Checkpoint**: All tests pass

---

## Dependencies

- Phase 2 depends on Phase 1 (handler needs adapter methods)
- Phase 3 depends on Phase 1 and 2 (tests need implementation)

## MVP Scope

**MVP = Phase 1 + Phase 2 (T001-T010)**

Core fix: Service response includes access URLs

## Parallel Opportunities

- T001, T002, T003 can be done together in adapter
- T011, T012 can run in parallel (different test files)
