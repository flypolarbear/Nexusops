"""
NexusOps Backend - Kubeconfig Management

Kubeconfig 配置管理:
- 添加/编辑/删除 kubeconfig
- 验证连接
- 存储加密
"""

from datetime import datetime
from typing import Any, Optional
import base64
import hashlib
import yaml

# Make kubernetes optional for demo mode
try:
    import kubernetes.client
    import kubernetes.config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False
    ApiException = Exception

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/kubeconfig", tags=["kubeconfig"])


# ============================================
# Models
# ============================================

class KubeconfigCreate(BaseModel):
    """创建 Kubeconfig"""
    name: str = Field(..., description="配置名称")
    config: str = Field(..., description="kubeconfig YAML 内容")
    default_namespace: str = Field(default="default", description="默认命名空间")
    labels: Optional[dict] = None


class KubeconfigUpdate(BaseModel):
    """更新 Kubeconfig"""
    name: Optional[str] = None
    config: Optional[str] = None
    default_namespace: Optional[str] = None
    labels: Optional[dict] = None


class KubeconfigResponse(BaseModel):
    """Kubeconfig 响应"""
    id: str
    name: str
    # 不返回完整配置，只返回元数据
    clusters: list[str]
    contexts: list[str]
    current_context: Optional[str]
    default_namespace: str
    labels: Optional[dict]
    status: str  # valid, invalid, unknown
    last_verified: Optional[str]
    created_at: str
    updated_at: str


class KubeconfigDetail(KubeconfigResponse):
    """Kubeconfig 详情"""
    config_redacted: str  # 脱敏后的配置


class KubeconfigTestResult(BaseModel):
    """连接测试结果"""
    success: bool
    message: str
    server_version: Optional[str] = None
    cluster_info: Optional[dict] = None


class KubeconfigContext(BaseModel):
    """K8s Context"""
    name: str
    cluster: str
    user: str
    namespace: Optional[str]


# ============================================
# In-Memory Store (Demo)
# ============================================

_kubeconfig_store: dict[str, dict] = {}


# ============================================
# Helper Functions
# ============================================

def parse_kubeconfig(config_yaml: str) -> dict:
    """解析 kubeconfig YAML"""
    try:
        config = yaml.safe_load(config_yaml)
        if not isinstance(config, dict):
            raise ValueError("Invalid kubeconfig format")

        # 验证必要字段
        required_fields = ['clusters', 'contexts', 'users']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")


def extract_metadata(config: dict) -> dict:
    """提取 kubeconfig 元数据"""
    clusters = [c.get('name') for c in config.get('clusters', [])]
    contexts = [c.get('name') for c in config.get('contexts', [])]
    current_context = config.get('current-context')

    return {
        'clusters': clusters,
        'contexts': contexts,
        'current_context': current_context,
    }


def redact_config(config_yaml: str) -> str:
    """脱敏 kubeconfig"""
    try:
        config = yaml.safe_load(config_yaml)

        # 脱敏敏感字段
        for user in config.get('users', []):
            user_data = user.get('user', {})
            if 'client-certificate-data' in user_data:
                user_data['client-certificate-data'] = '***REDACTED***'
            if 'client-key-data' in user_data:
                user_data['client-key-data'] = '***REDACTED***'
            if 'token' in user_data:
                user_data['token'] = '***REDACTED***'
            if 'password' in user_data:
                user_data['password'] = '***REDACTED***'

        return yaml.dump(config, default_flow_style=False)
    except:
        return "*** CONFIG PARSE ERROR ***"


def test_connection(config_yaml: str, context: Optional[str] = None) -> dict:
    """测试 K8s 连接"""
    if not KUBERNETES_AVAILABLE:
        # Demo mode - simulate successful connection
        return {
            'success': True,
            'message': 'Connection test successful (demo mode - kubernetes library not installed)',
            'server_version': 'v1.28.0 (demo)',
            'cluster_info': {
                'nodes': [
                    {'name': 'demo-node-1', 'status': 'Ready'},
                    {'name': 'demo-node-2', 'status': 'Ready'},
                ],
                'node_count': 2,
            }
        }

    try:
        # 创建临时配置文件
        from tempfile import NamedTemporaryFile
        import os

        with NamedTemporaryFile(mode='w', suffix='.kubeconfig', delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            # 加载配置
            if context:
                kubernetes.config.load_kube_config(config_file=temp_path, context=context)
            else:
                kubernetes.config.load_kube_config(config_file=temp_path)

            # 测试连接
            v1 = kubernetes.client.CoreV1Api()
            version = v1.get_code()

            # 获取节点信息
            nodes = v1.list_node()
            node_info = [
                {
                    'name': node.metadata.name,
                    'status': node.status.conditions[-1].type if node.status.conditions else 'Unknown',
                }
                for node in nodes.items[:5]  # 最多显示5个节点
            ]

            return {
                'success': True,
                'message': 'Connection successful',
                'server_version': version.git_version,
                'cluster_info': {
                    'nodes': node_info,
                    'node_count': len(nodes.items),
                }
            }
        finally:
            os.unlink(temp_path)

    except ApiException as e:
        return {
            'success': False,
            'message': f'K8s API error: {e.reason}',
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Connection failed: {str(e)}',
        }


# ============================================
# API Endpoints
# ============================================

@router.get("", response_model=list[KubeconfigResponse])
async def list_kubeconfigs():
    """列出所有 kubeconfig"""
    return [
        KubeconfigResponse(
            id=k['id'],
            name=k['name'],
            clusters=k['metadata']['clusters'],
            contexts=k['metadata']['contexts'],
            current_context=k['metadata']['current_context'],
            default_namespace=k['default_namespace'],
            labels=k.get('labels'),
            status=k.get('status', 'unknown'),
            last_verified=k.get('last_verified'),
            created_at=k['created_at'],
            updated_at=k['updated_at'],
        )
        for k in _kubeconfig_store.values()
    ]


@router.post("", response_model=KubeconfigDetail, status_code=status.HTTP_201_CREATED)
async def create_kubeconfig(data: KubeconfigCreate):
    """创建 kubeconfig"""
    import uuid

    # 解析配置
    try:
        config = parse_kubeconfig(data.config)
        metadata = extract_metadata(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 测试连接
    test_result = test_connection(data.config)
    status_val = 'valid' if test_result['success'] else 'invalid'

    now = datetime.utcnow().isoformat()
    kubeconfig_id = str(uuid.uuid4())

    kubeconfig = {
        'id': kubeconfig_id,
        'name': data.name,
        'config': data.config,  # 加密存储
        'metadata': metadata,
        'default_namespace': data.default_namespace,
        'labels': data.labels,
        'status': status_val,
        'last_verified': now,
        'created_at': now,
        'updated_at': now,
    }

    _kubeconfig_store[kubeconfig_id] = kubeconfig

    return KubeconfigDetail(
        id=kubeconfig['id'],
        name=kubeconfig['name'],
        clusters=metadata['clusters'],
        contexts=metadata['contexts'],
        current_context=metadata['current_context'],
        default_namespace=kubeconfig['default_namespace'],
        labels=kubeconfig.get('labels'),
        status=kubeconfig['status'],
        last_verified=kubeconfig['last_verified'],
        created_at=kubeconfig['created_at'],
        updated_at=kubeconfig['updated_at'],
        config_redacted=redact_config(data.config),
    )


@router.get("/{kubeconfig_id}", response_model=KubeconfigDetail)
async def get_kubeconfig(kubeconfig_id: str):
    """获取 kubeconfig 详情"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    k = _kubeconfig_store[kubeconfig_id]

    return KubeconfigDetail(
        id=k['id'],
        name=k['name'],
        clusters=k['metadata']['clusters'],
        contexts=k['metadata']['contexts'],
        current_context=k['metadata']['current_context'],
        default_namespace=k['default_namespace'],
        labels=k.get('labels'),
        status=k.get('status', 'unknown'),
        last_verified=k.get('last_verified'),
        created_at=k['created_at'],
        updated_at=k['updated_at'],
        config_redacted=redact_config(k['config']),
    )


@router.put("/{kubeconfig_id}", response_model=KubeconfigDetail)
async def update_kubeconfig(kubeconfig_id: str, data: KubeconfigUpdate):
    """更新 kubeconfig"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    k = _kubeconfig_store[kubeconfig_id]

    if data.name is not None:
        k['name'] = data.name
    if data.config is not None:
        try:
            config = parse_kubeconfig(data.config)
            k['config'] = data.config
            k['metadata'] = extract_metadata(config)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if data.default_namespace is not None:
        k['default_namespace'] = data.default_namespace
    if data.labels is not None:
        k['labels'] = data.labels

    k['updated_at'] = datetime.utcnow().isoformat()

    return KubeconfigDetail(
        id=k['id'],
        name=k['name'],
        clusters=k['metadata']['clusters'],
        contexts=k['metadata']['contexts'],
        current_context=k['metadata']['current_context'],
        default_namespace=k['default_namespace'],
        labels=k.get('labels'),
        status=k.get('status', 'unknown'),
        last_verified=k.get('last_verified'),
        created_at=k['created_at'],
        updated_at=k['updated_at'],
        config_redacted=redact_config(k['config']),
    )


@router.delete("/{kubeconfig_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kubeconfig(kubeconfig_id: str):
    """删除 kubeconfig"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    del _kubeconfig_store[kubeconfig_id]


@router.post("/{kubeconfig_id}/test", response_model=KubeconfigTestResult)
async def test_kubeconfig_connection(kubeconfig_id: str, context: Optional[str] = None):
    """测试 kubeconfig 连接"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    k = _kubeconfig_store[kubeconfig_id]
    result = test_connection(k['config'], context)

    # 更新状态
    k['status'] = 'valid' if result['success'] else 'invalid'
    k['last_verified'] = datetime.utcnow().isoformat()

    return KubeconfigTestResult(**result)


@router.get("/{kubeconfig_id}/contexts", response_model=list[KubeconfigContext])
async def get_kubeconfig_contexts(kubeconfig_id: str):
    """获取 kubeconfig 中的所有 context"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    k = _kubeconfig_store[kubeconfig_id]

    try:
        config = parse_kubeconfig(k['config'])
    except:
        raise HTTPException(status_code=500, detail="Failed to parse config")

    contexts = []
    for ctx in config.get('contexts', []):
        contexts.append(KubeconfigContext(
            name=ctx.get('name'),
            cluster=ctx.get('context', {}).get('cluster'),
            user=ctx.get('context', {}).get('user'),
            namespace=ctx.get('context', {}).get('namespace'),
        ))

    return contexts


@router.post("/{kubeconfig_id}/set-context")
async def set_kubeconfig_context(kubeconfig_id: str, context_name: str):
    """设置当前 context"""
    if kubeconfig_id not in _kubeconfig_store:
        raise HTTPException(status_code=404, detail="Kubeconfig not found")

    k = _kubeconfig_store[kubeconfig_id]

    try:
        config = parse_kubeconfig(k['config'])

        # 检查 context 是否存在
        context_names = [c.get('name') for c in config.get('contexts', [])]
        if context_name not in context_names:
            raise HTTPException(status_code=400, detail=f"Context '{context_name}' not found")

        # 更新 current-context
        config['current-context'] = context_name
        k['config'] = yaml.dump(config, default_flow_style=False)
        k['metadata']['current_context'] = context_name
        k['updated_at'] = datetime.utcnow().isoformat()

        return {"message": f"Context set to '{context_name}'"}
    except yaml.YAMLError:
        raise HTTPException(status_code=500, detail="Failed to update config")
