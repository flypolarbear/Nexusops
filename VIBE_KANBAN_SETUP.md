# NexusOps 项目导入 Vibe Kanban 操作指南

## ✅ 第一步：打开 Vibe Kanban

浏览器应该已经自动打开：http://localhost:54348

如果没有打开，手动访问：http://localhost:54348

---

## 📦 第二步：导入 NexusOps 项目

### 方法 1：在界面中导入

1. **点击 "+" 或 "New Project"**

2. **填写项目信息：**
   ```
   项目名称：NexusOps
   描述：AI Native Operations Platform
   Git 仓库 URL：https://gitee.com/auto-ark/nexusops.git
   本地路径：/Users/liuhanze/Development/ClaudeCodeWorkspace/Projects/NexusOps
   ```

3. **点击 "Create" 或 "Import"**

---

## 📋 第三步：创建第一个开发任务

### 推荐任务 1：环境优化

```
标题：优化 NexusOps 开发环境配置
描述：
- 检查并更新依赖版本
- 优化开发服务器配置
- 添加环境变量文档
- 更新 README.md

标签：setup, optimization
优先级：Medium
```

### 推荐任务 2：API 文档

```
标题：添加 FastAPI 自动文档
描述：
- 配置 Swagger UI
- 添加 API 端点描述
- 创建请求/响应示例
- 添加认证说明

文件：backend/src/main.py
标签：backend, documentation
优先级：High
```

### 推荐任务 3：前端优化

```
标题：优化前端构建配置
描述：
- 配置 Vite 构建优化
- 添加代码分割
- 优化打包体积
- 配置环境变量

文件：frontend/vite.config.ts
标签：frontend, optimization
优先级：Medium
```

---

## 🚀 第四步：启动工作区

1. **选择任务**
   - 点击任务卡片

2. **启动工作区**
   - 点击 "Start Workspace"
   - 选择 **Claude Code** 作为执行器
   - 选择分支（建议创建新分支）

3. **等待 Claude Code 开始工作**
   - 自动读取任务
   - 开始实现
   - 实时显示进度

---

## 💡 快速开始提示

### 在 Vibe Kanban 界面中：

1. **首次使用**
   - 可能需要登录或创建账户
   - 选择 Claude Code 作为默认执行器

2. **导入项目后**
   - 项目会显示在看板上
   - 可以看到所有分支
   - 可以创建任务

3. **创建任务时**
   - 尽量具体描述需求
   - 指定相关文件路径
   - 添加技术要求

---

## 🎯 推荐的第一个任务

**创建这个任务开始：**

```
标题：添加健康检查 API 端点
描述：
在 backend 中添加一个健康检查端点：

- 路径：/api/health
- 方法：GET
- 返回：{"status": "healthy", "version": "1.0.0"}
- 用途：Kubernetes 健康检查

文件：
- backend/src/routes/health.py
- backend/src/main.py (添加路由)

技术要求：
- FastAPI
- 异步处理
- 返回 JSON 格式

测试：
- 使用 curl 测试端点
- 验证返回格式
```

这个任务简单明确，适合作为第一个测试任务。

---

## 📱 界面操作提示

### Kanban 看板列
- **Backlog** - 待规划任务
- **To Do** - 待开始任务
- **In Progress** - 进行中
- **Review** - 代码审查
- **Done** - 已完成

### 工作区功能
- **Terminal** - 终端输出
- **Files** - 文件变更
- **Preview** - 浏览器预览
- **Diff** - 代码差异

---

## 🔄 下一步行动

1. ✅ 浏览器已打开 Vibe Kanban
2. ⏳ 导入 NexusOps 项目
3. ⏳ 创建第一个任务
4. ⏳ 启动工作区
5. ⏳ 观察 Claude Code 工作

---

## 🐛 故障排除

### 问题：找不到项目
**解决：**
- 确保路径正确
- 检查 Git 仓库是否克隆

### 问题：Claude Code 未检测到
**解决：**
- 确保 Claude Code 已安装
- 检查 ANTHROPIC_API_KEY 是否配置

### 问题：无法启动工作区
**解决：**
- 检查项目配置
- 确保有 Git 权限

---

**创建时间**: 2026-03-13 23:34
**状态**: ✅ 准备就绪
