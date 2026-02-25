"""
NexusOps LLM Client Factory

根据配置创建对应的 LLM 客户端。
"""

from typing import Optional

from app.llm.base import BaseLLMClient
from app.llm.config import LLMConfig, LLMProvider
from app.llm.glm import GLMClient


class LLMClientFactory:
    """LLM 客户端工厂"""

    _instances: dict = {}

    @classmethod
    def create(
        cls,
        provider: LLMProvider,
        config: LLMConfig,
    ) -> BaseLLMClient:
        """
        创建 LLM 客户端

        Args:
            provider: LLM 厂商
            config: LLM 配置

        Returns:
            LLM 客户端实例
        """
        # 检查缓存
        cache_key = f"{provider.value}_{id(config)}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        provider_config = config.get_provider_config(provider)
        if not provider_config:
            raise ValueError(f"No configuration found for provider: {provider}")

        client = None

        if provider == LLMProvider.GLM:
            client = GLMClient(
                api_key=provider_config.api_key,
                base_url=provider_config.base_url or "https://open.bigmodel.cn/api/paas/v4",
                model=provider_config.model_name,
                max_tokens=provider_config.max_tokens,
                temperature=provider_config.temperature,
                timeout=provider_config.timeout,
            )
        elif provider == LLMProvider.OPENAI:
            # TODO: Implement OpenAI client
            raise NotImplementedError("OpenAI client not yet implemented")
        elif provider == LLMProvider.CLAUDE:
            # TODO: Implement Claude client
            raise NotImplementedError("Claude client not yet implemented")
        elif provider == LLMProvider.GEMINI:
            # TODO: Implement Gemini client
            raise NotImplementedError("Gemini client not yet implemented")
        elif provider == LLMProvider.KIMI:
            # TODO: Implement Kimi client
            raise NotImplementedError("Kimi client not yet implemented")
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # 缓存实例
        cls._instances[cache_key] = client
        return client

    @classmethod
    def create_default(cls) -> BaseLLMClient:
        """
        创建默认 LLM 客户端

        从环境变量加载配置，使用默认厂商。
        """
        config = LLMConfig.from_env()
        return cls.create(config.default_provider, config)

    @classmethod
    def clear_cache(cls):
        """清除客户端缓存"""
        cls._instances.clear()
