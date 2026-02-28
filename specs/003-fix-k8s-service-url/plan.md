# Implementation Plan: Fix K8s Service URL Access

**Branch**: `003-fix-k8s-service-url` | **Date**: 2026-03-01 | **Spec**: [spec.md](./spec.md)

## Summary

Enhance Kubernetes Agent to return service access URLs. Fix the `_format_service()` method to include NodePort, LoadBalancer external IPs, and add Ingress query capability.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: kubernetes-client, FastAPI, Pydantic v2
**Storage**: N/A (Kubernetes API)
**Testing**: pytest
**Target Platform**: Kubernetes clusters
**Project Type**: backend-service

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. API-First Design | ✅ PASS | Extending existing K8s agent tools |
| II. Async-First Architecture | ✅ PASS | All K8s API calls are async |
| III. Type Safety | ✅ PASS | Pydantic models for all responses |
| V. Test Coverage | ⚠️ PARTIAL | Need tests for new tools |

**Gate Result**: PASS

## Project Structure

```text
backend/app/
├── adapters/
│   └── kubernetes.py       # ⚠️ MODIFY - Enhance _format_service(), add methods
└── agents/k8s/
    └── handler.py          # ⚠️ MODIFY - Add tools, update formatting

backend/tests/
├── unit/
│   └── test_k8s_handler.py  # ⚠️ MODIFY - Add tests for new tools
└── integration/
    └── test_k8s_real.py     # ⚠️ MODIFY - Add integration tests
```

## Implementation Approach

### What Exists

1. `k8s_list_services` tool - returns basic service info
2. `KubernetesAdapter` class with async K8s API access
3. Service formatting in `_format_service()`

### What Needs Implementation

1. **Enhance `_format_service()`**:
   - Add `node_port` to ports array
   - Add `external_ips` for LoadBalancer
   - Add `loadbalancer_hostname` if available
   - Add `access_urls` computed array

2. **Add `k8s_get_service` tool**:
   - Detailed service info
   - All access methods

3. **Add `k8s_list_ingresses` tool**:
   - Query Ingress resources
   - Map to backend services

4. **Update handler formatting**:
   - Show access URLs in service list summary
