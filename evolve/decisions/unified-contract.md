# 统一合约设计决策

## 状态

已采纳

## 背景

需要为所有 Agent（内置和第三方）提供一致的调用接口。

## 决策

所有 Agent 使用**统一的 Invoke API 合约**：
- 相同的请求格式 (InvokeRequest)
- 相同的响应格式 (InvokeResponse)
- 相同的错误模型 (ErrorDetail)

## 合约结构

### 请求

```json
{
  "request_id": "uuid",
  "agent_id": "nexusops.chat",
  "query": "用户输入",
  "context": {"user_id": "...", "project_id": "..."}
}
```

### 响应

```json
{
  "request_id": "uuid",
  "trace_id": "32位hex",
  "status": "success|error|partial",
  "content": {"text": "...", "format": "markdown"},
  "structured_output": {},
  "error": null
}
```

## 理由

1. 客户端体验一致，无需针对不同 Agent 适配
2. 添加新 Agent 无需修改客户端代码
3. 简化测试，一套合约测试覆盖所有 Agent
4. 便于观测和调试

## 影响

- **优点**: 一致性、可扩展性、简化测试
- **缺点**: 可能需要扩展点支持 Agent 特定功能

## 版本策略

- 合约变更通过 API 版本控制
- 新增可选字段不破坏兼容性
- 破坏性变更需要新版本 (v2)
