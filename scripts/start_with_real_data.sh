#!/bin/bash
# NexusOps 启动脚本 - 使用真实数据测试
# 用法: ./scripts/start_with_real_data.sh [选项]
#
# 选项:
#   --skip-infra    跳过基础设施启动 (假设已运行)
#   --skip-tests    跳过验证测试
#   --dry-run       只显示将执行的命令，不实际执行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 默认参数
SKIP_INFRA=false
SKIP_TESTS=false
DRY_RUN=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-infra)
            SKIP_INFRA=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "用法: ./scripts/start_with_real_data.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --skip-infra    跳过基础设施启动 (假设 PostgreSQL/Redis 已运行)"
            echo "  --skip-tests    跳过验证测试"
            echo "  --dry-run       只显示将执行的命令"
            echo "  --help          显示帮助"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

# 干运行模式
run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] $1"
    else
        eval "$1"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口可用
    fi
}

# 等待端口就绪
wait_for_port() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=0

    log_info "等待 $service 在端口 $port 就绪..."
    while ! check_port $port; do
        attempt=$((attempt + 1))
        if [ $attempt -ge $max_attempts ]; then
            log_error "$service 启动超时"
            return 1
        fi
        sleep 1
    done
    log_success "$service 已就绪 (端口 $port)"
}

echo ""
echo "=========================================="
echo "  NexusOps 真实数据测试启动脚本"
echo "=========================================="
echo ""

# ============================================
# 1. 启动基础设施 (PostgreSQL + Redis)
# ============================================
if [ "$SKIP_INFRA" = false ]; then
    log_info "启动基础设施服务..."

    cd docker

    # 检查 Docker 是否运行
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi

    # 启动 PostgreSQL 和 Redis
    run_cmd "docker-compose -f docker-compose.middleware.yml up -d postgres redis"

    cd "$PROJECT_DIR"

    # 等待服务就绪
    if [ "$DRY_RUN" = false ]; then
        sleep 3
        wait_for_port 5432 "PostgreSQL"
        wait_for_port 6379 "Redis"
    fi
else
    log_warn "跳过基础设施启动 (--skip-infra)"
fi

# ============================================
# 2. 启动后端服务
# ============================================
log_info "启动后端服务..."

cd backend

# 检查虚拟环境
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    log_info "创建 Python 虚拟环境..."
    run_cmd "python3 -m venv .venv"
    run_cmd "source .venv/bin/activate && pip install -r requirements.txt"
fi

# 激活虚拟环境并启动后端
if [ -d ".venv" ]; then
    VENV_PATH=".venv"
elif [ -d "venv" ]; then
    VENV_PATH="venv"
fi

if [ "$DRY_RUN" = false ]; then
    # 检查后端是否已运行
    if check_port 8000; then
        log_warn "后端服务已在运行 (端口 8000)"
    else
        source $VENV_PATH/bin/activate
        nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > /tmp/nexusops-backend.pid
        deactivate
        wait_for_port 8000 "Backend API"
    fi
else
    echo "[DRY-RUN] source $VENV_PATH/bin/activate"
    echo "[DRY-RUN] uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

cd "$PROJECT_DIR"

# ============================================
# 3. 启动前端服务
# ============================================
log_info "启动前端服务..."

cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    run_cmd "npm install"
fi

if [ "$DRY_RUN" = false ]; then
    # 检查前端是否已运行
    if check_port 3000; then
        log_warn "前端服务已在运行 (端口 3000)"
    else
        nohup npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > /tmp/nexusops-frontend.pid
        wait_for_port 3000 "Frontend"
    fi
else
    echo "[DRY-RUN] npm run dev"
fi

cd "$PROJECT_DIR"

# ============================================
# 4. 验证测试 (使用真实数据)
# ============================================
if [ "$SKIP_TESTS" = false ] && [ "$DRY_RUN" = false ]; then
    echo ""
    log_info "开始验证测试 (真实数据)..."
    echo ""

    # 4.1 健康检查
    log_test "测试 1: 健康检查"
    HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        log_success "  ✅ 后端健康检查通过"
    else
        log_error "  ❌ 后端健康检查失败"
    fi

    # 4.2 AI 配置测试 (真实 GLM API)
    log_test "测试 2: AI 配置 (GLM)"
    AI_CONFIG=$(curl -s http://localhost:8000/api/v1/ai/config 2>/dev/null)
    if echo "$AI_CONFIG" | grep -q "configured"; then
        log_success "  ✅ AI 配置已加载: $(echo "$AI_CONFIG" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d.get(\"provider\",\"?\")}/{d.get(\"model\",\"?\")}')")"
    else
        log_warn "  ⚠️ AI 配置未设置"
    fi

    # 4.3 AI 连接测试 (真实 API 调用)
    log_test "测试 3: AI 连接测试 (真实 GLM API)"
    AI_TEST=$(curl -s -X POST http://localhost:8000/api/v1/ai/test 2>/dev/null)
    if echo "$AI_TEST" | grep -q "success.*true\|Successfully connected"; then
        log_success "  ✅ GLM API 连接成功"
    else
        log_error "  ❌ GLM API 连接失败: $AI_TEST"
    fi

    # 4.4 Chat Agent 测试 (真实 AI 响应)
    log_test "测试 4: Chat Agent (真实 AI 响应)"
    CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agents/nexusops.chat/invoke \
        -H "Content-Type: application/json" \
        -d '{"request_id":"test-001","conversation_id":"test","agent_id":"nexusops.chat","query":"1+1=?"}' 2>/dev/null)
    if echo "$CHAT_RESPONSE" | grep -q "success.*success\|2\|两"; then
        log_success "  ✅ Chat Agent 正常响应"
    else
        log_warn "  ⚠️ Chat Agent 响应异常"
    fi

    # 4.5 集成连接测试 (K8s)
    log_test "测试 5: Kubernetes 连接测试"
    K8S_TEST=$(curl -s -X POST "http://localhost:8000/api/v1/integrations/type/kubernetes/test" 2>/dev/null)
    if echo "$K8S_TEST" | grep -q "success.*true\|connected"; then
        log_success "  ✅ K8s 连接成功"
    else
        log_warn "  ⚠️ K8s 连接失败 (可能未配置 kubeconfig)"
    fi

    # 4.6 数据库连接测试
    log_test "测试 6: 数据库连接"
    DB_TEST=$(curl -s http://localhost:8000/api/v1/projects 2>/dev/null)
    if [ -n "$DB_TEST" ] && ! echo "$DB_TEST" | grep -q "error\|Error"; then
        log_success "  ✅ 数据库连接正常"
    else
        log_error "  ❌ 数据库连接失败"
    fi

    # 4.7 Redis 连接测试
    log_test "测试 7: Redis 连接"
    REDIS_PING=$(docker exec nexusops-redis redis-cli ping 2>/dev/null)
    if [ "$REDIS_PING" = "PONG" ]; then
        log_success "  ✅ Redis 连接正常"
    else
        log_warn "  ⚠️ Redis 连接异常"
    fi

    # 4.8 前端页面测试
    log_test "测试 8: 前端页面"
    FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
    if [ "$FRONTEND_TEST" = "200" ]; then
        log_success "  ✅ 前端页面正常 (HTTP $FRONTEND_TEST)"
    else
        log_error "  ❌ 前端页面异常 (HTTP $FRONTEND_TEST)"
    fi

    echo ""
fi

# ============================================
# 5. 显示服务信息
# ============================================
echo ""
echo "=========================================="
echo -e "${GREEN}  NexusOps 启动完成!${NC}"
echo "=========================================="
echo ""
echo "服务地址:"
echo "  前端:      http://localhost:3000"
echo "  后端 API:  http://localhost:8000"
echo "  API 文档:  http://localhost:8000/docs"
echo "  PostgreSQL: localhost:5432 (nexusops/nexusops)"
echo "  Redis:     localhost:6379"
echo ""
echo "日志文件:"
echo "  后端: logs/backend.log"
echo "  前端: logs/frontend.log"
echo ""
echo "停止服务:"
echo "  ./scripts/start_with_real_data.sh --stop"
echo ""

# ============================================
# 停止服务选项
# ============================================
if [ "${1:-}" = "--stop" ]; then
    log_info "停止所有服务..."

    # 停止后端
    if [ -f /tmp/nexusops-backend.pid ]; then
        kill $(cat /tmp/nexusops-backend.pid) 2>/dev/null || true
        rm /tmp/nexusops-backend.pid
    fi
    pkill -f "uvicorn app.main:app" 2>/dev/null || true

    # 停止前端
    if [ -f /tmp/nexusops-frontend.pid ]; then
        kill $(cat /tmp/nexusops-frontend.pid) 2>/dev/null || true
        rm /tmp/nexusops-frontend.pid
    fi
    pkill -f "vite" 2>/dev/null || true

    # 停止 Docker 服务
    cd docker
    docker-compose -f docker-compose.middleware.yml down
    cd "$PROJECT_DIR"

    log_success "所有服务已停止"
    exit 0
fi
