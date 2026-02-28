---
description: "Magic command to start complete Spec-Kit workflow from natural language. Usage: /spec 我想在顶部 tab 栏添加一个小狗 icon"

# Agent Dispatch Configuration
agent_dispatch:
  workflow:
    - phase: specify
      primary: sisyphus
      clarify: metis
      
    - phase: plan
      research: librarian
      architecture: oracle
      task_planning: prometheus
      review: momus
      docs: writing
      
    - phase: tasks
      primary: sisyphus
      analyze: momus

handoffs:
  - label: Start Spec-Kit Specify
    agent: speckit.specify
    prompt: "Start the spec-kit workflow for this feature request."
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This is the **magic command** that starts the complete Spec-Kit workflow from a natural language feature description.

### Workflow Overview

```
/spec "我想在顶部 tab 栏添加一个小狗 icon"
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 1: /speckit.specify                               │
│   Agent: Sisyphus (主控)                                 │
│   Clarify: metis (如有歧义)                              │
│   Output: spec.md, checklists/requirements.md            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: /speckit.plan                                   │
│   Research: librarian (技术研究)                         │
│   Architecture: oracle (架构设计)                        │
│   Task Planning: prometheus (任务规划)                   │
│   Review: momus (计划审查)                               │
│   Docs: writing (文档撰写)                               │
│   Output: plan.md, research.md, data-model.md, contracts/│
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: /speckit.tasks                                  │
│   Agent: Sisyphus (任务分解)                             │
│   Analyze: momus (一致性分析，可选)                      │
│   Output: tasks.md                                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
  ✅ Ready for implementation
```

### Execution Steps

1. **Parse User Input**
   - Extract feature description from `$ARGUMENTS`
   - If empty: ERROR "Usage: /spec <feature description>"

2. **Phase 1: Execute `/speckit.specify`**
   ```bash
   # Dispatch to appropriate agent
   agent=$(./agent-dispatch.sh spec specify)
   
   # Execute specification phase
   # Sisyphus creates spec.md with user stories and requirements
   # If ambiguities exist, metis is dispatched for clarification
   ```

3. **Phase 2: Execute `/speckit.plan`**
   ```bash
   # Multi-agent dispatch for complex planning
   task(subagent_type="librarian", run_in_background=true, 
        prompt="Research tech stack for {feature}...")
   
   task(subagent_type="oracle", 
        prompt="Design architecture for {feature}...")
   
   task(subagent_type="prometheus",
        prompt="Create task breakdown plan for {feature}...")
   
   task(subagent_type="momus",
        prompt="Review plan for {feature}...")
   
   task(subagent_type="writing",
        prompt="Write quickstart.md for {feature}...")
   ```

4. **Phase 3: Execute `/speckit.tasks`**
   ```bash
   # Sisyphus decomposes tasks from plan
   # Creates dependency-ordered tasks.md
   ```

5. **Report Completion**
   - Summarize all generated artifacts
   - Show path to tasks.md
   - Indicate ready for implementation

### Agent Dispatch Summary

| Phase | Activity | Agent | Purpose |
|-------|----------|-------|---------|
| specify | 主流程 | sisyphus | 编排规格创建 |
| specify | 澄清 | metis | 消除歧义 |
| plan | 研究 | librarian | 技术调研 |
| plan | 架构 | oracle | 架构设计 |
| plan | 任务规划 | prometheus | 任务分解 |
| plan | 审查 | momus | 质量把关 |
| plan | 文档 | writing | 文档撰写 |
| tasks | 分解 | sisyphus | 任务编排 |

### Example Usage

```bash
# 简单功能
/spec 我想在顶部 tab 栏添加一个小狗 icon

# 复杂功能
/spec 实现一个用户认证系统，支持邮箱登录和 OAuth2

# 带约束的功能
/spec 添加数据导出功能，支持 CSV 和 Excel 格式，导出操作需要记录日志
```

### Validation

Before proceeding to implementation, verify:
- [ ] `specs/<feature>/spec.md` exists
- [ ] `specs/<feature>/plan.md` exists
- [ ] `specs/<feature>/tasks.md` exists
- [ ] All checklists pass (if any)

### Notes

- This command integrates the full Spec-Kit workflow with OMO agent dispatch
- Each phase uses the optimal agent based on task complexity
- Review phases (momus) are automatic for quality assurance
- The workflow can be interrupted at any phase for user review
