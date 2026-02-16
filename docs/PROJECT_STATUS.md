# NexusOps 项目状态与开发计划

> 📅 更新时间: 2025-02-17
> 📌 当前位置: Phase 3.5 完成，准备 Phase 4

---

## 🚨 发现的问题

### 1. 后端语言混乱

```
backend/
├── go.mod          ← Go 后端 (5 个 .go 文件)
├── pyproject.toml  ← Python 后端 (14 个 .py 文件)
├── cmd/            ← Go 服务入口
├── internal/       ← Go 内部包
├── app/            ← Python FastAPI 应用
└── pkg/            ← Go 公共包
```

**问题**: 同一目录下存在两种语言的后端实现，造成混乱。

---

## 📊 开发进度线性视图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NexusOps 开发进度                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: Vibe Coding        ████████████████████ 100% ✅ 已完成            │
│  ├── VC-001 版本卡片增强     ✅                                            │
│  ├── VC-002 创建版本流程     ✅                                            │
│  ├── VC-003 申请上线流程     ✅                                            │
│  ├── VC-004 Dashboard        ✅                                            │
│  └── VC-005 WorldMap筛选     ✅                                            │
│                                                                              │
│  Phase 2: 部署监控与诊断     ████████████████████ 100% ✅ 已完成            │
│  ├── OPS-001 部署链追踪      ✅                                            │
│  ├── OPS-002 K8sGPT诊断      ✅                                            │
│  └── OPS-003 快捷命令        ✅                                            │
│                                                                              │
│  Phase 3: 后端集成           ███████████████░░░░░  75% ⚠️ 部分完成         │
│  ├── BE-001 版本管理API      ✅ (Python)                                    │
│  ├── BE-002 ArgoCD集成       ✅ (Python)                                    │
│  ├── BE-003 CI/CD集成        ❌ 未完成                                      │
│  └── BE-004 Agent Gateway    ✅ (Python)                                    │
│                                                                              │
│  Phase 3.5: Agent基础架构   ████████████████████ 100% ✅ 已完成            │
│  ├── AGENT-001 类型系统      ✅                                            │
│  ├── AGENT-002 上下文管理    ✅                                            │
│  ├── AGENT-003 响应渲染器    ✅                                            │
│  ├── AGENT-004 Agent化改造   ✅                                            │
│  └── AGENT-005 工具层        ✅                                            │
│                                                                              │
│  Phase 4: 优化打磨           ░░░░░░░░░░░░░░░░░░░░   0% 📋 待开始           │
│  ├── OPT-001 WebSocket       ⬜                                            │
│  ├── OPT-002 性能优化        ⬜                                            │
│  └── OPT-003 JSON输出保证    ⬜                                            │
│                                                                              │
│  Phase 5: Agent Market       ░░░░░░░░░░░░░░░░░░░░   0% 📋 未来规划         │
│  ├── MK-001 注册中心         ⬜                                            │
│  ├── MK-002 Agent Gateway    ⬜                                            │
│  ├── MK-003 Store UI         ⬜                                            │
│  ├── MK-004 多语言SDK        ⬜                                            │
│  └── MK-005 开发文档         ⬜                                            │
│                                                                              │
│  ══════════════════════════════════════════════════════════════════════════ │
│                                                                              │
│  📍 当前位置: Phase 3.5 ✅ → Phase 4 待开始                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ 已完成功能 (21 项)

| # | ID | 功能 | 语言 | 文件位置 |
|---|-----|------|------|----------|
| 1 | VC-001 | 版本卡片增强 | TypeScript | `frontend/src/pages/Projects/` |
| 2 | VC-002 | 创建版本流程 | TypeScript | `frontend/src/components/` |
| 3 | VC-003 | 申请上线流程 | TypeScript | `frontend/src/components/` |
| 4 | VC-004 | Dashboard | TypeScript | `frontend/src/pages/Dashboard/` |
| 5 | VC-005 | WorldMap筛选 | TypeScript | `frontend/src/components/` |
| 6 | OPS-001 | 部署链追踪 | TypeScript | `frontend/src/pages/Deployments/` |
| 7 | OPS-002 | K8sGPT诊断 | TypeScript | `frontend/src/pages/Resources/` |
| 8 | OPS-003 | 快捷命令 | TypeScript | `frontend/src/components/` |
| 9 | BE-001 | 版本管理API | Python | `backend/app/api/projects.py` |
| 10 | BE-002 | ArgoCD集成 | Python | `backend/app/api/deployments.py` |
| 11 | BE-004 | Agent Gateway | Python | `backend/app/api/agents.py` |
| 12 | AGENT-001 | Agent类型系统 | TypeScript | `frontend/src/types/agent.ts` |
| 13 | AGENT-002 | 上下文管理 | TypeScript | `frontend/src/stores/agentContextStore.ts` |
| 14 | AGENT-003 | 响应渲染器 | TypeScript | `frontend/src/components/AgentResponseRenderer.tsx` |
| 15 | AGENT-004 | Agent化改造 | TypeScript | `frontend/src/components/AIAssistantDrawerV2.tsx` |
| 16 | AGENT-005 | 工具层 | TypeScript | `frontend/src/agents/tools/` |
| 17 | ADR-001~010 | 架构决策 | Markdown | `docs/adr/` |

---

## ❌ 未完成功能 (9 项)

| # | ID | 功能 | 优先级 | 说明 |
|---|-----|------|--------|------|
| 1 | BE-003 | CI/CD集成 | High | Jenkins/GitLab CI 集成 |
| 2 | OPT-001 | WebSocket | Medium | 实时数据推送 |
| 3 | OPT-002 | 性能优化 | Medium | 缓存、分页、懒加载 |
| 4 | OPT-003 | JSON输出保证 | Medium | Instructor集成 |
| 5 | MK-001 | Agent注册中心 | High | Phase 5 |
| 6 | MK-002 | Agent Gateway | High | Phase 5 |
| 7 | MK-003 | Agent Store UI | Medium | Phase 5 |
| 8 | MK-004 | 多语言SDK | Medium | Phase 5 |
| 9 | MK-005 | 开发文档 | Low | Phase 5 |

---

## 💻 开发语言选择建议

### 当前状态

| 组件 | 当前语言 | 文件数 |
|------|----------|--------|
| 前端 | TypeScript/React | 33 文件 |
| 后端 A | Go (Gin) | 5 文件 |
| 后端 B | Python (FastAPI) | 14 文件 |

### 推荐方案

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        推荐技术栈                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  前端 (保持不变)                                                              │
│  ├── 语言: TypeScript + React                                                │
│  ├── 框架: Ant Design 5                                                      │
│  ├── 状态: Zustand                                                           │
│  └── 原因: 已完成 99%，无需改动                                               │
│                                                                              │
│  后端 (推荐选择)                                                              │
│  ├── 🎯 推荐: Python (FastAPI)                                               │
│  │   ├── 原因:                                                               │
│  │   │   ✓ AI/ML 生态最好 (Instructor, LangChain, OpenAI SDK)                 │
│  │   │   ✓ 开发速度快，适合快速迭代                                            │
│  │   │   ✓ 已完成更多代码 (14 vs 5 文件)                                       │
│  │   │   ✓ 天然支持 async/await                                               │
│  │   │   ✓ Pydantic 类型系统与前端 TypeScript 天然对应                         │
│  │   │                                                                       │
│  │   └── 风险: 性能略低于 Go (可通过异步缓解)                                   │
│  │                                                                           │
│  └── 备选: Go (Gin)                                                          │
│      ├── 原因:                                                               │
│      │   ✓ 高性能，适合高并发                                                  │
│      │   ✓ 部署简单，单二进制                                                  │
│      │   ✓ 强类型，编译时检查                                                  │
│      │                                                                       │
│      └── 缺点:                                                                │
│          ✗ AI 库支持弱                                                        │
│          ✗ 需要重写 Python 代码                                                │
│                                                                              │
│  Agent SDK (多语言)                                                           │
│  ├── Python SDK  ← 优先 (与后端同语言)                                        │
│  ├── Node.js SDK ← 次要                                                       │
│  └── Go/Java SDK ← 未来
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 最终建议

| 决策点 | 建议 |
|--------|------|
| **后端主语言** | Python (FastAPI) |
| **Go 代码处理** | 删除或移动到 `backend-go-archive/` |
| **理由** | AI 生态、已有代码量、开发效率 |
| **何时选 Go** | 仅在性能成为瓶颈时考虑 |

---

## 📁 建议的项目结构

```
NexusOps/
├── frontend/                  # TypeScript + React
│   ├── src/
│   │   ├── components/       # UI 组件
│   │   ├── pages/            # 页面
│   │   ├── stores/           # Zustand stores
│   │   ├── services/         # API 服务
│   │   ├── agents/           # Agent 工具
│   │   └── types/            # 类型定义
│   └── package.json
│
├── backend/                   # Python + FastAPI (保留)
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务逻辑
│   │   └── core/             # 配置
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docs/                      # 文档
│   ├── adr/                  # 架构决策记录
│   └── *.md                  # 设计文档
│
├── agent-sdks/               # (未来) 多语言 SDK
│   ├── python/
│   ├── nodejs/
│   └── go/
│
├── feature_list.json         # 功能清单
└── README.md
```

---

## 🎯 线性开发路线图

```
现在 ──────────────────────────────────────────────────────────────> 未来

[✅ Phase 1] → [✅ Phase 2] → [✅ Phase 3.5] → [⚠️ Phase 3 收尾] → [📋 Phase 4] → [📋 Phase 5]
                                                      │
                                                      ▼
                                              BE-003 CI/CD 集成
                                              (唯一的 Phase 3 遗留)
```

### 下一步行动 (按优先级)

1. **清理后端** - 删除/归档 Go 代码，统一使用 Python
2. **完成 BE-003** - 实现 CI/CD 集成 (Jenkins/GitLab)
3. **Phase 4** - WebSocket + 性能优化
4. **Phase 5** - Agent Market (未来)

---

## 📋 决策确认

需要您确认以下决策：

- [ ] 后端统一使用 **Python (FastAPI)**
- [ ] 删除/归档 Go 后端代码
- [ ] 优先完成 BE-003 CI/CD 集成
- [ ] 然后进入 Phase 4 优化打磨

请确认后我将继续执行。
