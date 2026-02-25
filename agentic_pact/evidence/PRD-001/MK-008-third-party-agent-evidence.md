# Test Evidence: MK-008 - 第三方 Agent 最小闭环

## Environment
- Date: 2026-02-25
- Environment: Development
- Version/Commit: MK-008 implementation

## Overview

MK-008 实现了第三方 Agent 的完整最小闭环：
1. **注册** - 第三方 Agent Manifest 注册
2. **安装** - 安装与启停状态管理
3. **调用** - 调用并返回结构化输出
4. **拒绝** - 下线后调用拒绝验证

## API Endpoints Implemented

### 1. Agent 注册
- `POST /api/v1/market` - 注册新的 Agent
- `GET /api/v1/market/{agent_id}` - 获取 Agent 详情
- `GET /api/v1/market` - 列出所有 Agent

### 2. 安装状态管理
- `POST /api/v1/market/{agent_id}/install` - 安装 Agent
- `POST /api/v1/market/{agent_id}/uninstall` - 卸载 Agent
- `POST /api/v1/market/{agent_id}/enable` - 启用 Agent
- `POST /api/v1/market/{agent_id}/disable` - 禁用 Agent
- `GET /api/v1/market/{agent_id}/install-status` - 获取安装状态
- `GET /api/v1/market/installed` - 列出已安装的 Agent

### 3. Agent 调用
- `POST /api/v1/agents/{agent_id}/invoke` - 调用 Agent

## Request/Response Samples

### 注册 Agent

**Request:**
```json
POST /api/v1/market
{
    "manifest": {
        "agent_id": "com.example.weather-agent",
        "name": "Weather Agent",
        "version": "1.0.0",
        "description": "Get weather information",
        "category": "utilities",
        "capabilities": ["get_weather", "get_forecast"],
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather",
                "inputSchema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            }
        ]
    },
    "visibility": "public"
}
```

**Response (201 Created):**
```json
{
    "agent_id": "com.example.weather-agent",
    "name": "Weather Agent",
    "version": "1.0.0",
    "status": "active",
    "category": "utilities",
    "capabilities": ["get_weather", "get_forecast"],
    "tools_count": 1
}
```

### 安装 Agent

**Request:**
```json
POST /api/v1/market/com.example.weather-agent/install
```

**Response (200 OK):**
```json
{
    "agent_id": "com.example.weather-agent",
    "name": "Weather Agent",
    "version": "1.0.0",
    "install_status": "installed",
    "installed_at": "2026-02-25T00:00:00.000000",
    "message": "Agent installed successfully"
}
```

### 调用 Agent

**Request:**
```json
POST /api/v1/agents/com.example.weather-agent/invoke
{
    "request_id": "req-001",
    "conversation_id": "conv-001",
    "agent_id": "com.example.weather-agent",
    "query": "What's the weather in Tokyo?"
}
```

**Response (200 OK):**
```json
{
    "request_id": "req-001",
    "status": "success",
    "content": {
        "text": "## Third-party Agent Response\n\n**Agent:** Weather Agent (`com.example.weather-agent`)\n**Trace ID:** xxx-xxx-xxx\n\nYour request has been processed...",
        "format": "markdown"
    },
    "structured_output": {
        "type": "third_party_response",
        "agent_id": "com.example.weather-agent",
        "query": "What's the weather in Tokyo?",
        "processed": true
    },
    "metadata": {
        "trace_id": "xxx-xxx-xxx-xxx",
        "agent_type": "third_party",
        "execution_mode": "mock"
    }
}
```

### 未安装时调用被拒绝

**Request:**
```json
POST /api/v1/agents/com.example.weather-agent/invoke
{
    "request_id": "req-002",
    "conversation_id": "conv-002",
    "agent_id": "com.example.weather-agent",
    "query": "test"
}
```

**Response (403 Forbidden):**
```json
{
    "detail": {
        "code": "AGENT_NOT_INSTALLED",
        "message": "Agent 'com.example.weather-agent' is not installed. Please install it first.",
        "trace_id": "xxx-xxx-xxx-xxx"
    }
}
```

### 禁用时调用被拒绝

**Response (403 Forbidden):**
```json
{
    "detail": {
        "code": "AGENT_DISABLED",
        "message": "Agent 'com.example.weather-agent' is disabled. Please enable it first.",
        "trace_id": "xxx-xxx-xxx-xxx"
    }
}
```

## Test Results

### Test Summary
- **Total Tests**: 8
- **Passed**: 8
- **Failed**: 0
- **Pass Rate**: 100%

### Test Cases

| Test ID | Description | Status |
|---------|-------------|--------|
| RG-T01 | 注册合法 Manifest 成功 | PASS |
| RG-T02 | 注册非法 Manifest 失败并返回字段级错误 | PASS |
| RG-T03 | 安装已注册 Agent 成功并可调用 | PASS |
| RG-T04 | 下线 Agent 后调用被拒绝 | PASS |
| Enable-01 | 禁用 Agent 后调用被拒绝 | PASS |
| Enable-02 | 重新启用 Agent 后可调用 | PASS |
| Output-01 | 调用返回结构化输出 | PASS |
| List-01 | 列出已安装 Agent | PASS |

## Trace IDs

测试运行中的示例 trace_id：
- `8f2fac5e-efd3-415f-8866-a6714d73ae78`
- `99e5098d-f1f4-429b-917f-a35a5c4a7bc2`
- `eb4c0ea4-da33-438a-8289-337bedd9db2b`

## Files Changed

### New Files
- `backend/app/stores/agent_store.py` - 共享 Agent 存储模块
- `backend/app/stores/__init__.py` - 存储模块初始化
- `backend/tests/__init__.py` - 测试模块初始化
- `backend/tests/test_mk008_third_party_agent.py` - MK-008 测试用例

### Modified Files
- `backend/app/api/agent_market.py` - 添加安装/卸载/启用/禁用 API
- `backend/app/api/agents.py` - 添加第三方 Agent 执行器和安装状态检查

## Risks & TODOs

### Risks
1. **内存存储**: 当前使用内存存储，重启后数据丢失。生产环境需要替换为数据库存储。
2. **无认证**: 当前 API 无认证保护，生产环境需要添加认证。
3. **Mock 执行器**: 第三方 Agent 当前使用 mock 响应，需要支持真实 HTTP 调用。

### TODOs
1. 将内存存储替换为数据库存储
2. 添加 API 认证和授权
3. 实现真实的第三方 Agent HTTP 调用（带超时和错误处理）
4. 添加 Agent 健康检查机制
5. 实现 Agent 版本管理

## Conclusion

**Status: PASS**

MK-008 已成功实现第三方 Agent 最小闭环，包括：
- Agent 注册功能
- 安装/卸载/启用/禁用状态管理
- 调用时检查安装状态
- 未安装/禁用时拒绝调用
- 返回结构化输出和 trace_id

所有测试用例通过，符合 PRD-001 验收标准。
