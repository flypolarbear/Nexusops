---
description: 总结本次任务会话，将经验、模式、反模式或技术决策归档到 evolve/ 知识库。建议在完成重要任务模块后执行。
handoffs:
  - label: Continue Development
    agent: speckit.implement
    prompt: Continue with implementation tasks
---

## User Input

```text
$ARGUMENTS
```

## Outline

Goal: 分析本次会话的工作内容，提取可复用的经验，更新 `evolve/` 知识库，使项目持续积累最佳实践。

Execution steps:

1. **会话分析** - 回顾本次会话完成的工作：
   - 修改了哪些文件/模块
   - 做了哪些技术决策
   - 遇到了什么问题及解决方案
   - 发现了什么有效的模式或值得避免的坑

2. **分类判断** - 将发现的内容分类：

   | 类别 | 目标目录 | 适用场景 |
   |------|----------|----------|
   | Pattern | `evolve/patterns/` | 验证有效的解决方案、最佳实践 |
   | Anti-pattern | `evolve/anti-patterns/` | 需要避免的错误做法、常见陷阱 |
   | Decision | `evolve/decisions/` | 重要技术选型、架构决策、ADR |

3. **用户确认** - 向用户展示分析结果并询问：
   ```
   ## 本次会话总结
   
   ### 完成的工作
   - [列出主要改动]
   
   ### 发现的内容
   | 类型 | 标题 | 建议操作 |
   |------|------|----------|
   | pattern/anti-pattern/decision | 简短描述 | 新建/追加到 X 文件 |
   
   ### 推荐归档
   - [推荐的具体条目]
   
   是否确认归档？可补充或修改内容。
   ```

4. **文档生成** - 根据用户确认，按以下模板生成内容：

   ### Pattern 模板
   ```markdown
   ## [模式名称]
   
   ### 问题描述
   [简述要解决的问题]
   
   ### 解决方案
   [核心方案描述]
   
   ```python/typescript
   // 代码示例
   ```
   
   ### 注意事项
   - ✅ [推荐做法]
   - ❌ [避免做法]
   ```

   ### Anti-pattern 模板
   ```markdown
   ## [反模式名称]
   
   ### [类别，如：类型安全、异步处理等]
   
   ```python/typescript
   // ❌ 错误
   [错误示例]
   
   // ✅ 正确
   [正确示例]
   ```
   ```

   ### Decision 模板
   ```markdown
   # [决策标题]
   
   ## 状态
   已采纳 / 已废弃 / 讨论中
   
   ## 背景
   [为什么需要做这个决策]
   
   ## 决策
   [具体决策内容]
   
   ## 理由
   1. [理由一]
   2. [理由二]
   
   ## 影响
   - **优点**: [列举]
   - **缺点**: [列举]
   ```

5. **文件更新** - 智能选择更新方式：
   - **追加模式**: 同类内容追加到现有文件（如新的反模式添加到 `avoid.md`）
   - **新建模式**: 新主题创建独立文件（如新的技术决策）
   
   命名规则：
   - patterns: `kebab-case.md` (如 `circuit-breaker.md`)
   - decisions: `kebab-case.md` (如 `unified-contract.md`)
   - anti-patterns: 统一追加到 `avoid.md`，除非用户要求新建

6. **索引更新** - 如果新建了文件，更新 `evolve/index.md`：
   ```markdown
   | [模式名称](./patterns/xxx.md) | 简短描述 |
   ```

7. **完成报告**:
   ```
   ## Wind-up 完成
   
   ### 更新的文件
   - evolve/patterns/xxx.md (新建)
   - evolve/decisions/xxx.md (追加)
   - evolve/index.md (更新索引)
   
   ### 归档条目
   - Pattern: [名称] - [一句话描述]
   - Decision: [名称] - [一句话描述]
   
   项目知识库已更新！
   ```

## 行为规则

- **必须有实质内容**: 如果本次会话没有值得归档的经验，直接告知用户并退出
- **尊重用户判断**: 用户可以跳过、修改或补充建议的归档内容
- **保持简洁**: Pattern/Decision 文档控制在 50-100 行，避免冗长
- **代码示例**: Pattern 必须包含代码示例，Anti-pattern 必须有 ✅/❌ 对比
- **时间戳**: Decision 文档可添加日期标签 `YYYY-MM-DD`
- **不过度归档**: 琐碎的、项目无关的、或通用知识不归档

## 触发建议

适合执行 `/wind-up` 的场景：
- 完成一个功能模块的开发
- 解决了一个复杂的 bug
- 做了重要的架构调整
- 发现了一个有用的模式或陷阱
- 完成一个 sprint 或里程碑

不适合的场景：
- 简单的 typo 修复
- 常规的文档更新
- 没有新知识产生的重复性工作
