#!/bin/bash
# NexusOps Development Environment Startup Script
# Usage: ./init.sh [option]
#
# Options:
#   all       - Start all services (default)
#   infra     - Start infrastructure only (postgres, redis, etc.)
#   backend   - Start backend services only
#   frontend  - Start frontend only
#   stop      - Stop all services
#   status    - Show service status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_dependencies() {
    log_info "Checking dependencies..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check Go
    if ! command -v go &> /dev/null; then
        log_warn "Go is not installed. Backend services will not start."
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_warn "Node.js is not installed. Frontend will not start."
    fi

    log_success "Dependencies check passed"
}

start_infra() {
    log_info "Starting infrastructure services..."
    cd backend/deployments/docker

    # Start core services
    docker-compose up -d postgres redis grafana prometheus

    log_info "Waiting for services to be healthy..."
    sleep 5

    # Check if postgres is ready
    until docker-compose exec -T postgres pg_isready -U nexusops; do
        log_info "Waiting for PostgreSQL..."
        sleep 2
    done

    log_success "Infrastructure services started"
    log_info "  - PostgreSQL: localhost:5432"
    log_info "  - Redis: localhost:6379"
    log_info "  - Grafana: http://localhost:3001 (admin/admin)"
    log_info "  - Prometheus: http://localhost:9090"

    cd "$SCRIPT_DIR"
}

start_backend() {
    log_info "Starting backend services..."

    cd backend

    # Download dependencies
    if [ ! -d "vendor" ]; then
        log_info "Downloading Go dependencies..."
        go mod download
    fi

    # Start API Gateway
    log_info "Starting API Gateway on port 8080..."
    go run ./cmd/api-gateway &
    API_PID=$!
    echo $API_PID > /tmp/nexusops-api.pid

    # Start Chat Gateway
    log_info "Starting Chat Gateway on port 8081..."
    go run ./cmd/chat-gateway &
    CHAT_PID=$!
    echo $CHAT_PID > /tmp/nexusops-chat.pid

    cd "$SCRIPT_DIR"
    log_success "Backend services started"
    log_info "  - API Gateway: http://localhost:8080"
    log_info "  - Chat Gateway: ws://localhost:8081"
}

start_frontend() {
    log_info "Starting frontend..."

    cd frontend

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm install
    fi

    # Start dev server
    log_info "Starting Vite dev server..."
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/nexusops-frontend.pid

    cd "$SCRIPT_DIR"
    log_success "Frontend started"
    log_info "  - Frontend: http://localhost:3000"
}

stop_services() {
    log_info "Stopping all services..."

    # Stop backend processes
    if [ -f /tmp/nexusops-api.pid ]; then
        kill $(cat /tmp/nexusops-api.pid) 2>/dev/null || true
        rm /tmp/nexusops-api.pid
    fi
    if [ -f /tmp/nexusops-chat.pid ]; then
        kill $(cat /tmp/nexusops-chat.pid) 2>/dev/null || true
        rm /tmp/nexusops-chat.pid
    fi
    if [ -f /tmp/nexusops-frontend.pid ]; then
        kill $(cat /tmp/nexusops-frontend.pid) 2>/dev/null || true
        rm /tmp/nexusops-frontend.pid
    fi

    # Stop Docker services
    cd backend/deployments/docker
    docker-compose down
    cd "$SCRIPT_DIR"

    log_success "All services stopped"
}

show_status() {
    log_info "Service Status:"
    echo ""

    # Check Docker services
    cd backend/deployments/docker
    docker-compose ps
    cd "$SCRIPT_DIR"

    echo ""

    # Check backend processes
    if pgrep -f "api-gateway" > /dev/null; then
        log_success "API Gateway: Running"
    else
        log_warn "API Gateway: Not running"
    fi

    if pgrep -f "chat-gateway" > /dev/null; then
        log_success "Chat Gateway: Running"
    else
        log_warn "Chat Gateway: Not running"
    fi

    if pgrep -f "vite" > /dev/null; then
        log_success "Frontend: Running"
    else
        log_warn "Frontend: Not running"
    fi
}

show_urls() {
    echo ""
    log_info "Service URLs:"
    echo "  Frontend:      http://localhost:3000"
    echo "  API Gateway:   http://localhost:8080"
    echo "  Chat Gateway:  ws://localhost:8081"
    echo "  Grafana:       http://localhost:3001 (admin/admin)"
    echo "  Prometheus:    http://localhost:9090"
    echo "  PostgreSQL:    localhost:5432 (nexusops/nexusops_dev)"
    echo "  Redis:         localhost:6379"
    echo ""
}

# Main
case "${1:-all}" in
    all)
        check_dependencies
        start_infra
        start_backend
        start_frontend
        show_urls
        ;;
    infra)
        check_dependencies
        start_infra
        show_urls
        ;;
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {all|infra|backend|frontend|stop|status}"
        exit 1
        ;;
esac
