"""
NexusOps AI Provider Configuration API

支持多 Provider 配置、Model 选择、连接测试。
"""

import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.llm.multi_provider_config import (
    get_config_manager,
    get_llm_config,
    ProviderConfig,
    PROVIDER_METADATA,
)

# Load .env.llm if exists
load_dotenv(".env.llm")

router = APIRouter(prefix="/ai", tags=["AI Configuration"])


# ============================================
# Request/Response Models
# ============================================

class ProviderInfo(BaseModel):
    """Provider 信息"""
    id: str
    name: str
    description: str
    base_url: str
    models: List[Dict[str, str]]
    default_model: str
    configured: bool
    enabled: bool
    masked_api_key: Optional[str] = None  # 加密显示的 API Key (如 "xxxx...xxxx")
    current_model: Optional[str] = None   # 当前配置的模型


class ProviderConfigRequest(BaseModel):
    """Provider 配置请求"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = True


class SetCurrentModelRequest(BaseModel):
    """设置当前模型请求"""
    provider: str
    model: str


class ConnectionTestResult(BaseModel):
    """连接测试结果"""
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None


class FullConfigResponse(BaseModel):
    """完整配置响应"""
    providers: Dict[str, Any]
    current_provider: str
    current_model: str


# ============================================
# Provider ID Mapping (frontend -> backend)
# ============================================

# Frontend uses "glm", backend uses "zhipu" internally
PROVIDER_ID_MAP = {
    "glm": "zhipu",
    "zhipu": "zhipu",
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "gemini": "gemini",
    "kimi": "kimi",
}

REVERSE_PROVIDER_MAP = {v: k for k, v in PROVIDER_ID_MAP.items()}


def normalize_provider_id(provider_id: str) -> str:
    """Normalize provider ID for internal use"""
    return PROVIDER_ID_MAP.get(provider_id, provider_id)


def frontend_provider_id(internal_id: str) -> str:
    """Convert internal provider ID to frontend ID"""
    return REVERSE_PROVIDER_MAP.get(internal_id, internal_id)


# ============================================
# Helper Functions
# ============================================

def mask_api_key(api_key: str) -> str:
    """加密显示 API Key (只显示前后4位)"""
    if not api_key or len(api_key) <= 8:
        return "****" if api_key else ""
    return f"{api_key[:4]}...{api_key[-4:]}"


async def test_provider_connection(
    provider: str,
    api_key: str,
    base_url: str = None,
    model: str = None
) -> ConnectionTestResult:
    """测试 Provider 连接"""
    import time

    start = time.time()
    internal_provider = normalize_provider_id(provider)

    if internal_provider == "openai":
        return await _test_openai(api_key, base_url, model, start)
    elif internal_provider == "anthropic":
        return await _test_anthropic(api_key, base_url, model, start)
    elif internal_provider == "zhipu":
        return await _test_zhipu(api_key, base_url, model, start, provider)
    elif internal_provider == "gemini":
        return await _test_gemini(api_key, base_url, model, start)
    elif internal_provider == "kimi":
        return await _test_kimi(api_key, base_url, model, start)
    else:
        return ConnectionTestResult(
            success=False,
            message=f"Unsupported provider: {provider}",
            provider=provider,
            error="Unknown provider"
        )


async def _test_openai(api_key: str, base_url: str, model: str, start: float) -> ConnectionTestResult:
    """测试 OpenAI 连接"""
    import httpx
    import time

    base_url = base_url or "https://api.openai.com/v1"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to OpenAI",
                    provider="openai",
                    model=model,
                    response_time_ms=latency
                )
            elif response.status_code == 401:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid API key",
                    provider="openai",
                    error="Authentication failed"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"OpenAI returned status {response.status_code}",
                    provider="openai",
                    error=response.text[:200]
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Connection failed",
            provider="openai",
            error=str(e)
        )


async def _test_anthropic(api_key: str, base_url: str, model: str, start: float) -> ConnectionTestResult:
    """测试 Anthropic 连接"""
    import httpx
    import time

    base_url = base_url or "https://api.anthropic.com"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Anthropic doesn't have a simple health endpoint, try a minimal message
            response = await client.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or "claude-3-5-sonnet-20241022",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hi"}]
                }
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Anthropic",
                    provider="anthropic",
                    model=model,
                    response_time_ms=latency
                )
            elif response.status_code == 401:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid API key",
                    provider="anthropic",
                    error="Authentication failed"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Anthropic returned status {response.status_code}",
                    provider="anthropic",
                    error=response.text[:200]
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Connection failed",
            provider="anthropic",
            error=str(e)
        )


async def _test_zhipu(api_key: str, base_url: str, model: str, start: float, frontend_id: str = "glm") -> ConnectionTestResult:
    """测试智谱 GLM 连接"""
    import httpx
    import time

    base_url = base_url or "https://open.bigmodel.cn/api/paas/v4"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test with a simple chat completion
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or "glm-4-flash",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                }
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Zhipu GLM",
                    provider=frontend_id,
                    model=model,
                    response_time_ms=latency
                )
            elif response.status_code in [401, 403]:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid API key",
                    provider=frontend_id,
                    error="Authentication failed"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Zhipu returned status {response.status_code}",
                    provider=frontend_id,
                    error=response.text[:200]
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Connection failed",
            provider=frontend_id,
            error=str(e)
        )


async def _test_gemini(api_key: str, base_url: str, model: str, start: float) -> ConnectionTestResult:
    """测试 Google Gemini 连接"""
    import httpx
    import time

    base_url = base_url or "https://generativelanguage.googleapis.com"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{base_url}/v1beta/models",
                params={"key": api_key}
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Google Gemini",
                    provider="gemini",
                    model=model,
                    response_time_ms=latency
                )
            elif response.status_code == 401:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid API key",
                    provider="gemini",
                    error="Authentication failed"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Gemini returned status {response.status_code}",
                    provider="gemini",
                    error=response.text[:200]
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Connection failed",
            provider="gemini",
            error=str(e)
        )


async def _test_kimi(api_key: str, base_url: str, model: str, start: float) -> ConnectionTestResult:
    """测试 Kimi 连接"""
    import httpx
    import time

    base_url = base_url or "https://api.moonshot.cn/v1"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Moonshot Kimi",
                    provider="kimi",
                    model=model,
                    response_time_ms=latency
                )
            elif response.status_code == 401:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid API key",
                    provider="kimi",
                    error="Authentication failed"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Kimi returned status {response.status_code}",
                    provider="kimi",
                    error=response.text[:200]
                )
    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message="Connection failed",
            provider="kimi",
            error=str(e)
        )


# ============================================
# API Endpoints
# ============================================

@router.get("/providers")
async def list_providers() -> List[ProviderInfo]:
    """列出所有支持的 Provider"""
    config = get_llm_config()
    providers = []

    for provider_id, meta in PROVIDER_METADATA.items():
        provider_config = config.providers.get(provider_id)

        # Check if configured from env or saved config
        is_configured = False
        is_enabled = False
        masked_key = None
        current_model = None

        # Get API key (for masking)
        api_key = None
        if provider_config:
            is_configured = bool(provider_config.api_key)
            is_enabled = provider_config.enabled
            api_key = provider_config.api_key
            current_model = provider_config.default_model
        else:
            # Check env
            env_key = os.getenv(meta.get("env_key", ""))
            is_configured = bool(env_key)
            is_enabled = is_configured
            api_key = env_key

        # If this is the current provider, use the current model
        if config.current_provider == provider_id:
            current_model = config.current_model
        elif not current_model:
            current_model = meta["default_model"]

        # Mask the API key
        if api_key:
            masked_key = mask_api_key(api_key)

        providers.append(ProviderInfo(
            id=provider_id,
            name=meta["name"],
            description=meta["description"],
            base_url=provider_config.base_url if provider_config else meta["base_url"],
            models=meta["models"],
            default_model=meta["default_model"],
            configured=is_configured,
            enabled=is_enabled,
            masked_api_key=masked_key,
            current_model=current_model
        ))

    return providers


@router.get("/config")
async def get_config() -> FullConfigResponse:
    """获取完整配置"""
    config = get_llm_config()

    # Build providers dict with masked keys
    providers = {}
    for provider_id, meta in PROVIDER_METADATA.items():
        provider_config = config.providers.get(provider_id)

        # Check env for API key
        api_key = None
        if provider_config and provider_config.api_key:
            api_key = provider_config.api_key
        else:
            api_key = os.getenv(meta.get("env_key", ""))

        providers[provider_id] = {
            "name": meta["name"],
            "base_url": provider_config.base_url if provider_config else meta["base_url"],
            "models": [m["id"] for m in meta["models"]],
            "default_model": meta["default_model"],
            "has_api_key": bool(api_key),
            "enabled": provider_config.enabled if provider_config else bool(api_key)
        }

    return FullConfigResponse(
        providers=providers,
        current_provider=config.current_provider,
        current_model=config.current_model
    )


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, request: ProviderConfigRequest):
    """更新 Provider 配置"""
    if provider_id not in PROVIDER_METADATA:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_id}")

    manager = get_config_manager()
    config = manager.get_config()

    meta = PROVIDER_METADATA[provider_id]

    # Create or update provider config
    new_config = ProviderConfig(
        api_key=request.api_key,
        base_url=request.base_url or meta["base_url"],
        models=[m["id"] for m in meta["models"]],
        default_model=meta["default_model"],
        enabled=request.enabled
    )

    manager.update_provider(provider_id, new_config)

    return {
        "success": True,
        "message": f"Provider {provider_id} updated successfully",
        "provider": provider_id
    }


@router.post("/set-current")
async def set_current_model(request: SetCurrentModelRequest):
    """设置当前使用的 Provider 和 Model"""
    if request.provider not in PROVIDER_METADATA:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {request.provider}")

    # 允许任意模型名称，不做验证限制（用户可能使用最新的模型如 glm-5）
    manager = get_config_manager()
    manager.set_current_provider(request.provider, request.model)

    return {
        "success": True,
        "message": f"Set current model to {request.provider}/{request.model}",
        "current_provider": request.provider,
        "current_model": request.model
    }


@router.post("/providers/{provider_id}/test", response_model=ConnectionTestResult)
async def test_provider(provider_id: str):
    """测试 Provider 连接"""
    if provider_id not in PROVIDER_METADATA:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_id}")

    config = get_llm_config()
    provider_config = config.providers.get(provider_id)

    # Get API key from config or env
    meta = PROVIDER_METADATA[provider_id]
    api_key = None
    base_url = None

    if provider_config:
        api_key = provider_config.api_key
        base_url = provider_config.base_url

    if not api_key:
        api_key = os.getenv(meta.get("env_key", ""))

    if not base_url:
        base_url = os.getenv(meta.get("env_base_url", ""), meta["base_url"])

    if not api_key:
        return ConnectionTestResult(
            success=False,
            message=f"No API key configured for {meta['name']}",
            provider=provider_id,
            error="API key not configured"
        )

    model = provider_config.default_model if provider_config else meta["default_model"]

    return await test_provider_connection(provider_id, api_key, base_url, model)


@router.get("/providers/{provider_id}/models")
async def list_provider_models(provider_id: str):
    """列出 Provider 支持的所有模型"""
    if provider_id not in PROVIDER_METADATA:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_id}")

    meta = PROVIDER_METADATA[provider_id]

    return {
        "provider": provider_id,
        "name": meta["name"],
        "models": meta["models"],
        "default_model": meta["default_model"]
    }
