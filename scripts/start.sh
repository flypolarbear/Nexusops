#!/bin/bash

# NexusOps 启动脚本

set -e

echo "=========================================="
echo "       NexusOps 启动脚本"
echo "=========================================="

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 解析参数
FRONTEND=true
BACKEND=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend-only)
            BACKEND=false
            shift
            ;;
        --backend-only)
            FRONTEND=false
            shift
            ;;
        --help)
            echo "用法: ./scripts/start.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --frontend-only  只启动前端"
            echo "  --backend-only   只启动后端"
            echo "  --help          显示帮助"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 启动后端
if [ "$BACKEND" = true ]; then
    echo -e "${YELLOW}[后端] 检查 Python 环境...${NC}"

    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo -e "${RED}[后端] 错误: 未找到 Python${NC}"
        exit 1
    fi

    echo -e "${GREEN}[后端] Python: $($PYTHON_CMD --version)${NC}"

    # 检查虚拟环境
    if [ ! -d "backend/venv" ]; then
        echo -e "${YELLOW}[后端] 创建虚拟环境...${NC}"
        cd backend
        $PYTHON_CMD -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    else
        echo -e "${GREEN}[后端] 虚拟环境已存在${NC}"
    fi

    # 启动后端
    echo -e "${GREEN}[后端] 启动中...${NC}"
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}[后端] 已启动 (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}[后端] API: http://localhost:8000${NC}"
    echo -e "${GREEN}[后端] 文档: http://localhost:8000/docs${NC}"
fi

# 启动前端
if [ "$FRONTEND" = true ]; then
    echo ""
    echo -e "${YELLOW}[前端] 检查依赖...${NC}"

    cd frontend

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[前端] 安装依赖...${NC}"
        npm install
    fi

    echo -e "${GREEN}[前端] 启动中...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    echo -e "${GREEN}[前端] 已启动 (PID: $FRONTEND_PID)${NC}"
    echo -e "${GREEN}[前端] URL: http://localhost:3000${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}NexusOps 启动完成!${NC}"
echo "=========================================="
echo ""

if [ "$FRONTEND" = true ]; then
    echo "前端: http://localhost:3000"
fi
if [ "$BACKEND" = true ]; then
    echo "后端: http://localhost:8000"
    echo "API:  http://localhost:8000/docs"
fi

echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待
wait
