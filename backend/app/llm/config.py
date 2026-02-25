"""
NexusOps LLM Configuration

多厂商 LLM 配置管理。
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """支持的 LLM 厂商"""
    GLM = "glm"           # Zhipu GLM
    OPENAI = "openai"     # OpenAI
    CLAUDE = "claude"     # Anthropic Claude
    GEMINI = "gemini"     # Google Gemini
    KIMI = "kimi"         # Moonshot Kimi


class ModelConfig(BaseModel):
    """单个模型配置"""
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60


class GLMConfig(ModelConfig):
    """Zhipu GLM 配置"""
    model_name: str = "glm-4-flash"
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"


class OpenAIConfig(ModelConfig):
    """OpenAI 配置"""
    model_name: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"


class ClaudeConfig(ModelConfig):
    """Claude 配置"""
    model_name: str = "claude-3-5-sonnet-20241022"
    base_url: str = "https://api.anthropic.com"


class GeminiConfig(ModelConfig):
    """Gemini 配置"""
    model_name: str = "gemini-1.5-pro"
    base_url: str = "https://generativelanguage.googleapis.com"


class KimiConfig(ModelConfig):
    """Kimi (Moonshot) 配置"""
    model_name: str = "moonshot-v1-8k"
    base_url: str = "https://api.moonshot.cn/v1"


class LLMConfig(BaseModel):
    """LLM 统一配置"""
    default_provider: LLMProvider = LLMProvider.GLM
    providers: Dict[str, ModelConfig] = Field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载配置"""
        providers = {}

        # GLM
        if os.getenv("GLM_API_KEY"):
            providers["glm"] = GLMConfig(
                api_key=os.getenv("GLM_API_KEY"),
                model_name=os.getenv("GLM_MODEL", "glm-4-flash"),
            )

        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            )

        # Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["claude"] = ClaudeConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model_name=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            )

        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            providers["gemini"] = GeminiConfig(
                api_key=os.getenv("GEMINI_API_KEY"),
                model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            )

        # Kimi
        if os.getenv("KIMI_API_KEY"):
            providers["kimi"] = KimiConfig(
                api_key=os.getenv("KIMI_API_KEY"),
                model_name=os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
            )

        default_provider = LLMProvider(os.getenv("LLM_DEFAULT_PROVIDER", "glm"))

        return cls(
            default_provider=default_provider,
            providers=providers,
        )

    def get_provider_config(self, provider: LLMProvider) -> Optional[ModelConfig]:
        """获取指定厂商的配置"""
        return self.providers.get(provider.value)
