# 常见问题 (FAQ)

> AI 编码工具使用中的常见问题与解决方案

## 通用问题

### Q: AI 生成的代码不符合项目规范？

**A**: 检查指令文件是否正确配置：

```bash
# 确认 AGENTS.md 存在
cat AGENTS.md

# 确认工具特定文件存在
ls -la .github/copilot-instructions.md  # GitHub Copilot
ls -la .cursor/rules/                   # Cursor
cat CLAUDE.md                           # Claude Code
```

确保指令文件包含：
- 项目技术栈
- 代码规范
- 构建命令
- 禁止事项

### Q: AI 似乎不知道项目的上下文？

**A**:

1. **重新初始化**
   ```
   # OpenCode / Claude Code
   /init
   ```

2. **手动添加文件**
   ```
   # 在工具中
   /add backend/app/services/agent_service.py
   ```

3. **重建索引** (Cursor)
   - Settings → Codebase Indexing
   - 点击 "Reindex Codebase"

### Q: 响应太慢或超时？

**A**:

1. **减少上下文**
   ```
   /compact  # 压缩历史
   /clear    # 清空会话
   ```

2. **只添加必要文件**
   ```
   # 不要
   /add backend/

   # 而是
   /add backend/app/services/agent_service.py
   ```

3. **使用更快的模型**
   ```bash
   # OpenCode
   /model
   # 选择 gpt-4o 或 claude-sonnet

   # Claude Code
   export ANTHROPIC_MODEL="claude-sonnet-4-6"
   ```

---

## Claude Code

### Q: API Key 无效？

**A**:

```bash
# 检查 key 是否设置
echo $ANTHROPIC_API_KEY

# 检查 key 格式 (应以 sk-ant- 开头)

# 重新设置
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Q: 权限被拒绝？

**A**:

```bash
# 检查文件权限
ls -la backend/

# 在 Claude Code 中
/permissions
# 或启动时指定
claude --allowedTools "Read(*)"
```

### Q: MCP 服务器无法连接？

**A**:

1. 检查配置文件 `~/.claude/claude_desktop_config.json`
2. 确认 uvx 已安装
3. 检查服务器命令是否正确

---

## OpenCode

### Q: 配置不生效？

**A**:

```bash
# 检查配置加载顺序
/config

# 验证 JSON 语法
cat opencode.json | jq .

# 检查配置文件位置
ls -la opencode.json
ls -la ~/.config/opencode/opencode.json
```

### Q: 模型不可用？

**A**:

```bash
# 检查 API key
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# 在 OpenCode 中切换模型
/model
```

### Q: AGENTS.md 未被读取？

**A**:

```bash
# 确保文件在项目根目录
ls -la AGENTS.md

# 重新初始化
/init
```

---

## Cursor

### Q: 规则不生效？

**A**:

```bash
# 检查规则文件位置
ls -la .cursor/rules/

# 确保是 .md 格式
file .cursor/rules/*.md

# 重新加载窗口
Cmd/Ctrl + Shift + P → "Developer: Reload Window"
```

### Q: 索引问题？

**A**:

1. Cursor Settings → Codebase Indexing
2. 点击 "Reindex Codebase"
3. 等待索引完成
4. 重新加载窗口

### Q: Composer 模式不好用？

**A**:

1. 使用更具体的提示
2. 分步请求大改动
3. 每步后验证结果

---

## GitHub Copilot

### Q: 建议不相关？

**A**:

1. 检查 `.github/copilot-instructions.md` 是否存在
2. 确保文件格式正确
3. 重新加载 VS Code 窗口

### Q: CLI 认证失败？

**A**:

```bash
# 重新认证
gh auth login

# 检查状态
gh auth status

# 刷新 token
gh auth refresh
```

### Q: 指令文件未加载？

**A**:

```bash
# 确认文件位置
ls -la .github/copilot-instructions.md

# 检查文件格式
cat .github/copilot-instructions.md

# 在 Copilot Chat 中验证
@workspace 你知道项目的构建命令吗？
```

---

## Codex / Aider

### Q: API Key 问题？

**A**:

```bash
# 检查 key
echo $OPENAI_API_KEY

# 设置 key
export OPENAI_API_KEY="sk-..."

# 验证
aider --model gpt-4o --dry-run
```

### Q: 更改不符合预期？

**A**:

```
# 在 Aider 中
/diff    # 查看差异
/undo    # 撤销更改

# 更具体的提示
"只修改 AgentService 类的 generate_response 方法，
不要改动其他代码"
```

### Q: 上下文过长？

**A**:

```
# 在 Aider 中
/clear    # 清除历史
/map      # 查看 token 使用

# 只添加必要文件
/add backend/app/services/agent_service.py
# 而不是
/add backend/
```

---

## NexusOps 特定问题

### Q: AI 不知道 NexusOps 的项目结构？

**A**: 确保 AGENTS.md 包含完整信息：

```markdown
# AGENTS.md
## 项目结构
NexusOps/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── services/ # 业务逻辑
│   │   └── models/   # 数据模型
├── frontend/         # React 前端
├── docs/             # 用户文档
├── evolve/           # 演进知识库
└── copilot/          # AI 工具指南
```

### Q: AI 生成的代码不符合错误处理规范？

**A**: 在提示中引用文档：

```
根据 evolve/patterns/error-handling.md 的模式，
为这个端点添加错误处理
```

### Q: AI 不知道项目的测试命令？

**A**: 在 AGENTS.md 中明确指定：

```markdown
## 构建命令
- 后端测试: cd backend && pytest tests/ -v
- 前端测试: cd frontend && npm test
```

---

## 获取更多帮助

1. 查看 [工具指南](./tools/) 获取特定工具的详细配置
2. 查看 [指令文件格式](./instruction-files.md) 理解配置选项
3. 查看 [最佳实践](./best-practices.md) 提升使用效率
