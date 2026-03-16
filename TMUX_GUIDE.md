# NexusOps 开发环境 - tmux 快速指南

## 📊 当前 Session 状态

**Session 名称**: `nexusops-dev`
**创建时间**: 2026-03-13 17:08
**状态**: ✅ 运行中

---

## 🪟 窗口布局

| 窗口 | 名称 | 用途 | 目录 |
|------|------|------|------|
| **0** | Claude-Code | Claude Code 开发环境 | `~/Development/ClaudeCodeWorkspace/Projects/NexusOps` |
| **1** | Git | Git 操作 | `~/Development/ClaudeCodeWorkspace/Projects/NexusOps` |
| **2** | Backend | 后端开发 (FastAPI) | `~/Development/ClaudeCodeWorkspace/Projects/NexusOps/backend` |
| **3** | Frontend | 前端开发 (React) | `~/Development/ClaudeCodeWorkspace/Projects/NexusOps/frontend` |

---

## 🚀 连接到 Session

### 方式 1：直接连接
```bash
tmux attach -t nexusops-dev
```

### 方式 2：简写
```bash
tmux a -t nexusops-dev
```

### 方式 3：使用脚本
```bash
~/start_nexusops_tmux.sh
```

---

## ⌨️ 常用快捷键

### Session 管理
- `Ctrl+a d` - 断开 session（后台继续运行）
- `Ctrl+a D` - 关闭 session（完全退出）
- `Ctrl+a s` - 列出所有 session

### 窗口管理
- `Ctrl+a c` - 创建新窗口
- `Ctrl+a n` - 下一个窗口
- `Ctrl+a p` - 上一个窗口
- `Ctrl+a 0-9` - 切换到窗口 0-9
- `Ctrl+a &` - 关闭当前窗口

### 分屏操作
- `Ctrl+a |` - 垂直分屏
- `Ctrl+a -` - 水平分屏
- `Ctrl+a 方向键` - 切换分屏

### 其他操作
- `Ctrl+a ?` - 显示所有快捷键
- `Ctrl+a :` - 进入命令模式
- `Ctrl+a r` - 重载配置文件

---

## 💡 使用场景

### 场景 1: 使用 Claude Code 开发
```bash
# 连接到 session
tmux a -t nexusops-dev

# 会自动进入窗口 0 (Claude-Code)
# Claude Code 应该已经在运行

# 如果没有运行，claude
```

### 场景 2: 在 Backend 窗口工作
```bash
# 连接到 session
tmux a -t nexusops-dev

# 切换到窗口 2
Ctrl+a 2

# 启动后端服务
cd ~/Development/ClaudeCodeWorkspace/Projects/NexusOps/backend
source venv/bin/activate  # 如果有虚拟环境
uvicorn src.main:app --reload
```

### 场景 3: 在 Frontend 窗口工作
```bash
# 连接到 session
tmux a -t nexusops-dev

# 切换到窗口 3
Ctrl+a 3

# 启动前端服务
cd ~/Development/ClaudeCodeWorkspace/Projects/NexusOps/frontend
npm run dev
```

### 场景 4: Git 操作
```bash
# 连接到 session
tmux a -t nexusops-dev

# 切换到窗口 1
Ctrl+a 1

# 执行 Git 操作
git status
git add .
git commit -m "update message"
git push
```

---

## 🔧 高级操作

### 在后台运行 Session
```bash
# 断开但不关闭
Ctrl+a d

# 或者
tmux detach
```

### 查看所有 Session
```bash
tmux ls
```

### 关闭 Session
```bash
# 方式 1: 连接后关闭
tmux a -t nexusops-dev
# 然后输入
exit

# 方式 2: 从外部关闭
tmux kill-session -t nexusops-dev

# 方式 3: 关闭所有 session
tmux kill-server
```

---

## 📝 快速命令别名

可以添加到 `~/.zshrc` 或 `~/.bashrc`:

```bash
# NexusOps 开发快捷命令
alias nexusops='tmux a -t nexusops-dev'
alias nexusops-start='~/start_nexusops_dev.sh'
alias nexusops-stop='tmux kill-session -t nexusops-dev'
alias nexusops-list='tmux ls'
```

然后运行：
```bash
source ~/.zshrc
```

之后就可以用：
```bash
nexusops          # 连接到 session
nexusops-start    # 启动 session
nexusops-stop     # 停止 session
nexusops-list     # 列出所有 session
```

---

## 🎯 推荐工作流程

1. **启动开发环境**
   ```bash
   ~/start_nexusops_dev.sh
   ```

2. **连接到 session**
   ```bash
   tmux a -t nexusops-dev
   ```

3. **在窗口 0 使用 Claude Code 开发**

4. **在窗口 2 启动后端服务**
   ```bash
   Ctrl+a 2
   cd backend
   uvicorn src.main:app --reload
   ```

5. **在窗口 3 启动前端服务**
   ```bash
   Ctrl+a 3
   cd frontend
   npm run dev
   ```

6. **断开但保持运行**
   ```bash
   Ctrl+a d
   ```

---

## ⚠️ 注意事项

1. **Session 在后台持续运行** - 即使关闭终端也不会停止
2. **退出前记得保存文件** - 使用 `Ctrl+a d` 断开而不是直接关闭
3. **定期检查运行状态** - 使用 `tmux ls` 查看所有 session
4. **重启电脑后需要重新启动** - tmux session 不会自动恢复

---

## 🐛 故障排除

### Session 已存在
```bash
# 错误: duplicate session
# 解决: 先关闭旧的
tmux kill-session -t nexusops-dev
# 然后重新创建
~/start_nexusops_dev.sh
```

### 找不到 Session
```bash
# 查看 session 列表
tmux ls

# 如果没有输出，说明需要重新创建
~/start_nexusops_dev.sh
```

### Claude Code 没有启动
```bash
# 连接到 session
tmux a -t nexusops-dev

# 切换到窗口 0
Ctrl+a 0

# 手动启动
claude
```

---

**创建时间**: 2026-03-13 17:08
**维护者**: OpenClaw Assistant
