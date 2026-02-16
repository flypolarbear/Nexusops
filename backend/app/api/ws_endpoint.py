"""
NexusOps Backend - WebSocket API Router

OPT-001: WebSocket 端点
"""

from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

from app.api.websocket import ws_manager, WebSocketMessage, MessageType

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket 主端点

    连接后可以:
    1. 订阅频道: {"type": "subscribe", "data": {"channel": "deployments"}}
    2. 取消订阅: {"type": "unsubscribe", "data": {"channel": "deployments"}}
    3. 心跳: {"type": "ping"}

    可用频道:
    - deployments - 所有部署更新
    - deployments:{id} - 特定部署更新
    - versions - 所有版本更新
    - versions:{id} - 特定版本更新
    - alerts - 所有告警
    - alerts:{severity} - 特定严重级别的告警
    - conversations:{id} - Agent 对话流式响应
    """
    # TODO: 从 token 验证用户
    user_id = None
    if token:
        # 验证 token 并提取 user_id
        pass

    # 连接
    connection = await ws_manager.connect(websocket, user_id)

    try:
        # 处理消息
        await ws_manager.handle_connection(connection)
    except WebSocketDisconnect:
        ws_manager.disconnect(connection)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(connection)


# ============================================
# REST API for WebSocket info
# ============================================

from fastapi import APIRouter

rest_router = APIRouter(prefix="/ws", tags=["websocket"])


@rest_router.get("/channels")
async def list_channels():
    """列出可用的 WebSocket 频道"""
    return {
        "channels": [
            {
                "name": "deployments",
                "description": "所有部署状态更新",
                "pattern": "deployments",
            },
            {
                "name": "deployments:{id}",
                "description": "特定部署的状态更新",
                "pattern": "deployments:{deployment_id}",
            },
            {
                "name": "versions",
                "description": "所有版本状态更新",
                "pattern": "versions",
            },
            {
                "name": "versions:{id}",
                "description": "特定版本的状态更新",
                "pattern": "versions:{version_id}",
            },
            {
                "name": "alerts",
                "description": "所有告警通知",
                "pattern": "alerts",
            },
            {
                "name": "alerts:{severity}",
                "description": "特定严重级别的告警",
                "pattern": "alerts:critical|warning|info",
            },
            {
                "name": "conversations:{id}",
                "description": "Agent 对话流式响应",
                "pattern": "conversations:{conversation_id}",
            },
        ]
    }


@rest_router.get("/connections")
async def list_connections():
    """列出当前活跃的 WebSocket 连接（调试用）"""
    return {
        "active_connections": len(ws_manager.connections),
        "connections": [
            {
                "id": conn.id,
                "user_id": conn.user_id,
                "subscriptions": list(conn.subscriptions),
                "is_active": conn.is_active,
            }
            for conn in ws_manager.connections.values()
        ]
    }
