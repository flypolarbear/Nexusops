# Agentic Pact

多 Agent 协作的工作规范。

## 快速开始

1. 查看 `state/task_list.json` 选择任务
2. 在 `state/lock_registry.json` 登记锁定
3. 完成后在 `evidence/` 提交证据

## 核心规则

- **一次一个任务**: 不要同时锁定多个任务
- **证据驱动**: 完成后必须提交证据
- **状态同步**: 及时更新 task_list.json

## 文件说明

| 文件 | 说明 |
|------|------|
| PACT.md | 完整协作公约 |
| specs/ | 功能规格 |
| state/ | 运行时状态 |
| evidence/ | 完成证据 |

## 冲突解决优先级

1. PACT.md
2. specs/SPEC-*.md
3. adr/ADR-*.md
