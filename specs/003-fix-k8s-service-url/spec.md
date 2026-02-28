# Feature Specification: Fix K8s Service URL Access

**Feature Branch**: `003-fix-k8s-service-url`
**Created**: 2026-03-01
**Status**: Draft
**Input**: "Kubernetes Agent 无法通过对话查询服务的访问 URL 帮我修复这个问题"

## Problem Analysis

### Current Behavior
The `k8s_list_services` tool returns only:
- `name`, `namespace`, `type`, `cluster_ip`, `ports`, `age`

### What's Missing
1. **NodePort services**: Missing `node_port` in ports array
2. **LoadBalancer services**: Missing `external_ips` and `loadbalancer_ip`
3. **Ingress endpoints**: No ingress query capability
4. **Access URL generation**: No computed access URLs for different service types

### Root Cause
`backend/app/adapters/kubernetes.py` - `_format_service()` method only returns basic service info without access URLs.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Service Access URL (Priority: P1)

As a DevOps engineer, I want to ask "What's the access URL for my-api service?" and get a clear answer with all possible access methods.

**Why this priority**: Core functionality gap - users cannot discover how to access their services.

**Independent Test**: 
1. Deploy a NodePort service
2. Query via K8s Agent: "What's the URL for my-api service?"
3. Verify response includes `http://<node-ip>:<node-port>`

**Acceptance Scenarios**:

1. **Given** a NodePort service named "my-api", **When** I ask "What's the access URL for my-api?", **Then** I receive `http://<node-ip>:<node-port>` format URL
2. **Given** a LoadBalancer service with external IP, **When** I query the service, **Then** I see the external IP and port
3. **Given** a ClusterIP service, **When** I query the service, **Then** I see it's only accessible within cluster with cluster IP
4. **Given** an Ingress pointing to a service, **When** I query the service, **Then** I see the ingress URL

---

### User Story 2 - List All Services with Access Info (Priority: P1)

As a DevOps engineer, I want to list all services in a namespace and see their access URLs at a glance.

**Independent Test**: List services in a namespace with multiple service types, verify each shows appropriate access URL.

**Acceptance Scenarios**:

1. **Given** services of types NodePort, LoadBalancer, ClusterIP, **When** I run "list services", **Then** each service shows its access URL or indicates internal-only access

---

### User Story 3 - Query Ingress Endpoints (Priority: P2)

As a DevOps engineer, I want to query ingress resources to find HTTP(S) access URLs for my services.

**Independent Test**: Deploy an Ingress, query via K8s Agent, verify response includes host and path.

**Acceptance Scenarios**:

1. **Given** an Ingress resource, **When** I query "list ingresses", **Then** I see host, paths, and backend services
2. **Given** a service with Ingress, **When** I query the service, **Then** I see related Ingress URLs

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `k8s_list_services` MUST return `node_port` for each port in NodePort services
- **FR-002**: `k8s_list_services` MUST return `external_ips` for LoadBalancer services
- **FR-003**: `k8s_list_services` MUST return `loadbalancer_ip` when available
- **FR-004**: Add `k8s_list_ingresses` tool to query Ingress resources
- **FR-005**: Add `k8s_get_service` tool for detailed service info including access URLs
- **FR-006**: Service response MUST include computed `access_urls` array with formatted URLs
- **FR-007**: Handler MUST format service results to show access URLs clearly

### Key Entities

- **ServiceAccessInfo**: Extended service info with node_port, external_ips, access_urls
- **IngressInfo**: Ingress resource with host, paths, backend service mapping
- **AccessURL**: Formatted URL string with protocol, host/IP, port, path

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: NodePort service query returns `http://<node-ip>:<node-port>` format URL
- **SC-002**: LoadBalancer service query returns external IP with port
- **SC-003**: ClusterIP service query clearly indicates internal-only access
- **SC-004**: Ingress query returns host, paths, and TLS info
- **SC-005**: Service list shows access info for all service types

## Implementation Scope

### Files to Modify

1. `backend/app/adapters/kubernetes.py`
   - Enhance `_format_service()` to include node_port, external_ips
   - Add `_format_service_detail()` for detailed service info
   - Add `list_ingresses()` method
   - Add `get_service()` method

2. `backend/app/agents/k8s/handler.py`
   - Add `k8s_list_ingresses` tool
   - Add `k8s_get_service` tool
   - Update `_format_success_summary()` to show access URLs

## Assumptions

- Kubernetes API access is already configured
- Node IPs can be obtained from Kubernetes nodes API
- Ingress resources follow standard k8s networking.k8s.io/v1 API

## Out of Scope

- Service mesh (Istio, Linkerd) URL discovery
- Custom ingress controllers (only standard k8s ingress)
- DNS-based service discovery
