"""
LLM Integration Tests - Zhipu GLM

Tests real GLM API connectivity.
"""

import pytest
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load LLM environment variables
env_path = Path(__file__).parent.parent / ".env.llm"
if env_path.exists():
    load_dotenv(env_path)

from app.llm.base import LLMMessage, MessageRole
from app.llm.config import LLMConfig, LLMProvider
from app.llm.glm import GLMClient
from app.llm.factory import LLMClientFactory


def has_glm_config() -> bool:
    """Check if GLM configuration is available"""
    return bool(os.getenv("GLM_API_KEY"))


@pytest.fixture
def glm_config():
    """GLM configuration"""
    if not has_glm_config():
        pytest.skip("GLM configuration not available")
    return LLMConfig.from_env()


@pytest.fixture
def glm_client(glm_config):
    """GLM client"""
    return LLMClientFactory.create(LLMProvider.GLM, glm_config)


@pytest.mark.integration
@pytest.mark.llm
class TestGLMConnection:
    """Test GLM API connectivity"""

    def test_config_loaded(self, glm_config):
        """Test configuration is loaded"""
        assert glm_config.default_provider == LLMProvider.GLM
        assert "glm" in glm_config.providers

    def test_client_created(self, glm_client):
        """Test client is created"""
        assert glm_client is not None
        assert glm_client.api_key is not None
        assert glm_client.model == "glm-4-flash"


@pytest.mark.integration
@pytest.mark.llm
class TestGLMChat:
    """Test GLM chat functionality"""

    @pytest.mark.asyncio
    async def test_simple_chat(self, glm_client):
        """Test simple chat"""
        response = await glm_client.simple_chat(
            prompt="你好，请用一句话介绍自己。",
            system_prompt="你是一个友好的AI助手。",
        )

        assert response is not None
        assert len(response) > 0
        print(f"Response: {response}")

    @pytest.mark.asyncio
    async def test_chat_with_messages(self, glm_client):
        """Test chat with message list"""
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content="你是一个技术专家。"),
            LLMMessage(role=MessageRole.USER, content="什么是 Kubernetes？请用一句话回答。"),
        ]

        response = await glm_client.chat(messages)

        assert response.content is not None
        assert len(response.content) > 0
        assert response.model is not None
        print(f"Model: {response.model}")
        print(f"Content: {response.content}")
        print(f"Usage: {response.usage}")
        print(f"Latency: {response.latency_ms}ms")

    @pytest.mark.asyncio
    async def test_chat_with_context(self, glm_client):
        """Test chat with context"""
        messages = [
            LLMMessage(role=MessageRole.USER, content="我的名字是小明。"),
            LLMMessage(role=MessageRole.ASSISTANT, content="你好小明！很高兴认识你。"),
            LLMMessage(role=MessageRole.USER, content="你还记得我的名字吗？"),
        ]

        response = await glm_client.chat(messages)

        assert response.content is not None
        assert "小明" in response.content or "名字" in response.content
        print(f"Response: {response.content}")


@pytest.mark.integration
@pytest.mark.llm
class TestGLMStream:
    """Test GLM streaming"""

    @pytest.mark.asyncio
    async def test_stream_chat(self, glm_client):
        """Test streaming chat"""
        messages = [
            LLMMessage(role=MessageRole.USER, content="请用三句话描述春天。"),
        ]

        chunks = []
        async for chunk in glm_client.chat_stream(messages):
            chunks.append(chunk)
            print(chunk.content, end="", flush=True)

        print()  # New line

        assert len(chunks) > 0
        full_content = "".join(c.content for c in chunks)
        assert len(full_content) > 0


@pytest.mark.integration
@pytest.mark.llm
class TestGLMFactory:
    """Test LLM factory"""

    def test_create_default(self):
        """Test creating default client"""
        client = LLMClientFactory.create_default()
        assert client is not None
        assert isinstance(client, GLMClient)

    def test_clear_cache(self):
        """Test clearing cache"""
        LLMClientFactory.clear_cache()
        assert len(LLMClientFactory._instances) == 0
