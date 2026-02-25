"""
NexusOps LLM - Zhipu GLM Client

智谱 GLM 模型客户端实现。
"""

import asyncio
import time
from typing import List, Optional, Dict, Any, AsyncIterator
import httpx

from app.llm.base import BaseLLMClient, LLMMessage, LLMResponse, LLMStreamChunk, LLMStreamChunk


class GLMClient(BaseLLMClient):
    """
    Zhipu GLM 客户端

    支持的模型：
    - glm-4-flash (默认，快速)
    - glm-4
    - glm-4-plus
    - glm-3-turbo
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "glm-4-flash",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: List[LLMMessage],
        **kwargs,
    ) -> LLMResponse:
        """
        发送聊天请求到 GLM

        Args:
            messages: 消息列表
            **kwargs: 额外参数（top_p, stream 等）

        Returns:
            LLM 响应
        """
        start_time = time.time()

        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": self._build_messages(messages),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)

        choice = data["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason")

        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            finish_reason=finish_reason,
            latency_ms=latency_ms,
        )

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        **kwargs,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        发送流式聊天请求到 GLM

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            流式响应块
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": self._build_messages(messages),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "top_p": kwargs.get("top_p", 0.9),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or line == "data: [DONE]":
                        continue

                    if line.startswith("data: "):
                        import json
                        try:
                            data = json.loads(line[6:])
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                finish_reason = choices[0].get("finish_reason")

                                if content:
                                    yield LLMStreamChunk(
                                        content=content,
                                        finish_reason=finish_reason,
                                    )
                        except json.JSONDecodeError:
                            continue

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
