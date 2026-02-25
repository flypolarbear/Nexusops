# NexusOps 测试策略与质量保证研究报告

**研究员**: Cynthia
**日期**: 2026-02-25
**项目**: NexusOps - AI Native Operations Platform

---

## 1. 现有测试分析

### 1.1 测试文件概览

当前项目后端测试位于 `backend/tests/` 目录，共有以下测试文件：

| 文件 | 描述 | 测试用例数 |
|------|------|-----------|
| `test_mk006_mk007_p0.py` | MK-006/MK-007 P0 级别测试 | 16 个测试方法 |
| `test_mk008_third_party_agent.py` | 第三方 Agent 最小闭环测试 | 10 个测试方法 |
| `__init__.py` | 测试包初始化 | - |

**总计**: 约 26 个测试用例

### 1.2 测试用例详细分析

#### MK-006 Gateway 调用契约测试 (CT-001 ~ CT-008)

```
CT-001: 有效请求返回成功响应 - PASS
CT-002: 无效 JSON 返回 INPUT_INVALID_JSON - PASS
CT-003: 缺少 request_id 返回 INPUT_MISSING_FIELD - PASS
CT-004: agent_id 格式错误返回 INPUT_INVALID_AGENT_ID - PARTIAL (允许 422/500)
CT-005: 不存在的 agent_id 返回 AGENT_NOT_FOUND - PARTIAL (允许 404/500)
CT-006: 无 Authorization 返回 AUTH_TOKEN_MISSING - SKIPPED (Demo 模式不强制认证)
CT-007: 响应必须包含 trace_id 和 request_id - PASS
CT-008: 错误响应符合 ErrorDetail Schema - PASS
```

#### MK-007 Gateway 插件执行边界测试 (EX-001 ~ EX-008)

```
EX-001: 内置 Agent 调用成功 - PARTIAL (允许 200/500)
EX-002: 第三方 Agent 调用成功 - PARTIAL (允许 200/500)
EX-003: 不存在的 Agent 返回 AGENT_NOT_FOUND - PASS
EX-004: RemoteExecutor 超时返回 EXEC_TIMEOUT - PASS (仅验证错误码定义)
EX-005: RemoteExecutor 连接失败返回 EXEC_DOWNSTREAM_ERROR - PASS (仅验证错误码定义)
EX-006: 同一 trace_id 贯穿内置 Agent 调用 - PASS
EX-007: 同一 trace_id 贯穿第三方 Agent 调用 - PARTIAL
EX-008: Agent Handler 返回 ExecutorResult - PASS
```

#### MK-008 第三方 Agent 最小闭环测试

```
RG-T01: Register valid Manifest successfully - PASS
RG-T02: Register invalid Manifest fails with field-level errors - PASS
RG-T03: Install registered Agent successfully and can invoke - PARTIAL
RG-T04: Uninstall Agent then invoke is rejected - PASS
Enable/Disable Agent 功能测试 - PASS
结构化输出验证 - PARTIAL
已安装 Agent 列表查询 - PASS
```

### 1.3 测试覆盖率评估

#### 已覆盖的模块

| 模块 | 覆盖率估算 | 说明 |
|------|-----------|------|
| Agent Gateway | ~60% | 调用契约和执行边界有覆盖 |
| Agent Market API | ~50% | 注册/安装/卸载有覆盖 |
| Executor Router | ~40% | 基本路由逻辑有测试 |
| Error Handling | ~70% | 主要错误码有验证 |

#### 未覆盖的模块 (测试盲区)

| 模块 | 风险等级 | 建议优先级 |
|------|---------|-----------|
| Projects API | **HIGH** | P0 |
| Deployments API | **HIGH** | P0 |
| CI/CD Integration | **HIGH** | P0 |
| WebSocket Manager | **MEDIUM** | P1 |
| Kubeconfig API | **MEDIUM** | P1 |
| Integrations API | **MEDIUM** | P1 |
| Database Models | **MEDIUM** | P1 |
| Authentication/Authorization | **HIGH** | P0 |
| Frontend Components | **CRITICAL** | P0 |

---

## 2. 测试框架评估

### 2.1 当前使用的测试工具

#### 后端测试栈

```
- pytest (测试框架)
- FastAPI TestClient (HTTP 测试)
- Pydantic (数据验证)
- SQLAlchemy (数据库 ORM)
- httpx (HTTP 客户端，用于 Mock Remote Executor)
```

#### 依赖分析

```python
# backend/requirements.txt 中缺失的测试依赖
pytest-asyncio    # 异步测试支持 (当前通过 asyncio.run 变通)
pytest-cov        # 覆盖率报告
pytest-mock       # Mock 工具
faker             # 测试数据生成
freezegun         # 时间 Mock
```

### 2.2 测试配置评估

#### 缺失的配置文件

| 文件 | 状态 | 建议 |
|------|------|------|
| `pytest.ini` | **缺失** | 需要创建 |
| `conftest.py` | **缺失** | 需要创建 (共享 fixtures) |
| `.coveragerc` | **缺失** | 需要创建 |
| `tox.ini` | **缺失** | 可选 (多环境测试) |

#### 建议的 pytest.ini 配置

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks integration tests
    e2e: marks end-to-end tests
    unit: marks unit tests
filterwarnings =
    ignore::DeprecationWarning
```

#### 建议的 conftest.py

```python
"""
NexusOps Backend - Test Configuration
"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "name": "Test Project",
        "description": "A test project",
        "git_repo": "https://github.com/test/test.git"
    }


@pytest.fixture
def sample_version_data():
    """示例版本数据"""
    return {
        "codename": "Phoenix",
        "version": "1.0.0",
        "git_branch": "main",
        "git_commit": "abc123"
    }
```

### 2.3 前端测试现状

#### 当前状态: **无测试**

前端 `frontend/` 目录下没有任何测试文件。package.json 中也没有测试脚本配置。

#### 缺失的前端测试工具

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "jsdom": "^24.0.0",
    "msw": "^2.0.0"
  }
}
```

#### 建议的 vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

---

## 3. 质量风险评估

### 3.1 高风险模块识别

#### Critical Risk (必须立即测试)

| 模块 | 风险描述 | 影响 |
|------|---------|------|
| **Authentication** | 无认证测试，Demo 模式跳过认证 | 安全漏洞 |
| **Projects API** | 核心业务逻辑无测试 | 数据损坏风险 |
| **Deployments API** | 部署操作无测试 | 生产事故风险 |
| **RBAC** | 权限控制无测试 | 越权访问风险 |

#### High Risk (需要优先测试)

| 模块 | 风险描述 | 影响 |
|------|---------|------|
| **WebSocket Manager** | 连接管理无测试 | 消息丢失/连接泄漏 |
| **Agent Executor** | 远程执行异常处理不完整 | 服务不可用 |
| **Database Transactions** | 无事务回滚测试 | 数据不一致 |

#### Medium Risk (需要测试)

| 模块 | 风险描述 | 影响 |
|------|---------|------|
| **Version Management** | 版本状态转换无测试 | 状态混乱 |
| **CI/CD Integration** | 外部集成无 Mock | 集成失败 |
| **Frontend Forms** | 表单验证无测试 | 数据验证遗漏 |

### 3.2 安全测试需求

#### 认证与授权测试

```python
class TestAuthentication:
    """认证安全测试"""

    def test_missing_token_returns_401(self, client):
        """缺少 Token 返回 401"""
        pass

    def test_invalid_token_returns_401(self, client):
        """无效 Token 返回 401"""
        pass

    def test_expired_token_returns_401(self, client):
        """过期 Token 返回 401"""
        pass

    def test_token_tampering_detected(self, client):
        """Token 篡改检测"""
        pass

    def test_csrf_protection_enabled(self, client):
        """CSRF 保护启用"""
        pass


class TestAuthorization:
    """授权测试"""

    def test_non_admin_cannot_approve_deployment(self, client, regular_user):
        """非管理员不能批准部署"""
        pass

    def test_user_can_only_access_own_projects(self, client, regular_user):
        """用户只能访问自己的项目"""
        pass

    def test_cross_tenant_isolation(self, client, tenant_a_user, tenant_b_data):
        """跨租户隔离"""
        pass

    def test_project_permission_inheritance(self, client):
        """项目权限继承"""
        pass
```

#### 输入验证测试

```python
class TestInputValidation:
    """输入验证安全测试"""

    def test_sql_injection_prevention(self, client):
        """SQL 注入防护"""
        malicious_inputs = [
            "'; DROP TABLE projects; --",
            "' OR '1'='1",
            "1; DELETE FROM users WHERE 1=1",
        ]
        for payload in malicious_inputs:
            resp = client.get(f"/api/v1/projects?name={payload}")
            assert resp.status_code not in [200, 500]

    def test_xss_prevention(self, client):
        """XSS 防护"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        for payload in xss_payloads:
            resp = client.post("/api/v1/projects", json={
                "name": payload,
                "description": payload
            })
            # 验证响应不包含可执行的脚本
            assert "<script>" not in resp.text

    def test_path_traversal_prevention(self, client):
        """路径遍历防护"""
        pass

    def test_command_injection_prevention(self, client):
        """命令注入防护"""
        pass
```

### 3.3 性能测试需求

#### API 响应时间测试

```python
class TestPerformance:
    """性能测试"""

    @pytest.mark.slow
    def test_projects_list_response_time(self, client, hundred_projects):
        """项目列表响应时间 < 200ms"""
        import time
        start = time.time()
        resp = client.get("/api/v1/projects")
        elapsed = (time.time() - start) * 1000
        assert resp.status_code == 200
        assert elapsed < 200, f"Response time {elapsed}ms exceeds 200ms"

    @pytest.mark.slow
    def test_agent_invoke_response_time(self, client):
        """Agent 调用响应时间 < 5s"""
        pass

    @pytest.mark.slow
    def test_concurrent_requests_handling(self, client):
        """并发请求处理"""
        import asyncio
        async def make_request():
            async with AsyncClient(app=app) as ac:
                return await ac.get("/api/v1/projects")

        results = asyncio.run(
            asyncio.gather(*[make_request() for _ in range(50)])
        )
        assert all(r.status_code == 200 for r in results)
```

#### 负载测试建议 (使用 Locust)

```python
# locustfile.py
from locust import HttpUser, task, between

class NexusOpsUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_projects(self):
        self.client.get("/api/v1/projects")

    @task(1)
    def invoke_agent(self):
        self.client.post("/api/v1/agents/nexusops.chat/invoke", json={
            "request_id": "test-req",
            "conversation_id": "test-conv",
            "agent_id": "nexusops.chat",
            "query": "What is the status?"
        })
```

---

## 4. E2E 测试规划

### 4.1 关键用户旅程

#### Journey 1: 项目管理完整流程

```
1. 用户登录
2. 创建新项目
3. 添加 Service
4. 创建新版本
5. 部署到测试环境
6. 查看部署状态
7. 请求生产部署
8. 管理员审批
9. 部署到生产环境
```

#### Journey 2: Agent 市场交互

```
1. 浏览 Agent 市场
2. 查看第三方 Agent 详情
3. 安装 Agent
4. 调用 Agent
5. 查看调用历史
6. 卸载 Agent
```

#### Journey 3: 告警处理流程

```
1. 接收告警通知
2. 查看告警详情
3. 使用 AI 助手分析
4. 创建工单
5. 处理告警
6. 关闭告警
```

### 4.2 Playwright 测试用例设计

#### 安装配置

```bash
npm install -D @playwright/test
npx playwright install
```

#### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### 测试用例示例: e2e/project-management.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Project Management', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.fill('[name="username"]', 'admin');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should create a new project', async ({ page }) => {
    // 导航到项目页面
    await page.goto('/projects');

    // 点击新建项目按钮
    await page.click('button:has-text("New Project")');

    // 填写表单
    await page.fill('[name="name"]', 'E2E Test Project');
    await page.fill('[name="code"]', 'e2e-test-project');
    await page.fill('[name="owner"]', 'Test Team');
    await page.fill('[name="description"]', 'Created by E2E test');

    // 提交
    await page.click('button:has-text("OK")');

    // 验证创建成功
    await expect(page.locator('text=E2E Test Project')).toBeVisible();
  });

  test('should create version and deploy to test', async ({ page }) => {
    await page.goto('/projects');

    // 选择项目
    await page.click('text=Test Project');

    // 点击创建版本
    await page.click('button:has-text("Create Version")');

    // 填写版本信息
    await page.fill('[name="codename"]', 'Phoenix');
    await page.fill('[name="imageUrl"]', 'harbor.local/test:v1');

    // 选择部署区域
    await page.click('.ant-select-selector');
    await page.click('text=US-East');

    // 提交
    await page.click('button:has-text("Create & Deploy")');

    // 等待部署进度
    await expect(page.locator('text=Deployment Successful')).toBeVisible({
      timeout: 60000
    });
  });

  test('should handle production deployment request flow', async ({ page }) => {
    await page.goto('/projects');

    // 找到测试版本
    await page.click('text=Phoenix');

    // 请求生产部署
    await page.click('button:has-text("Request Prod")');

    // 填写发布说明
    await page.fill('[name="changeSummary"]', 'Bug fixes and performance improvements');
    await page.fill('[name="testResults"]', 'All tests passed');

    // 选择生产区域
    await page.click('text=Production Regions');
    await page.click('text=US-West');

    // 提交请求
    await page.click('button:has-text("Submit Request")');

    // 验证请求已提交
    await expect(page.locator('text=Waiting for Admin approval')).toBeVisible();
  });
});
```

#### 测试用例示例: e2e/agent-market.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Agent Market', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agent-store');
  });

  test('should display available agents', async ({ page }) => {
    // 验证内置 Agent 显示
    await expect(page.locator('text=AI Assistant')).toBeVisible();
    await expect(page.locator('text=DNS Operations Agent')).toBeVisible();
    await expect(page.locator('text=Kubernetes Agent')).toBeVisible();
  });

  test('should install and invoke third-party agent', async ({ page }) => {
    // 找到第三方 Agent
    await page.click('text=Weather Agent');

    // 安装
    await page.click('button:has-text("Install")');
    await expect(page.locator('text=Installed')).toBeVisible();

    // 导航到 AI 助手
    await page.goto('/ai-assistant');

    // 调用 Agent
    await page.fill('[placeholder="Ask anything..."]', 'What is the weather in Tokyo?');
    await page.press('[placeholder="Ask anything..."]', 'Enter');

    // 验证响应
    await expect(page.locator('.agent-response')).toBeVisible({ timeout: 30000 });
  });
});
```

### 4.3 测试环境需求

#### 环境配置

| 环境 | 用途 | 配置要求 |
|------|------|---------|
| Development | 本地开发测试 | Docker Compose + SQLite |
| CI | 自动化测试 | GitHub Actions + PostgreSQL |
| Staging | E2E 测试 | Kubernetes + 生产级配置 |

#### 测试数据管理

```yaml
# docker/docker-compose.test.yml
version: '3.8'
services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: nexusops_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

  redis-test:
    image: redis:7
    ports:
      - "6380:6379"
    tmpfs:
      - /data
```

---

## 5. 测试策略建议

### 5.1 单元测试计划

#### 目标覆盖率

| 层级 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| Models | 90% | 0% |
| Services | 80% | 0% |
| API Routes | 70% | ~30% |
| Utils | 95% | 0% |

#### 后端单元测试结构

```
backend/tests/
├── conftest.py              # 共享 fixtures
├── pytest.ini               # pytest 配置
├── unit/
│   ├── models/
│   │   ├── test_schemas.py
│   │   └── test_database.py
│   ├── services/
│   │   ├── test_cicd.py
│   │   └── test_json_output.py
│   ├── gateway/
│   │   ├── test_executor_router.py
│   │   ├── test_builtin_executor.py
│   │   └── test_remote_executor.py
│   └── utils/
│       └── test_helpers.py
├── integration/
│   ├── test_projects_api.py
│   ├── test_deployments_api.py
│   ├── test_agents_api.py
│   └── test_market_api.py
└── e2e/
    └── test_full_flow.py
```

#### 前端单元测试结构

```
frontend/src/
├── __tests__/
│   ├── setup.ts
│   ├── components/
│   │   ├── MainLayout.test.tsx
│   │   ├── ResourceChatPanel.test.tsx
│   │   └── AgentResponseRenderer.test.tsx
│   ├── pages/
│   │   ├── Projects.test.tsx
│   │   ├── Dashboard.test.tsx
│   │   └── AgentStore.test.tsx
│   ├── stores/
│   │   ├── authStore.test.ts
│   │   ├── projectStore.test.ts
│   │   └── versionStore.test.ts
│   └── hooks/
│       └── useWebSocket.test.ts
```

#### 示例单元测试: test_projects_api.py

```python
"""
Projects API Unit Tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Project


class TestProjectsAPI:
    """Projects API 测试类"""

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, client: AsyncClient):
        """测试空项目列表"""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_project_success(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试创建项目成功"""
        response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_project_data["name"]
        assert data["status"] == "active"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_project_duplicate_name(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        sample_project_data: dict
    ):
        """测试创建重复名称项目"""
        # 创建第一个项目
        await client.post("/api/v1/projects", json=sample_project_data)

        # 尝试创建同名项目
        response = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """测试获取不存在的项目"""
        response = await client.get("/api/v1/projects/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试更新项目"""
        # 创建项目
        create_resp = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_resp.json()["id"]

        # 更新项目
        update_resp = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated description"}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_project(
        self,
        client: AsyncClient,
        sample_project_data: dict
    ):
        """测试删除项目"""
        # 创建项目
        create_resp = await client.post(
            "/api/v1/projects",
            json=sample_project_data
        )
        project_id = create_resp.json()["id"]

        # 删除项目
        delete_resp = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_resp.status_code == 204

        # 验证已删除
        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize("page,page_size,expected", [
        (1, 10, 10),
        (2, 10, 5),
        (1, 20, 15),
    ])
    async def test_pagination(
        self,
        client: AsyncClient,
        page: int,
        page_size: int,
        expected: int
    ):
        """测试分页"""
        # 创建 15 个项目
        for i in range(15):
            await client.post(
                "/api/v1/projects",
                json={
                    "name": f"Project {i}",
                    "description": f"Description {i}"
                }
            )

        response = await client.get(
            f"/api/v1/projects?page={page}&page_size={page_size}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == expected
        assert data["total"] == 15
```

### 5.2 集成测试计划

#### 集成测试重点

```python
class TestIntegration:
    """集成测试"""

    @pytest.mark.integration
    async def test_full_deployment_flow(self, client, db_session):
        """完整部署流程测试"""
        # 1. 创建项目
        project_resp = await client.post("/api/v1/projects", json={...})
        project_id = project_resp.json()["id"]

        # 2. 创建版本
        version_resp = await client.post(
            f"/api/v1/projects/{project_id}/versions",
            json={...}
        )
        version_id = version_resp.json()["id"]

        # 3. 创建部署
        deploy_resp = await client.post(
            "/api/v1/deployments",
            json={"version_id": version_id, "region": "us-east"}
        )
        deployment_id = deploy_resp.json()["id"]

        # 4. 验证部署状态
        status_resp = await client.get(f"/api/v1/deployments/{deployment_id}")
        assert status_resp.json()["status"] in ["pending", "running"]

    @pytest.mark.integration
    async def test_agent_market_to_invoke_flow(self, client):
        """Agent 市场到调用流程"""
        # 1. 注册 Agent
        # 2. 安装 Agent
        # 3. 调用 Agent
        # 4. 验证结果
        pass
```

### 5.3 E2E 测试计划

#### 测试场景矩阵

| 场景 | 优先级 | 测试类型 | 预计时间 |
|------|--------|---------|---------|
| 用户登录/登出 | P0 | E2E | 2min |
| 项目 CRUD | P0 | E2E | 5min |
| 版本创建和部署 | P0 | E2E | 10min |
| 生产部署审批 | P1 | E2E | 5min |
| Agent 安装和调用 | P1 | E2E | 5min |
| 告警处理 | P2 | E2E | 5min |
| WebSocket 连接 | P2 | E2E | 3min |

### 5.4 CI/CD 集成方案

#### GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: nexusops_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/nexusops_test
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/nexusops_test
        run: |
          cd backend
          pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run linting
        run: |
          cd frontend
          npm run lint

      - name: Run unit tests
        run: |
          cd frontend
          npm run test:unit

      - name: Build
        run: |
          cd frontend
          npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: nexusops_e2e
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Playwright
        run: |
          npm install -D @playwright/test
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          npx playwright test
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/nexusops_e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

---

## 6. 质量门禁定义

### 6.1 发布前检查清单

#### Code Quality Gate

- [ ] **代码覆盖率**: 后端 >= 70%, 前端 >= 60%
- [ ] **Linter 检查**: 0 errors, 0 warnings
- [ ] **类型检查**: mypy/tsc 无错误
- [ ] **安全扫描**: 无高危/严重漏洞
- [ ] **依赖审计**: 无已知漏洞依赖

#### Test Quality Gate

- [ ] **单元测试**: 100% 通过
- [ ] **集成测试**: 100% 通过
- [ ] **E2E 测试**: 100% 通过 (关键路径)
- [ ] **性能测试**: API 响应 < 200ms (P95)
- [ ] **安全测试**: 无认证/授权漏洞

#### Documentation Gate

- [ ] **API 文档**: OpenAPI 规范完整
- [ ] **README 更新**: 安装/运行说明准确
- [ ] **CHANGELOG 更新**: 变更记录完整

### 6.2 Definition of Done (DoD)

根据 `agentic_pact/PACT.md` 定义的 DoD:

```markdown
## Definition of Done

A task is complete only when:

- [ ] The implementation matches the spec
- [ ] Tests and required checks are done
- [ ] Evidence is recorded
- [ ] The task is marked pass in Task List
- [ ] The session is summarized
- [ ] The lock is released

### Additional DoD for NexusOps:

- [ ] All new code has corresponding tests
- [ ] Code review approved by at least one reviewer
- [ ] CI pipeline passes (lint, test, build)
- [ ] No regression in existing tests
- [ ] Performance benchmarks within acceptable range
- [ ] Security review for auth/data handling changes
- [ ] Documentation updated for API changes
```

### 6.3 自动化验收标准

#### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest (fast tests only)
        entry: bash -c 'cd backend && pytest tests/unit -m "not slow" -x'
        language: system
        pass_filenames: false
        always_run: true
```

#### Quality Gates Script

```bash
#!/bin/bash
# scripts/quality-gate.sh

set -e

echo "=== Running Quality Gates ==="

# 1. Linting
echo "1. Running linters..."
make lint

# 2. Unit tests with coverage
echo "2. Running unit tests..."
cd backend && pytest tests/unit -v --cov=app --cov-fail-under=70

# 3. Integration tests
echo "3. Running integration tests..."
pytest tests/integration -v

# 4. Security scan
echo "4. Running security scan..."
pip install safety
safety check --full-report

# 5. Frontend tests
echo "5. Running frontend tests..."
cd ../frontend && npm run test:unit

# 6. Build check
echo "6. Running build check..."
npm run build

echo "=== All Quality Gates Passed ==="
```

---

## 7. 行动计划

### Phase 1: 基础设施 (Week 1-2)

1. 创建测试配置文件 (pytest.ini, conftest.py, vitest.config.ts)
2. 配置 CI/CD 流水线
3. 设置测试数据库环境
4. 安装测试依赖

### Phase 2: 单元测试 (Week 2-4)

1. 编写 Models 单元测试
2. 编写 Services 单元测试
3. 编写 Gateway 单元测试
4. 编写前端组件测试
5. 编写 Store 测试

### Phase 3: 集成测试 (Week 4-6)

1. Projects API 集成测试
2. Deployments API 集成测试
3. Agent Market 集成测试
4. WebSocket 集成测试

### Phase 4: E2E 测试 (Week 6-8)

1. 配置 Playwright
2. 编写关键用户旅程测试
3. 配置 E2E 测试环境
4. 集成到 CI/CD

### Phase 5: 质量门禁 (Week 8-10)

1. 配置 pre-commit hooks
2. 设置覆盖率目标
3. 配置安全扫描
4. 文档化 DoD

---

## 8. 总结

### 当前测试成熟度评估

| 维度 | 评分 (1-5) | 说明 |
|------|-----------|------|
| 测试覆盖率 | 2 | 后端 ~30%, 前端 0% |
| 测试质量 | 3 | 现有测试结构良好 |
| 测试自动化 | 2 | 有基础但未集成 CI |
| 测试文档 | 1 | 缺乏测试文档 |
| 安全测试 | 1 | 几乎没有 |
| E2E 测试 | 1 | 完全缺失 |

### 优先行动项

1. **立即**: 配置 CI/CD 测试流水线
2. **本周**: 创建 Projects API 测试
3. **本月**: 建立前端测试框架
4. **下月**: 完成 E2E 测试基础设施

---

**报告生成时间**: 2026-02-25
**下次评审时间**: 建议 4 周后
