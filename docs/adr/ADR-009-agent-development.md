# ADR-009: Agent 调试与开发体验

## 状态
已接受 (2024-02-16)

## 背景

开发者需要良好的工具来：
- 本地开发和测试 Agent
- 调试 Agent 行为
- 模拟 Agent 间调用
- 查看日志和追踪
- 验证输出格式

当前缺乏：
- 本地开发环境
- 调试工具
- 测试框架
- 模拟器

## 选项

### 选项 A: 完整 SDK + 本地模拟器（推荐）
- 提供完整开发 SDK
- 本地模拟 NexusOps 环境
- 支持断点调试
- 集成测试框架

**优点**：
- 完整的开发体验
- 快速迭代
- 可靠的测试

**缺点**：
- SDK 维护成本

### 选项 B: 仅在线开发
- 只能在 NexusOps 环境中开发

**优点**：
- 无需本地环境

**缺点**：
- 开发效率低
- 无法本地调试

### 选项 C: 第三方工具集成
- 使用现有工具（如 LangChain）

**优点**：
- 生态丰富

**缺点**：
- 不够定制化

## 决策

**采用选项 A：完整 SDK + 本地模拟器**

## 详细设计

### 1. Agent 开发 SDK

```python
# nexusops-agent-sdk/python/nexusops_agent/__init__.py

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import httpx
import asyncio

class AgentContext:
    """Agent 执行上下文"""
    def __init__(
        self,
        agent_id: str,
        conversation_id: str,
        user_id: str,
        tenant_id: str,
        project_id: Optional[str] = None,
        **kwargs
    ):
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.metadata = kwargs

class AgentTool:
    """Agent 工具定义"""
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: callable
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    async def execute(self, **kwargs) -> Any:
        return await self.handler(**kwargs)

class AgentResponse:
    """Agent 响应"""
    def __init__(
        self,
        content: str,
        structured_output: Optional[Dict] = None,
        suggested_actions: Optional[List[Dict]] = None,
        related_resources: Optional[List[Dict]] = None,
        metadata: Optional[Dict] = None
    ):
        self.content = content
        self.structured_output = structured_output
        self.suggested_actions = suggested_actions or []
        self.related_resources = related_resources or []
        self.metadata = metadata or {}

class BaseAgent:
    """Agent 基类"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str,
        description: str = ""
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.description = description
        self.tools: List[AgentTool] = []
        self._llm_client = None

    def tool(self, name: str, description: str, parameters: Dict):
        """装饰器：注册工具"""
        def decorator(func):
            tool = AgentTool(name, description, parameters, func)
            self.tools.append(tool)
            return func
        return decorator

    async def invoke(self, query: str, context: AgentContext) -> AgentResponse:
        """主入口：处理用户查询"""
        raise NotImplementedError("Subclasses must implement invoke()")

    def get_manifest(self) -> Dict:
        """获取 Agent 清单"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
                for t in self.tools
            ]
        }

    # A2A 通信
    async def call_agent(
        self,
        agent_id: str,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """调用其他 Agent"""
        # 实现通过 A2A 协议调用
        pass

    # 状态管理
    async def get_state(self, key: str, context: AgentContext) -> Optional[Any]:
        """获取状态"""
        pass

    async def set_state(
        self,
        key: str,
        value: Any,
        context: AgentContext,
        expires_in: Optional[int] = None
    ):
        """设置状态"""
        pass

    # 日志
    def log(self, level: str, message: str, **kwargs):
        """记录日志"""
        import logging
        logger = logging.getLogger(self.agent_id)
        getattr(logger, level)(message, extra=kwargs)


# 使用示例
class DNSAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="com.nexusops.agents.dns",
            name="DNS Operations Agent",
            version="1.0.0"
        )
        self.cloudflare_client = None

    @tool(
        name="create_dns_record",
        description="Create a DNS record",
        parameters={
            "type": "object",
            "properties": {
                "zone_id": {"type": "string"},
                "record_type": {"type": "string", "enum": ["A", "AAAA", "CNAME", "MX", "TXT"]},
                "name": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["zone_id", "record_type", "name", "content"]
        }
    )
    async def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 3600
    ) -> Dict:
        """创建 DNS 记录"""
        # 调用 Cloudflare API
        result = await self.cloudflare_client.create_record(
            zone_id=zone_id,
            type=record_type,
            name=name,
            content=content,
            ttl=ttl
        )
        return result

    async def invoke(self, query: str, context: AgentContext) -> AgentResponse:
        # 解析用户意图
        # 调用相应的工具
        # 返回响应
        pass
```

### 2. 本地模拟器

```python
# nexusops-agent-sdk/python/nexusops_agent/simulator.py

from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime

class MockCredentialStore:
    """模拟凭证存储"""
    def __init__(self):
        self._credentials: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._credentials[key] = value

    def get(self, key: str) -> Optional[Any]:
        return self._credentials.get(key)

    def load_from_env(self):
        """从环境变量加载凭证"""
        import os
        for key, value in os.environ.items():
            if key.startswith('NEXUSOPS_CRED_'):
                cred_key = key.replace('NEXUSOPS_CRED_', '').lower()
                self._credentials[cred_key] = value

class MockStateStore:
    """模拟状态存储"""
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}

    async def get(self, agent_id: str, conversation_id: str, key: str) -> Optional[Any]:
        store_key = f"{agent_id}:{conversation_id}"
        return self._states.get(store_key, {}).get(key)

    async def set(
        self,
        agent_id: str,
        conversation_id: str,
        key: str,
        value: Any,
        expires_in: Optional[int] = None
    ):
        store_key = f"{agent_id}:{conversation_id}"
        if store_key not in self._states:
            self._states[store_key] = {}
        self._states[store_key][key] = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_in
        }

class MockAgentRegistry:
    """模拟 Agent 注册表"""
    def __init__(self):
        self._agents: Dict[str, Any] = {}

    def register(self, agent: 'BaseAgent'):
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> Optional['BaseAgent']:
        return self._agents.get(agent_id)

    def list_all(self) -> List[str]:
        return list(self._agents.keys())

class LocalSimulator:
    """本地模拟器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.credentials = MockCredentialStore()
        self.states = MockStateStore()
        self.registry = MockAgentRegistry()
        self._setup_complete = False

    def setup(self):
        """初始化模拟器"""
        # 加载凭证
        self.credentials.load_from_env()

        # 加载配置
        self._load_config()

        self._setup_complete = True

    def _load_config(self):
        """从文件加载配置"""
        import os
        config_path = os.environ.get(
            'NEXUSOPS_CONFIG',
            './nexusops.yaml'
        )

        if os.path.exists(config_path):
            import yaml
            with open(config_path) as f:
                self.config.update(yaml.safe_load(f))

    def register_agent(self, agent: 'BaseAgent'):
        """注册 Agent"""
        self.registry.register(agent)

    async def invoke(
        self,
        agent_id: str,
        query: str,
        context: Optional[AgentContext] = None
    ) -> AgentResponse:
        """调用 Agent"""
        if not self._setup_complete:
            self.setup()

        agent = self.registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # 创建默认上下文
        if context is None:
            context = AgentContext(
                agent_id=agent_id,
                conversation_id="local-test",
                user_id="developer",
                tenant_id="local"
            )

        # 注入模拟服务
        agent.credentials = self.credentials
        agent.states = self.states

        # 调用 Agent
        response = await agent.invoke(query, context)

        return response

    async def call_agent(
        self,
        from_agent_id: str,
        to_agent_id: str,
        query: str,
        context: AgentContext
    ) -> AgentResponse:
        """模拟 Agent 间调用"""
        # 记录调用日志
        print(f"[A2A] {from_agent_id} -> {to_agent_id}: {query}")

        # 调用目标 Agent
        return await self.invoke(to_agent_id, query, context)

    def create_test_context(self, **kwargs) -> AgentContext:
        """创建测试上下文"""
        return AgentContext(
            agent_id=kwargs.get('agent_id', 'test-agent'),
            conversation_id=kwargs.get('conversation_id', 'test-conversation'),
            user_id=kwargs.get('user_id', 'test-user'),
            tenant_id=kwargs.get('tenant_id', 'test-tenant'),
            project_id=kwargs.get('project_id'),
            **{k: v for k, v in kwargs.items() if k not in [
                'agent_id', 'conversation_id', 'user_id', 'tenant_id', 'project_id'
            ]}
        )

# 便捷函数
def create_simulator(config: Optional[Dict] = None) -> LocalSimulator:
    """创建模拟器实例"""
    simulator = LocalSimulator(config)
    simulator.setup()
    return simulator
```

### 3. 测试框架

```python
# nexusops-agent-sdk/python/nexusops_agent/testing.py

import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import json

@dataclass
class TestCase:
    """测试用例"""
    name: str
    description: str
    input_query: str
    expected_output: Optional[Dict] = None
    expected_tools: Optional[List[str]] = None
    expected_actions: Optional[List[str]] = None
    context_overrides: Optional[Dict] = None
    mock_responses: Optional[Dict[str, Any]] = None

class AgentTestRunner:
    """Agent 测试运行器"""

    def __init__(self, simulator: 'LocalSimulator'):
        self.simulator = simulator
        self.results: List[Dict] = []
        self._mock_handlers: Dict[str, Callable] = {}

    def mock_tool(self, tool_name: str, handler: Callable):
        """模拟工具响应"""
        self._mock_handlers[tool_name] = handler

    def mock_agent(self, agent_id: str, handler: Callable):
        """模拟其他 Agent 响应"""
        self._mock_handlers[f"agent:{agent_id}"] = handler

    async def run_test(self, agent_id: str, test_case: TestCase) -> Dict:
        """运行单个测试"""
        # 创建上下文
        context = self.simulator.create_test_context(
            agent_id=agent_id,
            **(test_case.context_overrides or {})
        )

        # 设置模拟响应
        if test_case.mock_responses:
            for key, value in test_case.mock_responses.items():
                self.simulator.credentials.set(key, value)

        # 执行测试
        try:
            start_time = asyncio.get_event_loop().time()
            response = await self.simulator.invoke(
                agent_id,
                test_case.input_query,
                context
            )
            end_time = asyncio.get_event_loop().time()

            result = {
                "name": test_case.name,
                "passed": True,
                "duration_ms": (end_time - start_time) * 1000,
                "response": {
                    "content": response.content,
                    "structured_output": response.structured_output,
                    "suggested_actions": [a.get('type') for a in response.suggested_actions],
                },
                "error": None
            }

            # 验证期望
            if test_case.expected_output:
                self._validate_output(response, test_case.expected_output, result)

            if test_case.expected_tools:
                # 检查是否调用了期望的工具
                pass

            if test_case.expected_actions:
                self._validate_actions(response, test_case.expected_actions, result)

        except Exception as e:
            result = {
                "name": test_case.name,
                "passed": False,
                "duration_ms": 0,
                "response": None,
                "error": str(e)
            }

        self.results.append(result)
        return result

    async def run_tests(self, agent_id: str, test_cases: List[TestCase]) -> Dict:
        """运行多个测试"""
        for test_case in test_cases:
            await self.run_test(agent_id, test_case)

        return self.get_summary()

    def get_summary(self) -> Dict:
        """获取测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "results": self.results
        }

    def _validate_output(self, response, expected, result):
        """验证输出"""
        if expected.get('content_contains'):
            for text in expected['content_contains']:
                if text not in response.content:
                    result['passed'] = False
                    result['error'] = f"Expected content '{text}' not found"

        if expected.get('structured_output'):
            for key, value in expected['structured_output'].items():
                if response.structured_output.get(key) != value:
                    result['passed'] = False
                    result['error'] = f"Structured output mismatch: {key}"

    def _validate_actions(self, response, expected_actions, result):
        """验证建议操作"""
        actual_actions = [a.get('type') for a in response.suggested_actions]
        for action in expected_actions:
            if action not in actual_actions:
                result['passed'] = False
                result['error'] = f"Expected action '{action}' not found"

# 测试装饰器
def agent_test(name: str, **kwargs):
    """测试用例装饰器"""
    def decorator(func):
        func._test_case = TestCase(
            name=name,
            description=kwargs.get('description', func.__doc__ or ''),
            input_query=kwargs.get('input_query', ''),
            expected_output=kwargs.get('expected_output'),
            expected_tools=kwargs.get('expected_tools'),
            expected_actions=kwargs.get('expected_actions'),
            context_overrides=kwargs.get('context_overrides'),
            mock_responses=kwargs.get('mock_responses'),
        )
        return func
    return decorator

# 使用示例
class DNSAgentTests:
    @agent_test(
        name="Create DNS Record",
        description="Test creating a DNS record",
        input_query="Create an A record for test.example.com pointing to 1.2.3.4",
        expected_output={
            'content_contains': ['DNS record', 'created'],
        },
        expected_actions=['navigate'],
    )
    async def test_create_record(self, runner: AgentTestRunner, agent_id: str):
        pass

    @agent_test(
        name="Generate Random Subdomain",
        description="Test generating a random subdomain",
        input_query="Generate a random 4-level subdomain for test.example.com",
        expected_output={
            'content_contains': ['subdomain', 'test.example.com'],
        },
    )
    async def test_generate_subdomain(self, runner: AgentTestRunner, agent_id: str):
        pass

# 运行测试
async def run_all_tests():
    simulator = create_simulator()
    agent = DNSAgent()
    simulator.register_agent(agent)

    runner = AgentTestRunner(simulator)

    tests = DNSAgentTests()
    test_cases = [
        tests.test_create_record._test_case,
        tests.test_generate_subdomain._test_case,
    ]

    results = await runner.run_tests(agent.agent_id, test_cases)
    print(json.dumps(results, indent=2))
```

### 4. 调试工具

```python
# nexusops-agent-sdk/python/nexusops_agent/debugger.py

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

class AgentDebugger:
    """Agent 调试器"""

    def __init__(self, simulator: 'LocalSimulator'):
        self.simulator = simulator
        self.breakpoints: Dict[str, List[str]] = {}  # agent_id -> [tool_names]
        self.call_stack: List[Dict] = []
        self.logs: List[Dict] = []
        self._step_mode = False
        self._paused = False

    def set_breakpoint(self, agent_id: str, tool_name: Optional[str] = None):
        """设置断点"""
        if agent_id not in self.breakpoints:
            self.breakpoints[agent_id] = []
        if tool_name:
            self.breakpoints[agent_id].append(tool_name)

    def remove_breakpoint(self, agent_id: str, tool_name: Optional[str] = None):
        """移除断点"""
        if tool_name and agent_id in self.breakpoints:
            self.breakpoints[agent_id] = [
                t for t in self.breakpoints[agent_id] if t != tool_name
            ]
        elif agent_id in self.breakpoints:
            del self.breakpoints[agent_id]

    def enable_step_mode(self):
        """启用单步模式"""
        self._step_mode = True

    def disable_step_mode(self):
        """禁用单步模式"""
        self._step_mode = False

    async def step(self):
        """单步执行"""
        self._paused = False

    async def continue_execution(self):
        """继续执行"""
        self._paused = False
        self._step_mode = False

    async def check_breakpoint(self, agent_id: str, tool_name: str, params: Dict):
        """检查断点"""
        should_break = False

        # 检查 Agent 级别断点
        if agent_id in self.breakpoints:
            if not self.breakpoints[agent_id] or tool_name in self.breakpoints[agent_id]:
                should_break = True

        # 单步模式
        if self._step_mode:
            should_break = True

        if should_break:
            self._paused = True
            self.log_event('breakpoint', {
                'agent_id': agent_id,
                'tool_name': tool_name,
                'params': params,
                'call_stack': self.call_stack.copy()
            })

            # 等待用户操作
            while self._paused:
                await asyncio.sleep(0.1)

    def log_event(self, event_type: str, data: Dict):
        """记录事件"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data
        })

    def push_call(self, agent_id: str, query: str):
        """压入调用栈"""
        self.call_stack.append({
            'agent_id': agent_id,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        self.log_event('call', {
            'agent_id': agent_id,
            'query': query,
            'depth': len(self.call_stack)
        })

    def pop_call(self, agent_id: str, response: Any):
        """弹出调用栈"""
        if self.call_stack:
            call = self.call_stack.pop()
            self.log_event('return', {
                'agent_id': agent_id,
                'response': str(response)[:500]  # 截断长响应
            })

    def get_logs(self, filter_type: Optional[str] = None) -> List[Dict]:
        """获取日志"""
        if filter_type:
            return [l for l in self.logs if l['type'] == filter_type]
        return self.logs

    def export_trace(self) -> str:
        """导出追踪信息"""
        return json.dumps({
            'logs': self.logs,
            'call_stack': self.call_stack
        }, indent=2, default=str)

    def print_call_tree(self):
        """打印调用树"""
        indent = '  '
        for log in self.logs:
            if log['type'] == 'call':
                depth = log['data'].get('depth', 1)
                print(f"{indent * (depth - 1)}├─ {log['data']['agent_id']}: {log['data']['query'][:50]}")

    # 交互式调试
    async def interactive_debug(self, agent_id: str, query: str):
        """交互式调试会话"""
        print(f"\n🐛 Starting debug session for {agent_id}")
        print(f"Query: {query}")
        print("Commands: (s)tep, (c)ontinue, (b)reakpoints, (l)ogs, (q)uit\n")

        self.enable_step_mode()

        # 启动调用
        task = asyncio.create_task(
            self._debug_invoke(agent_id, query)
        )

        # 处理用户输入
        while not task.done():
            if self._paused:
                cmd = input("debug> ").strip().lower()

                if cmd == 's':
                    await self.step()
                elif cmd == 'c':
                    await self.continue_execution()
                elif cmd == 'b':
                    print("Breakpoints:", self.breakpoints)
                elif cmd == 'l':
                    for log in self.logs[-10:]:
                        print(f"  {log['type']}: {log['data']}")
                elif cmd == 'q':
                    task.cancel()
                    break

            await asyncio.sleep(0.1)

        try:
            result = task.result()
            print("\n✅ Debug session complete")
            self.print_call_tree()
            return result
        except asyncio.CancelledError:
            print("\n⚠️ Debug session cancelled")
            return None

    async def _debug_invoke(self, agent_id: str, query: str):
        """带调试的调用"""
        self.push_call(agent_id, query)
        try:
            result = await self.simulator.invoke(agent_id, query)
            return result
        finally:
            self.pop_call(agent_id, result)
```

### 5. CLI 工具

```python
# nexusops-agent-sdk/python/nexusops_agent/cli.py

import asyncio
import click
import json
import yaml
from pathlib import Path

@click.group()
def cli():
    """NexusOps Agent SDK CLI"""
    pass

@cli.command()
@click.option('--agent-id', required=True, help='Agent ID')
@click.option('--query', required=True, help='Query to test')
@click.option('--config', default='nexusops.yaml', help='Config file path')
def test(agent_id: str, query: str, config: str):
    """Test an agent locally"""
    from .simulator import create_simulator

    simulator = create_simulator({'config_path': config})

    # 加载 Agent
    # ...

    async def run():
        response = await simulator.invoke(agent_id, query)
        print("\n📋 Response:")
        print(f"Content: {response.content}")
        if response.structured_output:
            print(f"Structured: {json.dumps(response.structured_output, indent=2)}")
        if response.suggested_actions:
            print(f"Actions: {response.suggested_actions}")

    asyncio.run(run())

@cli.command()
@click.option('--agent-id', required=True, help='Agent ID')
@click.option('--query', required=True, help='Query to debug')
def debug(agent_id: str, query: str):
    """Debug an agent interactively"""
    from .debugger import AgentDebugger
    from .simulator import create_simulator

    simulator = create_simulator()
    debugger = AgentDebugger(simulator)

    async def run():
        await debugger.interactive_debug(agent_id, query)

    asyncio.run(run())

@cli.command()
@click.option('--agent-id', required=True, help='Agent ID')
@click.option('--test-file', default='tests/agent_tests.py', help='Test file')
def run_tests(agent_id: str, test_file: str):
    """Run agent tests"""
    # 加载测试文件并运行
    pass

@cli.command()
@click.option('--agent-id', required=True, help='Agent ID')
def manifest(agent_id: str):
    """Print agent manifest"""
    # 加载 Agent 并打印 manifest
    pass

@cli.command()
def init():
    """Initialize a new agent project"""
    template = {
        'agent_id': 'com.example.agents.my-agent',
        'name': 'My Agent',
        'version': '0.1.0',
        'description': 'A new agent',
    }

    # 创建项目结构
    Path('agent.py').write_text('''
from nexusops_agent import BaseAgent, AgentResponse, AgentContext

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="com.example.agents.my-agent",
            name="My Agent",
            version="0.1.0"
        )

    async def invoke(self, query: str, context: AgentContext) -> AgentResponse:
        # TODO: Implement agent logic
        return AgentResponse(content="Hello from my agent!")

agent = MyAgent()
''')

    Path('nexusops.yaml').write_text(yaml.dump(template))
    Path('tests').mkdir(exist_ok=True)

    print("✅ Agent project initialized!")
    print("  - agent.py: Agent implementation")
    print("  - nexusops.yaml: Configuration")
    print("  - tests/: Test directory")

if __name__ == '__main__':
    cli()
```

### 6. VS Code 扩展配置

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Agent",
      "type": "python",
      "request": "launch",
      "module": "nexusops_agent.cli",
      "args": ["debug", "--agent-id", "${input:agentId}", "--query", "${input:query}"],
      "console": "integratedTerminal"
    },
    {
      "name": "Test Agent",
      "type": "python",
      "request": "launch",
      "module": "nexusops_agent.cli",
      "args": ["test", "--agent-id", "${input:agentId}", "--query", "${input:query}"],
      "console": "integratedTerminal"
    }
  ],
  "inputs": [
    {
      "id": "agentId",
      "type": "promptString",
      "description": "Agent ID"
    },
    {
      "id": "query",
      "type": "promptString",
      "description": "Query"
    }
  ]
}
```

## 后果

### 正面
- 完整的本地开发体验
- 支持断点调试
- 自动化测试框架
- 快速迭代

### 负面
- SDK 维护成本
- 模拟器可能与生产环境有差异

## 实现

1. **Phase 3.5**: 基础 SDK 和模拟器
2. **Phase 4**: 测试框架和调试器
3. **Phase 5**: CLI 工具和 IDE 集成
