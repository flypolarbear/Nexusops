# AI 编码最佳实践

> 提升 AI 编码效率的通用技巧

## 提示词技巧

### 1. 提供上下文

```
# ❌ 差
添加缓存

# ✅ 好
在 backend/app/services/agent_service.py 的 AgentService 类中，
为 generate_response 方法添加 Redis 缓存，
TTL 设为 5 分钟，参考 evolve/patterns/caching.md 的策略
```

### 2. 引用文档

```
# ❌ 差
写个错误处理

# ✅ 好
根据 docs/api/errors.md 中的错误码规范，
为 POST /api/agents/invoke 端点添加错误处理，
包括：参数验证失败、Agent 不存在、调用超时
```

### 3. 分步请求

```
# ❌ 差 (一次请求太多)
重构整个 AgentService，添加缓存、日志、错误处理

# ✅ 好 (分步)
# 第一步
分析 AgentService 的当前实现

# 第二步
为 AgentService 添加 Redis 缓存

# 第三步
添加结构化日志

# 第四步
添加错误处理并运行测试
```

### 4. 请求验证

```
# ❌ 差
改好了吗？

# ✅ 好
实现后请：
1. 运行 cd backend && pytest tests/services/test_agent.py -v
2. 确认所有测试通过
3. 检查是否有 mypy 错误
```

### 5. 正向指导

```
# ❌ 差 (负面规则容易被忽略)
不要使用 as any
不要写空 catch 块

# ✅ 好 (正面指导)
使用明确的类型注解，遇到类型不确定时查阅文档
在 catch 块中记录错误日志并向上抛出
```

---

## 上下文管理

### 1. 只添加必要文件

```
# ❌ 添加整个目录
/add backend/

# ✅ 只添加相关文件
/add backend/app/services/agent_service.py
/add backend/app/api/routes/agents.py
```

### 2. 定期清理历史

```
# Claude Code / OpenCode
/compact    # 压缩历史
/clear      # 清空会话

# 何时清理
- 切换到不相关任务时
- 会话超过 1 小时时
- Token 使用过高时
```

### 3. 使用文件引用

```
# ❌ 粘贴代码
"这是我的代码：[粘贴 100 行代码]"

# ✅ 引用文件
"@backend/app/services/agent_service.py 中的 generate_response 方法"
```

---

## 代码审查

### 1. 安全审查

```
审查这个 PR 的安全性：
1. SQL 注入风险
2. XSS 风险
3. 认证/授权问题
4. 敏感数据泄露
```

### 2. 性能审查

```
审查 AgentService 的性能：
1. N+1 查询问题
2. 缓存使用
3. 数据库连接池
4. 异步操作是否正确
```

### 3. 代码质量

```
审查代码质量：
1. 类型注解完整性
2. 错误处理是否充分
3. 日志是否完善
4. 是否遵循项目规范
```

---

## 常见问题避免

### 1. 类型安全

```python
# ❌ 避免
def process(data):
    return data.get("key")

# ✅ 推荐
def process(data: dict[str, Any]) -> str | None:
    return data.get("key")
```

### 2. 错误处理

```python
# ❌ 避免
try:
    do_something()
except Exception:
    pass

# ✅ 推荐
try:
    do_something()
except SpecificError as e:
    logger.error(f"Failed to do something: {e}")
    raise
```

### 3. 异步操作

```python
# ❌ 避免
def get_user(id):
    return db.query(User).get(id)

# ✅ 推荐
async def get_user(id: int) -> User | None:
    async with db.session() as session:
        return await session.get(User, id)
```

---

## 工作流建议

### 1. 新功能开发

```
1. 描述需求 → AI 分析并给出方案
2. 选择方案 → AI 生成代码骨架
3. 填充细节 → 逐步完善实现
4. 编写测试 → AI 生成测试用例
5. 代码审查 → AI 审查并优化
```

### 2. Bug 修复

```
1. 描述问题 → AI 分析可能原因
2. 定位代码 → AI 帮助找到相关代码
3. 理解逻辑 → AI 解释代码行为
4. 提出修复 → AI 生成修复方案
5. 验证修复 → 运行测试确认
```

### 3. 代码重构

```
1. 分析现状 → AI 理解当前结构
2. 制定计划 → AI 提出重构方案
3. 分步执行 → 每步验证后继续
4. 更新测试 → 确保测试覆盖
5. 文档更新 → 更新相关文档
```

---

## 效率技巧

### 1. 使用模板

创建常用提示词模板：

```markdown
<!-- .opencode/commands/test.md -->
运行相关测试：
1. 确定修改的模块
2. 运行对应的测试文件
3. 检查覆盖率报告
```

### 2. 批量操作

```
# 为多个文件添加类型注解
为 backend/app/services/ 目录下所有 .py 文件添加类型注解
```

### 3. 利用文档

```
# 引用项目文档
根据 evolve/patterns/caching.md 的策略实现缓存

# 引用外部文档
按照 FastAPI 官方文档的最佳实践实现依赖注入
```

---

## 安全注意事项

### 1. 敏感信息

```
# ❌ 不要在提示词中包含
API Key: sk-xxxxx
密码: my-password
数据库连接字符串

# ✅ 使用环境变量或配置文件
# .env (不提交到 git)
DATABASE_URL=postgresql://...
```

### 2. 代码执行

```
# 检查 AI 生成的代码
- 不执行不明来源的 shell 命令
- 不运行未经审查的脚本
- 注意文件操作权限
```

### 3. 依赖安装

```
# 审查 AI 建议的依赖
- 检查包的来源和信誉
- 确认版本号明确
- 检查是否有已知漏洞
```
