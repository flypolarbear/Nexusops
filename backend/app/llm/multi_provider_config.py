"""
NexusOps LLM Multi-Provider Configuration System

支持 OpenAI、Anthropic、Zhipu GLM 等多 Provider 配置。
参考 OpenCode 项目的配置结构设计。
"""

import os
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path


# ============================================
# Provider Definitions
# ============================================

class ProviderType(str, Enum):
    """支持的 Provider 类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"
    GEMINI = "gemini"
    KIMI = "kimi"


# Provider 元数据定义
PROVIDER_METADATA = {
    "openai": {
        "name": "OpenAI",
        "description": "GPT-4, GPT-4o, O1/O3 系列模型",
        "base_url": "https://api.openai.com/v1",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "description": "最新旗舰模型，多模态"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "轻量高效版本"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "GPT-4 增强版"},
            {"id": "o1", "name": "O1", "description": "推理增强模型"},
            {"id": "o1-mini", "name": "O1 Mini", "description": "轻量推理模型"},
            {"id": "o3-mini", "name": "O3 Mini", "description": "最新推理模型"},
        ],
        "default_model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "env_base_url": "OPENAI_BASE_URL",
    },
    "anthropic": {
        "name": "Anthropic",
        "description": "Claude 系列模型",
        "base_url": "https://api.anthropic.com",
        "models": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "最新 Claude 3.5 Sonnet"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "description": "快速轻量模型"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "最强推理能力"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "平衡性能"},
        ],
        "default_model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
        "env_base_url": "ANTHROPIC_BASE_URL",
    },
    # "glm" is the primary key, "zhipu" is kept for backward compatibility
    "glm": {
        "name": "Zhipu GLM",
        "description": "智谱 GLM 系列模型",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "description": "快速响应，适合日常对话"},
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "description": "增强能力，复杂任务"},
            {"id": "glm-4", "name": "GLM-4", "description": "标准版本"},
            {"id": "glm-4-air", "name": "GLM-4 Air", "description": "性价比版本"},
            {"id": "glm-4-airx", "name": "GLM-4 AirX", "description": "极速推理"},
        ],
        "default_model": "glm-4-flash",
        "env_key": "GLM_API_KEY",
        "env_base_url": "GLM_BASE_URL",
    },
    # Alias for backward compatibility
    "zhipu": {
        "name": "Zhipu GLM",
        "description": "智谱 GLM 系列模型",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-4-flash", "name": "GLM-4 Flash", "description": "快速响应，适合日常对话"},
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "description": "增强能力，复杂任务"},
            {"id": "glm-4", "name": "GLM-4", "description": "标准版本"},
            {"id": "glm-4-air", "name": "GLM-4 Air", "description": "性价比版本"},
            {"id": "glm-4-airx", "name": "GLM-4 AirX", "description": "极速推理"},
        ],
        "default_model": "glm-4-flash",
        "env_key": "GLM_API_KEY",
        "env_base_url": "GLM_BASE_URL",
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google Gemini 系列模型",
        "base_url": "https://generativelanguage.googleapis.com",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "description": "最新 Pro 版本"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "description": "快速响应"},
            {"id": "gemini-pro", "name": "Gemini Pro", "description": "标准版本"},
        ],
        "default_model": "gemini-1.5-pro",
        "env_key": "GEMINI_API_KEY",
        "env_base_url": "GEMINI_BASE_URL",
    },
    "kimi": {
        "name": "Moonshot Kimi",
        "description": "Moonshot Kimi 长上下文模型",
        "base_url": "https://api.moonshot.cn/v1",
        "models": [
            {"id": "moonshot-v1-8k", "name": "Kimi 8K", "description": "8K 上下文"},
            {"id": "moonshot-v1-32k", "name": "Kimi 32K", "description": "32K 上下文"},
            {"id": "moonshot-v1-128k", "name": "Kimi 128K", "description": "128K 超长上下文"},
        ],
        "default_model": "moonshot-v1-8k",
        "env_key": "KIMI_API_KEY",
        "env_base_url": "KIMI_BASE_URL",
    },
}


# ============================================
# Configuration Models
# ============================================

class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    description: str = ""


class ProviderConfig(BaseModel):
    """单个 Provider 的配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    enabled: bool = False


class MultiProviderConfig(BaseModel):
    """多 Provider 配置"""
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    current_provider: str = "zhipu"
    current_model: str = "glm-4-flash"

    def get_current_config(self) -> Optional[ProviderConfig]:
        """获取当前 Provider 配置"""
        return self.providers.get(self.current_provider)

    def is_provider_configured(self, provider: str) -> bool:
        """检查 Provider 是否已配置"""
        config = self.providers.get(provider)
        return config is not None and bool(config.api_key) and config.enabled


# ============================================
# Configuration Manager
# ============================================

class LLMConfigManager:
    """LLM 配置管理器"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_path()
        self._config: Optional[MultiProviderConfig] = None

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先使用项目目录下的配置
        project_config = os.path.join(os.getcwd(), ".nexusops", "llm_config.json")
        if os.path.exists(project_config):
            return project_config

        # 其次使用用户目录
        home_config = os.path.expanduser("~/.nexusops/llm_config.json")
        return home_config

    def load(self) -> MultiProviderConfig:
        """加载配置"""
        if self._config is not None:
            return self._config

        # 尝试从文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                self._config = MultiProviderConfig(**data)
            except Exception as e:
                print(f"Failed to load config from {self.config_file}: {e}")
                self._config = self._create_default_config()
        else:
            self._config = self._create_default_config()

        # 从环境变量补充配置
        self._merge_env_config()

        return self._config

    def _create_default_config(self) -> MultiProviderConfig:
        """创建默认配置"""
        providers = {}

        for provider_id, meta in PROVIDER_METADATA.items():
            providers[provider_id] = ProviderConfig(
                api_key=None,
                base_url=meta["base_url"],
                models=[m["id"] for m in meta["models"]],
                default_model=meta["default_model"],
                enabled=False
            )

        return MultiProviderConfig(
            providers=providers,
            current_provider="zhipu",
            current_model="glm-4-flash"
        )

    def _merge_env_config(self):
        """从环境变量合并配置"""
        for provider_id, meta in PROVIDER_METADATA.items():
            env_key = os.getenv(meta.get("env_key", ""))
            if env_key:
                if provider_id not in self._config.providers:
                    self._config.providers[provider_id] = ProviderConfig(
                        api_key=env_key,
                        base_url=os.getenv(meta.get("env_base_url", ""), meta["base_url"]),
                        models=[m["id"] for m in meta["models"]],
                        default_model=meta["default_model"],
                        enabled=True
                    )
                else:
                    self._config.providers[provider_id].api_key = env_key
                    self._config.providers[provider_id].enabled = True

            # 检查 base_url
            env_base_url = os.getenv(meta.get("env_base_url", ""))
            if env_base_url and provider_id in self._config.providers:
                self._config.providers[provider_id].base_url = env_base_url

    def save(self):
        """保存配置到文件"""
        if self._config is None:
            return

        # 确保目录存在
        config_dir = os.path.dirname(self.config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        # Save config (keep API keys for runtime use)
        # Note: In production, consider encrypting sensitive data
        save_config = self._config.model_dump()

        with open(self.config_file, 'w') as f:
            json.dump(save_config, f, indent=2)

    def _mask_api_key(self, api_key: str) -> str:
        """隐藏 API Key 中间部分"""
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

    def get_config(self) -> MultiProviderConfig:
        """获取当前配置"""
        if self._config is None:
            return self.load()
        return self._config

    def update_provider(self, provider_id: str, config: ProviderConfig):
        """更新 Provider 配置"""
        if self._config is None:
            self.load()

        self._config.providers[provider_id] = config
        self.save()

    def set_current_provider(self, provider_id: str, model: str = None):
        """设置当前 Provider"""
        if self._config is None:
            self.load()

        if provider_id not in self._config.providers:
            raise ValueError(f"Unknown provider: {provider_id}")

        self._config.current_provider = provider_id

        if model:
            self._config.current_model = model
        else:
            # 使用默认模型
            provider_config = self._config.providers[provider_id]
            self._config.current_model = provider_config.default_model or PROVIDER_METADATA[provider_id]["default_model"]

        self.save()

    def get_current_client_config(self) -> Dict[str, Any]:
        """获取当前 Provider 的客户端配置"""
        config = self.get_config()
        provider_config = config.get_current_config()

        if provider_config is None or not provider_config.api_key:
            return None

        meta = PROVIDER_METADATA.get(config.current_provider, {})

        return {
            "provider": config.current_provider,
            "model": config.current_model,
            "api_key": provider_config.api_key,
            "base_url": provider_config.base_url or meta.get("base_url"),
        }


# ============================================
# Global Instance
# ============================================

_config_manager: Optional[LLMConfigManager] = None


def get_config_manager() -> LLMConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = LLMConfigManager()
    return _config_manager


def get_llm_config() -> MultiProviderConfig:
    """获取 LLM 配置"""
    return get_config_manager().get_config()
