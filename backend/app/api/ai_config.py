"""
NexusOps AI Configuration API

提供 AI/LLM 配置管理接口。
使用 LLMConfigManager 统一管理配置。
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from app.llm.multi_provider_config import get_config_manager, PROVIDER_METADATA

# Load .env.llm if exists
load_dotenv(".env.llm")

router = APIRouter(prefix="/ai", tags=["AI Configuration"])


# ============================================
# Models
# ============================================

class AIConfigResponse(BaseModel):
    """AI 配置响应"""
    provider: str
    model: str
    api_url: str
    status: str
    configured: bool


class AIConfigUpdate(BaseModel):
    """AI 配置更新请求"""
    provider: Optional[str] = None
    model: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None


class AITestResponse(BaseModel):
    """AI 连接测试响应"""
    success: bool
    message: str
    model: Optional[str] = None
    provider: Optional[str] = None


# ============================================
# Provider Configurations (for backward compatibility)
# ============================================

PROVIDER_CONFIGS = {
    "glm": {
        "name": "Zhipu GLM",
        "default_model": "glm-4-flash",
        "api_url": "https://open.bigmodel.cn/api/paas/v4",
        "env_key": "GLM_API_KEY",
        "env_model": "GLM_MODEL",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o",
        "api_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "env_model": "OPENAI_MODEL",
    },
    "claude": {
        "name": "Anthropic Claude",
        "default_model": "claude-3-5-sonnet-20241022",
        "api_url": "https://api.anthropic.com",
        "env_key": "ANTHROPIC_API_KEY",
        "env_model": "CLAUDE_MODEL",
    },
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-1.5-pro",
        "api_url": "https://generativelanguage.googleapis.com",
        "env_key": "GEMINI_API_KEY",
        "env_model": "GEMINI_MODEL",
    },
    "kimi": {
        "name": "Moonshot Kimi",
        "default_model": "moonshot-v1-8k",
        "api_url": "https://api.moonshot.cn/v1",
        "env_key": "KIMI_API_KEY",
        "env_model": "KIMI_MODEL",
    },
}


def get_current_config() -> dict:
    """获取当前配置 - 使用 LLMConfigManager"""
    manager = get_config_manager()
    config = manager.get_config()

    provider_id = config.current_provider
    model = config.current_model

    # Get provider config
    provider_config = config.providers.get(provider_id)

    # Get metadata
    meta = PROVIDER_METADATA.get(provider_id, {})

    # Check if configured
    has_key = False
    api_url = meta.get("base_url", "")

    if provider_config:
        has_key = bool(provider_config.api_key)
        api_url = provider_config.base_url or api_url
    else:
        # Check environment variable
        env_key_name = meta.get("env_key", "")
        has_key = bool(os.getenv(env_key_name))

    return {
        "provider": provider_id,
        "model": model,
        "api_url": api_url,
        "status": "configured" if has_key else "not_configured",
        "configured": has_key,
    }


# ============================================
# Endpoints
# ============================================

@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config():
    """
    获取当前 AI 配置

    返回当前配置的 Provider、Model 和连接状态。
    """
    config = get_current_config()
    return AIConfigResponse(**config)


@router.put("/config", response_model=AIConfigResponse)
async def update_ai_config(update: AIConfigUpdate):
    """
    更新 AI 配置

    更新 Provider、Model 或 API Key。
    """
    manager = get_config_manager()
    config = manager.get_config()

    # Update provider and model if specified
    if update.provider:
        if update.provider not in PROVIDER_METADATA:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {update.provider}. Valid providers: {list(PROVIDER_METADATA.keys())}"
            )

        # Set current provider
        model = update.model or config.current_model
        manager.set_current_provider(update.provider, model)

    # Update API key if provided
    if update.api_key:
        from app.llm.multi_provider_config import ProviderConfig

        provider_id = update.provider or config.current_provider
        meta = PROVIDER_METADATA.get(provider_id, {})
        existing = config.providers.get(provider_id)

        new_config = ProviderConfig(
            api_key=update.api_key,
            base_url=update.api_url or (existing.base_url if existing else meta.get("base_url")),
            models=existing.models if existing else [m["id"] for m in meta.get("models", [])],
            default_model=existing.default_model if existing else meta.get("default_model"),
            enabled=True
        )
        manager.update_provider(provider_id, new_config)

    return AIConfigResponse(**get_current_config())


@router.post("/test", response_model=AITestResponse)
async def test_ai_connection():
    """
    测试 AI 连接

    使用当前配置测试与 LLM Provider 的连接。
    """
    config = get_current_config()
    provider = config["provider"]
    provider_info = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["glm"])

    # Get API key from LLMConfigManager
    manager = get_config_manager()
    llm_config = manager.get_config()
    provider_config = llm_config.providers.get(provider)

    api_key = None
    if provider_config:
        api_key = provider_config.api_key

    # Fallback to environment variable
    if not api_key:
        meta = PROVIDER_METADATA.get(provider, {})
        env_key_name = meta.get("env_key", "")
        api_key = os.getenv(env_key_name)

    if not api_key:
        return AITestResponse(
            success=False,
            message=f"No API key configured for {provider_info['name']}. Please configure your API key.",
            model=config["model"],
            provider=provider,
        )

    # Test connection based on provider
    try:
        if provider == "glm":
            return await _test_glm_connection(api_key, config["model"])
        elif provider == "openai":
            return await _test_openai_connection(api_key, config["model"])
        elif provider == "claude":
            return await _test_claude_connection(api_key, config["model"])
        elif provider == "gemini":
            return await _test_gemini_connection(api_key, config["model"])
        elif provider == "kimi":
            return await _test_kimi_connection(api_key, config["model"])
        else:
            return AITestResponse(
                success=False,
                message=f"Unsupported provider: {provider}",
            )
    except Exception as e:
        return AITestResponse(
            success=False,
            message=f"Connection test failed: {str(e)}",
            model=config["model"],
            provider=provider,
        )


@router.get("/providers")
async def list_providers():
    """
    列出所有支持的 AI Providers
    """
    manager = get_config_manager()
    config = manager.get_config()

    def mask_key(key: str) -> str:
        """加密显示 API Key"""
        if not key or len(key) <= 8:
            return "****" if key else ""
        return f"{key[:4]}...{key[-4:]}"

    result = []
    for key, info in PROVIDER_CONFIGS.items():
        # Check LLMConfigManager first
        provider_config = config.providers.get(key)
        meta = PROVIDER_METADATA.get(key, {})

        has_key = False
        masked_key = None
        current_model = None

        if provider_config:
            has_key = bool(provider_config.api_key)
            if provider_config.api_key:
                masked_key = mask_key(provider_config.api_key)
            current_model = provider_config.default_model
        else:
            # Check environment variable
            env_key_name = meta.get("env_key", "")
            env_key = os.getenv(env_key_name)
            has_key = bool(env_key)
            if env_key:
                masked_key = mask_key(env_key)

        # 如果是当前 provider，使用当前配置的模型
        if config.current_provider == key:
            current_model = config.current_model
        elif not current_model:
            current_model = info["default_model"]

        result.append({
            "id": key,
            "name": info["name"],
            "default_model": info["default_model"],
            "api_url": provider_config.base_url if provider_config else info["api_url"],
            "configured": has_key,
            "masked_api_key": masked_key,
            "current_model": current_model,
        })

    return result


# ============================================
# Provider-specific test functions
# ============================================

async def _test_glm_connection(api_key: str, model: str) -> AITestResponse:
    """测试 GLM 连接"""
    try:
        from app.llm.glm import GLMClient
        from app.llm.base import LLMMessage, MessageRole

        client = GLMClient(api_key=api_key, model=model)
        # Use simple_chat for easy testing
        response = await client.simple_chat("Hi")

        if response:
            return AITestResponse(
                success=True,
                message=f"Successfully connected to Zhipu GLM ({model})",
                model=model,
                provider="glm",
            )
        else:
            return AITestResponse(
                success=False,
                message="GLM returned empty response",
                model=model,
                provider="glm",
            )
    except ImportError:
        return AITestResponse(
            success=False,
            message="GLM client not installed. Please check dependencies.",
            model=model,
            provider="glm",
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid_api_key" in error_msg.lower():
            return AITestResponse(
                success=False,
                message="Invalid API key for GLM. Please check your credentials.",
                model=model,
                provider="glm",
            )
        return AITestResponse(
            success=False,
            message=f"GLM connection error: {error_msg}",
            model=model,
            provider="glm",
        )


async def _test_openai_connection(api_key: str, model: str) -> AITestResponse:
    """测试 OpenAI 连接"""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )

        if response.choices:
            return AITestResponse(
                success=True,
                message=f"Successfully connected to OpenAI ({model})",
                model=model,
                provider="openai",
            )
        else:
            return AITestResponse(
                success=False,
                message="OpenAI returned empty response",
                model=model,
                provider="openai",
            )
    except ImportError:
        return AITestResponse(
            success=False,
            message="OpenAI library not installed. Run: pip install openai",
            model=model,
            provider="openai",
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return AITestResponse(
                success=False,
                message="Invalid API key for OpenAI. Please check your credentials.",
                model=model,
                provider="openai",
            )
        return AITestResponse(
            success=False,
            message=f"OpenAI connection error: {error_msg}",
            model=model,
            provider="openai",
        )


async def _test_claude_connection(api_key: str, model: str) -> AITestResponse:
    """测试 Claude 连接"""
    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )

        if response.content:
            return AITestResponse(
                success=True,
                message=f"Successfully connected to Claude ({model})",
                model=model,
                provider="claude",
            )
        else:
            return AITestResponse(
                success=False,
                message="Claude returned empty response",
                model=model,
                provider="claude",
            )
    except ImportError:
        return AITestResponse(
            success=False,
            message="Anthropic library not installed. Run: pip install anthropic",
            model=model,
            provider="claude",
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return AITestResponse(
                success=False,
                message="Invalid API key for Claude. Please check your credentials.",
                model=model,
                provider="claude",
            )
        return AITestResponse(
            success=False,
            message=f"Claude connection error: {error_msg}",
            model=model,
            provider="claude",
        )


async def _test_gemini_connection(api_key: str, model: str) -> AITestResponse:
    """测试 Gemini 连接"""
    # Gemini uses REST API, so we'll use httpx
    try:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": api_key}
        data = {
            "contents": [{"parts": [{"text": "Hi"}]}]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params, json=data, timeout=30)

            if response.status_code == 200:
                return AITestResponse(
                    success=True,
                    message=f"Successfully connected to Gemini ({model})",
                    model=model,
                    provider="gemini",
                )
            elif response.status_code == 401:
                return AITestResponse(
                    success=False,
                    message="Invalid API key for Gemini. Please check your credentials.",
                    model=model,
                    provider="gemini",
                )
            else:
                return AITestResponse(
                    success=False,
                    message=f"Gemini returned status {response.status_code}: {response.text[:200]}",
                    model=model,
                    provider="gemini",
                )
    except ImportError:
        return AITestResponse(
            success=False,
            message="httpx library not installed. Run: pip install httpx",
            model=model,
            provider="gemini",
        )
    except Exception as e:
        return AITestResponse(
            success=False,
            message=f"Gemini connection error: {str(e)}",
            model=model,
            provider="gemini",
        )


async def _test_kimi_connection(api_key: str, model: str) -> AITestResponse:
    """测试 Kimi 连接"""
    try:
        from openai import AsyncOpenAI

        # Kimi uses OpenAI-compatible API
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )

        if response.choices:
            return AITestResponse(
                success=True,
                message=f"Successfully connected to Kimi ({model})",
                model=model,
                provider="kimi",
            )
        else:
            return AITestResponse(
                success=False,
                message="Kimi returned empty response",
                model=model,
                provider="kimi",
            )
    except ImportError:
        return AITestResponse(
            success=False,
            message="OpenAI library not installed. Run: pip install openai",
            model=model,
            provider="kimi",
        )
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return AITestResponse(
                success=False,
                message="Invalid API key for Kimi. Please check your credentials.",
                model=model,
                provider="kimi",
            )
        return AITestResponse(
            success=False,
            message=f"Kimi connection error: {error_msg}",
            model=model,
            provider="kimi",
        )
