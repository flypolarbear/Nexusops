"""
NexusOps LLM Base Client

统一的 LLM 客户端接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator
from pydantic import BaseModel
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    """LLM 消息"""
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        return data


class LLMResponse(BaseModel):
    """LLM 响应"""
    content: str
    model: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    latency_ms: Optional[int] = None


class LLMStreamChunk(BaseModel):
    """流式响应块"""
    content: str
    finish_reason: Optional[str] = None


class BaseLLMClient(ABC):
    """LLM 客户端基类"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        **kwargs,
    ) -> LLMResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        **kwargs,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        发送流式聊天请求

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            流式响应块
        """
        pass

    async def simple_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        简单聊天接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示（可选）

        Returns:
            响应文本
        """
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role=MessageRole.SYSTEM, content=system_prompt))
        messages.append(LLMMessage(role=MessageRole.USER, content=prompt))

        response = await self.chat(messages)
        return response.content

    def _build_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """构建消息列表"""
        return [msg.to_dict() for msg in messages]
