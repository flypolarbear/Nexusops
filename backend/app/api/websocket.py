"""
NexusOps Backend - WebSocket Manager

OPT-001: 实时数据推送
- 部署状态实时更新
- 告警实时推送
- 断线自动重连
"""

import asyncio
import json
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import uuid

from fastapi import WebSocket, WebSocketDisconnect


class MessageType(str, Enum):
    """WebSocket 消息类型"""
    # 连接
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # 订阅
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # 部署相关
    DEPLOYMENT_UPDATE = "deployment_update"
    DEPLOYMENT_STEP_UPDATE = "deployment_step_update"

    # 告警相关
    ALERT_NEW = "alert_new"
    ALERT_UPDATE = "alert_update"

    # Agent 相关
    AGENT_MESSAGE = "agent_message"
    AGENT_STREAM = "agent_stream"

    # 版本相关
    VERSION_UPDATE = "version_update"

    # 通用
    NOTIFICATION = "notification"
    ERROR = "error"


class WebSocketMessage:
    """WebSocket 消息格式"""

    def __init__(
        self,
        type: MessageType,
        data: Any = None,
        channel: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        self.type = type
        self.data = data
        self.channel = channel
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "channel": self.channel,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketMessage":
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            data=data.get("data"),
            channel=data.get("channel"),
            timestamp=data.get("timestamp"),
        )


class Connection:
    """WebSocket 连接封装"""

    def __init__(self, websocket: WebSocket, user_id: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.websocket = websocket
        self.user_id = user_id
        self.subscriptions: set[str] = set()
        self.last_ping = datetime.utcnow()
        self.is_active = True

    async def send(self, message: WebSocketMessage) -> bool:
        """发送消息"""
        if not self.is_active:
            return False
        try:
            await self.websocket.send_text(message.to_json())
            return True
        except Exception:
            self.is_active = False
            return False

    async def receive(self) -> Optional[WebSocketMessage]:
        """接收消息"""
        if not self.is_active:
            return None
        try:
            data = await self.websocket.receive_text()
            return WebSocketMessage.from_json(data)
        except WebSocketDisconnect:
            self.is_active = False
            return None
        except Exception:
            self.is_active = False
            return None

    def subscribe(self, channel: str):
        """订阅频道"""
        self.subscriptions.add(channel)

    def unsubscribe(self, channel: str):
        """取消订阅"""
        self.subscriptions.discard(channel)

    def is_subscribed(self, channel: str) -> bool:
        """检查是否订阅"""
        return channel in self.subscriptions


class ChannelManager:
    """频道管理器"""

    def __init__(self):
        # 预定义频道
        self.channels: dict[str, set[str]] = {
            # 部署相关
            "deployments": set(),  # 所有部署更新
            "deployments:*": set(),  # 所有部署（通配符）
            "deployments:{deployment_id}": set(),  # 特定部署

            # 版本相关
            "versions": set(),
            "versions:{version_id}": set(),

            # 告警相关
            "alerts": set(),
            "alerts:{severity}": set(),

            # Agent 相关
            "agents": set(),
            "agents:{agent_id}": set(),
            "conversations:{conversation_id}": set(),
        }

    def get_channel_pattern(self, channel: str) -> list[str]:
        """获取匹配的频道模式"""
        patterns = [channel]

        # 添加通配符匹配
        parts = channel.split(":")
        if len(parts) > 1:
            patterns.append(f"{parts[0]}:*")

        return patterns

    def should_receive(self, connection: Connection, channel: str) -> bool:
        """检查连接是否应该接收该频道的消息"""
        for pattern in self.get_channel_pattern(channel):
            if connection.is_subscribed(pattern):
                return True
        return False


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.connections: dict[str, Connection] = {}
        self.channel_manager = ChannelManager()
        self._message_handlers: dict[MessageType, list[Callable]] = {}
        self._background_tasks: list[asyncio.Task] = []

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> Connection:
        """接受新连接"""
        await websocket.accept()
        connection = Connection(websocket, user_id)
        self.connections[connection.id] = connection

        # 发送连接确认
        await connection.send(WebSocketMessage(
            type=MessageType.CONNECT,
            data={"connection_id": connection.id}
        ))

        return connection

    def disconnect(self, connection: Connection):
        """断开连接"""
        connection.is_active = False
        if connection.id in self.connections:
            del self.connections[connection.id]

    async def broadcast(self, message: WebSocketMessage, channel: Optional[str] = None):
        """广播消息到所有连接或特定频道"""
        message.channel = channel

        disconnected = []
        for connection in self.connections.values():
            if not connection.is_active:
                disconnected.append(connection.id)
                continue

            if channel and not self.channel_manager.should_receive(connection, channel):
                continue

            await connection.send(message)

        # 清理断开的连接
        for conn_id in disconnected:
            if conn_id in self.connections:
                del self.connections[conn_id]

    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """发送消息给特定用户"""
        for connection in self.connections.values():
            if connection.user_id == user_id:
                await connection.send(message)

    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """发送消息给特定连接"""
        if connection_id in self.connections:
            await self.connections[connection_id].send(message)

    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    async def handle_message(self, connection: Connection, message: WebSocketMessage):
        """处理接收到的消息"""
        handlers = self._message_handlers.get(message.type, [])

        for handler in handlers:
            try:
                await handler(connection, message)
            except Exception as e:
                await connection.send(WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"message": str(e)}
                ))

        # 内置处理器
        if message.type == MessageType.SUBSCRIBE:
            if message.data and "channel" in message.data:
                connection.subscribe(message.data["channel"])
                await connection.send(WebSocketMessage(
                    type=MessageType.NOTIFICATION,
                    data={"message": f"Subscribed to {message.data['channel']}"}
                ))

        elif message.type == MessageType.UNSUBSCRIBE:
            if message.data and "channel" in message.data:
                connection.unsubscribe(message.data["channel"])

        elif message.type == MessageType.PING:
            connection.last_ping = datetime.utcnow()
            await connection.send(WebSocketMessage(type=MessageType.PONG))

    async def handle_connection(self, connection: Connection):
        """处理连接的生命周期"""
        try:
            while connection.is_active:
                message = await connection.receive()
                if message is None:
                    break
                await self.handle_message(connection, message)
        finally:
            self.disconnect(connection)

    # ============================================
    # 业务方法：推送特定类型的消息
    # ============================================

    async def push_deployment_update(
        self,
        deployment_id: str,
        status: str,
        data: Optional[dict] = None
    ):
        """推送部署状态更新"""
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.DEPLOYMENT_UPDATE,
                data={
                    "deployment_id": deployment_id,
                    "status": status,
                    **(data or {})
                }
            ),
            channel=f"deployments:{deployment_id}"
        )
        # 也广播到通用频道
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.DEPLOYMENT_UPDATE,
                data={
                    "deployment_id": deployment_id,
                    "status": status,
                    **(data or {})
                }
            ),
            channel="deployments"
        )

    async def push_deployment_step_update(
        self,
        deployment_id: str,
        step_id: str,
        step_type: str,
        status: str,
        message: Optional[str] = None
    ):
        """推送部署步骤更新"""
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.DEPLOYMENT_STEP_UPDATE,
                data={
                    "deployment_id": deployment_id,
                    "step_id": step_id,
                    "step_type": step_type,
                    "status": status,
                    "message": message
                }
            ),
            channel=f"deployments:{deployment_id}"
        )

    async def push_alert(
        self,
        alert_id: str,
        severity: str,
        title: str,
        message: str,
        data: Optional[dict] = None
    ):
        """推送新告警"""
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.ALERT_NEW,
                data={
                    "alert_id": alert_id,
                    "severity": severity,
                    "title": title,
                    "message": message,
                    **(data or {})
                }
            ),
            channel="alerts"
        )
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.ALERT_NEW,
                data={
                    "alert_id": alert_id,
                    "severity": severity,
                    "title": title,
                    "message": message,
                    **(data or {})
                }
            ),
            channel=f"alerts:{severity}"
        )

    async def push_agent_stream(
        self,
        conversation_id: str,
        agent_id: str,
        chunk: str,
        is_final: bool = False
    ):
        """推送 Agent 流式响应"""
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.AGENT_STREAM,
                data={
                    "conversation_id": conversation_id,
                    "agent_id": agent_id,
                    "chunk": chunk,
                    "is_final": is_final
                }
            ),
            channel=f"conversations:{conversation_id}"
        )

    async def push_version_update(
        self,
        version_id: str,
        status: str,
        health: str,
        data: Optional[dict] = None
    ):
        """推送版本状态更新"""
        await self.broadcast(
            WebSocketMessage(
                type=MessageType.VERSION_UPDATE,
                data={
                    "version_id": version_id,
                    "status": status,
                    "health": health,
                    **(data or {})
                }
            ),
            channel=f"versions:{version_id}"
        )

    # ============================================
    # 后台任务
    # ============================================

    async def start_ping_task(self, interval: int = 30):
        """启动心跳检测任务"""
        async def ping_task():
            while True:
                await asyncio.sleep(interval)
                now = datetime.utcnow()
                for conn_id, conn in list(self.connections.items()):
                    if (now - conn.last_ping).total_seconds() > interval * 3:
                        # 超时断开
                        self.disconnect(conn)
                    else:
                        await conn.send(WebSocketMessage(type=MessageType.PING))

        self._background_tasks.append(asyncio.create_task(ping_task()))

    async def start_demo_task(self):
        """启动演示任务（模拟实时数据）"""
        async def demo_task():
            import random
            while True:
                await asyncio.sleep(5)

                # 随机推送部署更新
                if self.connections:
                    deployment_id = f"dep-{random.randint(1, 10)}"
                    statuses = ["pending", "running", "success", "failed"]
                    await self.push_deployment_update(
                        deployment_id,
                        random.choice(statuses),
                        {"progress": random.randint(0, 100)}
                    )

        self._background_tasks.append(asyncio.create_task(demo_task()))


# 全局 WebSocket 管理器
ws_manager = WebSocketManager()
