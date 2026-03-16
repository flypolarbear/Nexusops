# Spec: MK-009 - Built-in Agent Capability Acceptance

## 1. Summary

验收 NexusOps 内置 Agent 能力达到可调用、可诊断、可回滚的生产就绪标准。本规范定义 7 类核心内置 Agent 的功能边界、接口契约、工具定义和验收标准。

**前置依赖:**
- MK-006: Gateway 调用契约与错误模型 (已完成)
- MK-007: Gateway 插件执行边界 (已完成)
- MK-008: 第三方 Agent 闭环 (已完成)

---

## 2. Goals

1. 定义 7 类内置 Agent 的功能边界与能力清单
2. 标准化每个 Agent 的输入/输出契约
3. 确保每个 Agent 可通过 Gateway 调用
4. 确保每个 Agent 可诊断（trace_id、错误详情、执行日志）
5. 确保可回滚的操作有回滚能力或确认机制

## 3. Non-Goals

1. 不实现 Agent 的 AI/LLM 能力（当前为规则引擎实现）
2. 不定义 Agent 的计费模型
3. 不实现 Agent 的热更新机制
4. 不实现流式响应（SSE/WebSocket）

---

## 4. Agent 清单

### 4.1 Agent 概览

| Agent ID | Name | Category | Description |
|----------|------|----------|-------------|
| `nexusops.k8s` | K8s Agent | Infrastructure | Kubernetes 资源状态检索、诊断 |
| `nexusops.deploy` | Deploy Agent | Deployment | 部署流程编排、ArgoCD 操作 |
| `nexusops.logs` | Logs Agent | Observability | 日志查询、过滤、分析 |
| `nexusops.cost` | Cost Agent | FinOps | 云资源成本分析、预算管理 |
| `nexusops.dns` | DNS Agent | Infrastructure | DNS 记录管理、域名生成 |
| `nexusops.cicd` | CI/CD Agent | Deployment | CI/CD 流水线操作 |
| `nexusops.git` | Git Agent | Source Control | Git 仓库操作、版本管理 |

### 4.2 Agent 能力矩阵

```
              调用  诊断  回滚  确认  危险操作
nexusops.k8s   Y     Y     N     N     N
nexusops.deploy Y    Y     Y     Y     Y
nexusops.logs   Y    Y     N     N     N
nexusops.cost   Y    Y     N     N     N
nexusops.dns    Y    Y     Y     Y     Y
nexusops.cicd   Y    Y     Y     Y     Y
nexusops.git    Y    Y     Y     Y     Y
```

**图例:**
- **调用 (Invoke)**: 可通过 Gateway API 调用
- **诊断 (Diagnose)**: 可获取 trace_id、错误详情、执行日志
- **回滚 (Rollback)**: 操作可回滚
- **确认 (Confirm)**: 需要用户确认后执行
- **危险操作 (Danger)**: 可能造成数据丢失或服务中断

---

## 5. 接口规范

### 5.1 通用响应结构

所有 Agent 响应必须遵循 MK-006 定义的 `ExecutorResult` 结构:

```python
class ExecutorResult(BaseModel):
    success: bool                              # 执行是否成功
    content: Dict[str, Any]                    # 响应内容 {text, format, data}
    structured_output: Optional[Any] = None    # 结构化输出
    suggested_actions: List[Dict] = []         # 建议操作
    related_resources: List[Dict] = []         # 关联资源
    tool_calls: Optional[List[Dict]] = None    # 工具调用记录
    metadata: Dict[str, Any] = {}              # 元数据
    error: Optional[Dict[str, Any]] = None     # 错误详情
```

### 5.2 Agent 详细规范

---

#### 5.2.1 nexusops.k8s - K8s 状态检索 Agent

**功能:**
- Kubernetes 资源状态查询
- Pod/Deployment/Service 诊断
- 日志获取
- 资源扩缩容

**Capabilities:**
```python
["k8s_deploy", "k8s_scale", "k8s_logs", "k8s_describe", "k8s_diagnose"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["status", "logs", "describe", "scale", "diagnose"]
    },
    "resource_type": {"type": "string", "description": "Pod, Deployment, Service, etc."},
    "resource_name": {"type": "string"},
    "namespace": {"type": "string", "default": "default"},
    "tail_lines": {"type": "integer", "default": 100},
    "replicas": {"type": "integer", "description": "Target replicas for scale"}
  }
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {"type": "string"},
    "resource_type": {"type": "string"},
    "resource_name": {"type": "string"},
    "namespace": {"type": "string"},
    "status": {"type": "string", "enum": ["running", "pending", "failed", "unknown"]},
    "health": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
    "logs": {"type": "array", "items": {"type": "string"}},
    "issues": {"type": "array", "items": {"type": "object"}}
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level |
|-----------|-------------|------------|
| `get_pod_logs` | Get logs from a pod | Low |
| `describe_resource` | Describe a Kubernetes resource | Low |
| `scale_deployment` | Scale a deployment | Medium |
| `diagnose_resource` | Run diagnostics on a resource | Low |

**Suggested Actions:**
- View full logs
- View resource details
- Diagnose resource

---

#### 5.2.2 nexusops.deploy - Manifest 生成与部署 Agent

**功能:**
- 部署流程编排
- ArgoCD 同步操作
- 部署回滚
- 多区域部署状态

**Capabilities:**
```python
["deploy_create", "deploy_rollback", "deploy_status", "deploy_force_sync"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["deploy", "rollback", "status", "sync"]
    },
    "version_id": {"type": "string", "description": "Version/codename to deploy"},
    "regions": {"type": "array", "items": {"type": "string"}},
    "target_revision": {"type": "string", "description": "Git revision for rollback"}
  },
  "required": ["operation"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["deployment_result", "rollback_result", "deployment_status", "sync_result"]},
    "codename": {"type": "string"},
    "status": {"type": "string", "enum": ["success", "in_progress", "failed", "rolled_back"]},
    "regions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "status": {"type": "string"},
          "health": {"type": "string"},
          "replicas": {"type": "string"}
        }
      }
    },
    "services": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "status": {"type": "string"},
          "health": {"type": "string"}
        }
      }
    }
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level | Confirm Required |
|-----------|-------------|------------|------------------|
| `create_deployment` | Create a new deployment | High | Yes |
| `rollback_deployment` | Rollback a deployment | High | Yes |
| `force_sync` | Force sync ArgoCD application | Medium | Yes |
| `get_deployment_status` | Get deployment status | Low | No |

**Suggested Actions:**
- View deployment status
- View logs
- Confirm rollback (with danger flag)
- Force sync

**Rollback Support:**
- 支持 `rollback` 操作
- 回滚前显示目标版本信息
- 需要 `confirm_required: true`

---

#### 5.2.3 nexusops.logs - 日志查询 Agent

**功能:**
- 日志查询与过滤
- 按级别/服务/时间范围过滤
- 关键词搜索
- 日志统计

**Capabilities:**
```python
["query_logs", "search_errors", "tail_logs", "filter_by_level", "filter_by_service", "search_keywords", "time_range"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "service": {"type": "string", "description": "Filter by service name"},
    "level": {"type": "string", "enum": ["ERROR", "WARN", "INFO", "DEBUG"]},
    "keyword": {"type": "string", "description": "Search keyword"},
    "from_time": {"type": "string", "description": "Start time (ISO or relative)"},
    "to_time": {"type": "string", "description": "End time (ISO or relative)"},
    "limit": {"type": "integer", "default": 100}
  }
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["log_query_result", "log_level_result", "search_result", "time_range_result"]},
    "total_count": {"type": "integer"},
    "logs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": {"type": "string"},
          "level": {"type": "string"},
          "service": {"type": "string"},
          "message": {"type": "string"},
          "metadata": {"type": "object"}
        }
      }
    },
    "filters": {"type": "object"},
    "time_range": {"type": "object"}
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level |
|-----------|-------------|------------|
| `query_logs` | Query logs with optional filters | Low |
| `search_logs` | Full-text search across logs | Low |
| `get_log_stats` | Get log statistics | Low |

**Suggested Actions:**
- Filter by error level
- Search by keyword
- Expand time range
- Follow logs (tail)

---

#### 5.2.4 nexusops.cost - 成本计算 Agent

**功能:**
- 云资源成本概览
- 按服务/区域分摊
- 成本趋势分析
- 预算对比与告警
- 优化建议

**Capabilities:**
```python
["cost_query", "cost_by_service", "cost_by_region", "cost_trend_analysis", "budget_comparison", "budget_alert", "cost_optimization", "resource_utilization"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["overview", "by_service", "by_region", "trend", "budget", "optimization", "utilization"]
    },
    "period": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "monthly"},
    "services": {"type": "array", "items": {"type": "string"}},
    "regions": {"type": "array", "items": {"type": "string"}},
    "period_days": {"type": "integer", "default": 30}
  }
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["cost_overview", "cost_by_service", "cost_by_region", "cost_trend", "budget_comparison", "cost_optimization", "resource_utilization"]},
    "data": {
      "type": "object",
      "properties": {
        "total_cost": {"type": "number"},
        "budget": {"type": "number"},
        "usage_percentage": {"type": "number"},
        "by_service": {"type": "object"},
        "by_region": {"type": "object"},
        "trend": {"type": "array"},
        "optimization_tips": {"type": "array"}
      }
    }
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level |
|-----------|-------------|------------|
| `get_cost_overview` | Get overall cost summary | Low |
| `get_cost_by_service` | Get cost by service | Low |
| `get_cost_by_region` | Get cost by region | Low |
| `get_cost_trend` | Get cost trend analysis | Low |
| `get_budget_status` | Get budget comparison | Low |
| `get_optimization_suggestions` | Get optimization tips | Low |
| `get_resource_utilization` | Get utilization analysis | Low |

**Suggested Actions:**
- View cost trend
- View optimization suggestions
- Check resource utilization
- Set budget alert

---

#### 5.2.5 nexusops.dns - DNS Agent

**功能:**
- DNS 记录管理 (CRUD)
- 随机域名生成
- DNS 状态查询

**Capabilities:**
```python
["dns_record_create", "dns_record_delete", "dns_record_query", "random_domain_generate"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["create", "delete", "query", "generate", "status"]
    },
    "zone_id": {"type": "string", "description": "DNS zone identifier"},
    "record_type": {"type": "string", "enum": ["A", "AAAA", "CNAME", "MX", "TXT"]},
    "record_name": {"type": "string"},
    "content": {"type": "string", "description": "Record value"},
    "base_domain": {"type": "string", "description": "For generate operation"},
    "levels": {"type": "integer", "default": 4, "description": "Subdomain levels for generate"}
  }
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["dns_record_created", "dns_record_deleted", "dns_query_result", "random_domain"]},
    "zone": {"type": "string"},
    "record_name": {"type": "string"},
    "record_type": {"type": "string"},
    "records": {"type": "array"},
    "full_domain": {"type": "string", "description": "For generate operation"},
    "status": {"type": "string", "enum": ["created", "deleted", "active"]}
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level | Confirm Required |
|-----------|-------------|------------|------------------|
| `create_dns_record` | Create a DNS record | Medium | No |
| `delete_dns_record` | Delete a DNS record | High | Yes |
| `query_dns_record` | Query DNS records | Low | No |
| `generate_random_subdomain` | Generate random subdomain | Low | No |

**Suggested Actions:**
- Create DNS record
- Query DNS records
- View DNS status

**Rollback Support:**
- 删除操作可重新创建记录（需记录原始值）
- `delete` 操作需要 `confirm_required: true`

---

#### 5.2.6 nexusops.cicd - CI/CD Agent

**功能:**
- CI/CD 流水线触发
- 流水线状态查询
- 流水线取消
- 构建日志获取

**Capabilities:**
```python
["pipeline_trigger", "pipeline_status", "pipeline_cancel", "build_logs", "pipeline_list"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["trigger", "status", "cancel", "logs", "list"]
    },
    "pipeline_id": {"type": "string"},
    "branch": {"type": "string", "default": "main"},
    "parameters": {"type": "object", "description": "Pipeline parameters"},
    "build_id": {"type": "string"}
  },
  "required": ["operation"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["pipeline_triggered", "pipeline_status", "pipeline_cancelled", "build_logs", "pipeline_list"]},
    "pipeline_id": {"type": "string"},
    "build_id": {"type": "string"},
    "status": {"type": "string", "enum": ["pending", "running", "success", "failed", "cancelled"]},
    "logs": {"type": "array", "items": {"type": "string"}},
    "pipelines": {"type": "array"}
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level | Confirm Required |
|-----------|-------------|------------|------------------|
| `trigger_pipeline` | Trigger a pipeline | Medium | No |
| `get_pipeline_status` | Get pipeline status | Low | No |
| `cancel_pipeline` | Cancel a running pipeline | High | Yes |
| `get_build_logs` | Get build logs | Low | No |
| `list_pipelines` | List available pipelines | Low | No |

**Suggested Actions:**
- View pipeline status
- View build logs
- Cancel pipeline (with danger flag)
- Retry failed build

**Rollback Support:**
- 支持重新触发历史构建
- `cancel` 操作需要 `confirm_required: true`

---

#### 5.2.7 nexusops.git - Git 管理 Agent

**功能:**
- 仓库状态查询
- 分支操作
- Tag 管理
- PR/MR 操作

**Capabilities:**
```python
["git_status", "git_branch", "git_tag", "git_pr", "git_diff"]
```

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["status", "branch", "tag", "pr", "diff", "commit"]
    },
    "repo": {"type": "string", "description": "Repository path or URL"},
    "branch": {"type": "string"},
    "tag": {"type": "string"},
    "commit_sha": {"type": "string"},
    "base_branch": {"type": "string", "default": "main"},
    "head_branch": {"type": "string"}
  },
  "required": ["operation"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "type": {"type": "string", "enum": ["git_status", "branch_info", "tag_info", "pr_info", "diff_result", "commit_info"]},
    "repo": {"type": "string"},
    "current_branch": {"type": "string"},
    "branches": {"type": "array"},
    "tags": {"type": "array"},
    "status": {"type": "string"},
    "diff": {"type": "string"},
    "commits": {"type": "array"}
  }
}
```

**Tools:**

| Tool Name | Description | Risk Level | Confirm Required |
|-----------|-------------|------------|------------------|
| `get_repo_status` | Get repository status | Low | No |
| `list_branches` | List branches | Low | No |
| `create_branch` | Create a new branch | Low | No |
| `delete_branch` | Delete a branch | Medium | Yes |
| `create_tag` | Create a tag | Low | No |
| `delete_tag` | Delete a tag | Medium | Yes |
| `get_diff` | Get diff between branches | Low | No |

**Suggested Actions:**
- View branch list
- Create new branch
- View diff
- Create PR

**Rollback Support:**
- 分支/Tag 删除可通过重新创建恢复
- `delete_branch` 和 `delete_tag` 需要 `confirm_required: true`

---

## 6. 工具定义规范

### 6.1 Tool Schema 格式

所有 Agent 的工具定义必须遵循以下格式:

```json
{
  "name": "tool_name",
  "description": "Human-readable description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {"type": "string", "description": "Parameter description"},
      "param2": {"type": "integer", "default": 100}
    },
    "required": ["param1"]
  }
}
```

### 6.2 风险等级定义

| Risk Level | Description | Examples |
|------------|-------------|----------|
| **Low** | 只读操作，无副作用 | 查询状态、获取日志 |
| **Medium** | 可逆操作，影响有限 | 扩缩容、创建资源 |
| **High** | 不可逆或影响重大 | 删除资源、回滚部署 |

### 6.3 确认机制

高风险操作必须设置 `confirm_required: true`:

```python
self._action(
    "delete-resource",
    "invoke",
    "Delete Resource",
    {"agent_id": "nexusops.k8s", "query": "delete pod xxx"},
    confirm_required=True,
    danger=True
)
```

---

## 7. 验收标准

### 7.1 可调用 (Invoke)

| Criteria | Description | Verification |
|----------|-------------|--------------|
| **INV-001** | 所有 Agent 注册到 BuiltinExecutor | `router.list_agents()` 包含 7 个 Agent |
| **INV-002** | 每个 Agent 可通过 Gateway API 调用 | POST /api/v1/agents/{agent_id}/invoke 返回 200 |
| **INV-003** | 请求遵循 MK-006 Request Schema | JSON Schema 校验通过 |
| **INV-004** | 响应遵循 MK-006 Response Schema | JSON Schema 校验通过 |
| **INV-005** | 每个 Agent 返回正确的 agent_id | 响应中 agent_id 与请求一致 |

### 7.2 可诊断 (Diagnose)

| Criteria | Description | Verification |
|----------|-------------|--------------|
| **DIAG-001** | 每次调用生成唯一 trace_id | 响应 Header 包含 X-Trace-ID |
| **DIAG-002** | trace_id 贯穿整个调用链 | 日志中同一 trace_id 关联所有步骤 |
| **DIAG-003** | 错误返回详细 ErrorDetail | error.code + error.message + error.details |
| **DIAG-004** | 执行时间记录在 metadata | metadata.latency_ms 存在 |
| **DIAG-005** | 工具调用记录在 tool_calls | 每个 tool_call 包含 input/output/status |

### 7.3 可回滚 (Rollback)

| Criteria | Description | Verification |
|----------|-------------|--------------|
| **RB-001** | 危险操作标记 danger=true | suggested_actions.danger = true |
| **RB-002** | 危险操作需要确认 | suggested_actions.confirm_required = true |
| **RB-003** | 回滚操作可用 | deploy/dns/cicd/git 支持 rollback |
| **RB-004** | 回滚操作有确认提示 | 回滚前显示目标状态 |
| **RB-005** | 删除操作记录原始值 | 删除前记录可恢复信息 |

---

## 8. 测试用例

### 8.1 P0 用例 (必须 100% 通过)

| ID | Agent | Test Case | Expected Result |
|----|-------|-----------|-----------------|
| **BA-001** | All | 调用所有 Agent | status=success |
| **BA-002** | All | 每个响应包含 trace_id | trace_id 存在且为 32 位 hex |
| **BA-003** | All | 不存在的 Agent 调用 | status=error, code=AGENT_NOT_FOUND |
| **BA-004** | k8s | 查询 K8s 状态 | 返回资源状态结构化数据 |
| **BA-005** | k8s | 获取 Pod 日志 | 返回日志列表 |
| **BA-006** | deploy | 触发部署 | 返回部署状态，包含 regions 数组 |
| **BA-007** | deploy | 执行回滚 | confirm_required=true, danger=true |
| **BA-008** | logs | 查询日志 | 返回 logs 数组 |
| **BA-009** | logs | 按 ERROR 级别过滤 | 只返回 ERROR 级别日志 |
| **BA-010** | cost | 获取成本概览 | 返回 total_cost, by_service, by_region |
| **BA-011** | cost | 获取优化建议 | 返回 optimization_tips 数组 |
| **BA-012** | dns | 创建 DNS 记录 | 返回 status=created |
| **BA-013** | dns | 删除 DNS 记录 | confirm_required=true |
| **BA-014** | dns | 生成随机域名 | 返回 full_domain |
| **BA-015** | cicd | 触发流水线 | 返回 pipeline_id, build_id |
| **BA-016** | cicd | 取消流水线 | confirm_required=true, danger=true |
| **BA-017** | git | 获取仓库状态 | 返回 current_branch, status |
| **BA-018** | git | 删除分支 | confirm_required=true |

### 8.2 P1 用例 (通过率 >= 95%)

| ID | Agent | Test Case | Expected Result |
|----|-------|-----------|-----------------|
| **BA-101** | All | 错误响应包含 doc_url | doc_url 指向错误文档 |
| **BA-102** | k8s | 扩缩容操作 | 返回新副本数 |
| **BA-103** | deploy | 多区域部署 | regions 数组包含多个区域 |
| **BA-104** | logs | 时间范围过滤 | 只返回指定时间范围日志 |
| **BA-105** | logs | 关键词搜索 | 返回匹配日志 |
| **BA-106** | cost | 趋势分析 | 返回 30 天趋势数据 |
| **BA-107** | cost | 预算告警 | 超预算时返回 alert_level=warning |
| **BA-108** | dns | 查询 DNS 记录 | 返回 records 数组 |
| **BA-109** | cicd | 获取构建日志 | 返回 logs 数组 |
| **BA-110** | git | 获取 diff | 返回 diff 内容 |
| **BA-111** | All | suggested_actions 有效 | action 可点击触发 |
| **BA-112** | All | related_resources 有效 | resource 链接可访问 |

### 8.3 诊断测试

```python
# tests/agents/test_diagnostics.py

async def test_trace_id_propagation():
    """验证 trace_id 贯穿调用链"""
    trace_id = generate_trace_id()

    # 调用 Agent
    result = await router.route_and_execute(
        agent_id="nexusops.k8s",
        trace_id=trace_id,
        request_id="req-001",
        query="status",
        request_context={}
    )

    # 验证日志中 trace_id 一致
    logs = get_logs_by_trace_id(trace_id)
    assert all(log["trace_id"] == trace_id for log in logs)

async def test_error_detail_structure():
    """验证错误详情结构"""
    result = await invoke_agent("invalid.agent", "test")

    assert result["status"] == "error"
    assert "error" in result
    assert "code" in result["error"]
    assert "message" in result["error"]
    assert len(result["error"]["code"]) >= 3
```

---

## 9. 目录结构

```
backend/app/
├── agents/                   # 内置 Agent 实现
│   ├── __init__.py           # 导出所有 Handler
│   ├── base.py               # BaseAgentHandler
│   ├── chat.py               # nexusops.chat
│   ├── k8s.py                # nexusops.k8s
│   ├── deploy.py             # nexusops.deploy
│   ├── logs.py               # nexusops.logs
│   ├── cost.py               # nexusops.cost
│   ├── dns.py                # nexusops.dns
│   ├── cicd.py               # nexusops.cicd (待实现)
│   └── git.py                # nexusops.git (待实现)
├── gateway/
│   ├── contract.py           # MK-006: 契约定义
│   ├── errors.py             # MK-006: 错误码
│   ├── trace.py              # MK-006: Trace 处理
│   └── executor/
│       ├── base.py           # BaseExecutor
│       ├── builtin.py        # BuiltinExecutor
│       ├── remote.py         # RemoteExecutor
│       └── router.py         # ExecutorRouter
└── api/
    └── agents.py             # API 端点
```

---

## 10. 实施约束

1. **禁止**在 Agent Handler 中直接调用外部 API（需通过工具层）
2. **必须**所有 Agent 继承 `BaseAgentHandler`
3. **必须**所有 Agent 通过 `BuiltinExecutor` 注册
4. **必须**危险操作设置 `confirm_required: true` 和 `danger: true`
5. **必须**每个 Agent 定义 `get_tools()` 返回工具清单

---

## 11. Rollback Plan

1. Agent 实现可独立回滚，不影响 Gateway 层
2. 新增 Agent 不影响已有 Agent 功能
3. 工具变更需保持向后兼容
4. 通过特性开关控制新 Agent 上线

---

## 12. 里程碑检查点

| Checkpoint | Description | Status |
|------------|-------------|--------|
| **CP-001** | 7 个 Agent 全部注册到 BuiltinExecutor | Pending |
| **CP-002** | 所有 P0 测试通过 | Pending |
| **CP-003** | 诊断能力验证 (trace_id 贯穿) | Pending |
| **CP-004** | 危险操作确认机制验证 | Pending |
| **CP-005** | 文档更新完成 | Pending |

---

## 13. Appendix

### 13.1 错误码映射

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `AGENT_NOT_FOUND` | 404 | Agent 不存在 |
| `AGENT_INACTIVE` | 503 | Agent 已下线 |
| `AGENT_INPUT_REJECTED` | 400 | 输入参数校验失败 |
| `EXEC_INTERNAL_ERROR` | 500 | Agent 内部错误 |
| `EXEC_TIMEOUT` | 504 | 执行超时 |
| `EXEC_TOOL_FAILED` | 500 | 工具调用失败 |

### 13.2 日志格式

```json
{
  "timestamp": "2026-02-25T00:00:00.000Z",
  "level": "INFO",
  "trace_id": "a1b2c3d4e5f67890a1b2c3d4e5f67890",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "nexusops.k8s",
  "event": "invoke_start",
  "operation": "get_pod_logs",
  "context": {
    "namespace": "default",
    "pod_name": "api-xxx"
  }
}
```
