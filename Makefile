.PHONY: all dev backend backend-chat frontend docker-up docker-down docker-logs clean test architect developer agent-help test-monitor

# Default target
all: dev

# Start everything for development
dev: docker-up
	@echo "Starting backend..."
	@cd backend && uvicorn app.main:app --reload --port 8000 &
	@echo "Starting frontend..."
	@cd frontend && npm run dev

# Backend only
backend:
	@cd backend && uvicorn app.main:app --reload --port 8000

backend-chat:
	@$(MAKE) backend

# Frontend only
frontend:
	@cd frontend && npm run dev

# Install dependencies
install:
	@cd backend && python -m pip install -r requirements.txt
	@cd frontend && npm install

# Docker
docker-up:
	@cd docker && docker-compose -f docker-compose.middleware.yml up -d

docker-down:
	@cd docker && docker-compose -f docker-compose.middleware.yml down

docker-logs:
	@cd docker && docker-compose -f docker-compose.middleware.yml logs -f

# Database
db-init:
	@cd docker && PGPASSWORD=nexusops psql -h localhost -U nexusops -d nexusops -f scripts/init-db.sql

db-reset:
	@cd docker && docker-compose -f docker-compose.middleware.yml down -v && docker-compose -f docker-compose.middleware.yml up -d postgres

# Build
build-backend:
	@cd backend && python -m compileall app

build-frontend:
	@cd frontend && npm run build

build: build-backend build-frontend

# Test
test-backend:
	@cd backend && pytest tests/ -v

test-frontend:
	@cd frontend && npm run test

test: test-backend test-frontend

# Lint
lint-backend:
	@cd backend && ruff check . --fix && black . && mypy app/

lint-frontend:
	@cd frontend && npm run lint

lint: lint-backend lint-frontend

# Clean
clean:
	@rm -rf backend/.mypy_cache
	@rm -rf backend/__pycache__
	@rm -rf frontend/dist
	@rm -rf frontend/node_modules

# Agent Team
architect:
	@./scripts/architect.sh

developer:
	@./scripts/developer.sh

test-monitor:
	@./scripts/start_test_monitor.sh

agent-help:
	@echo "Agent Team Commands:"
	@echo "  make architect    - 启动 Architect Agent (Claude Opus)"
	@echo "  make developer    - 启动 Developer Agent (GLM-5)"
	@echo "  make test-monitor - 启动测试监控 Agent (周期性运行测试)"
	@echo ""
	@echo "直接运行脚本:"
	@echo "  ./scripts/architect.sh   - 架构设计与代码审查"
	@echo "  ./scripts/developer.sh   - 日常开发工作"
	@echo "  ./scripts/start_test_monitor.sh - 测试监控服务"

# Help
help:
	@echo "Available targets:"
	@echo "  make dev          - Start full development environment"
	@echo "  make backend      - Start FastAPI backend"
	@echo "  make frontend     - Start frontend only"
	@echo "  make install      - Install all dependencies"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make build        - Build all services"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Agent Team:"
	@echo "  make architect    - 启动 Architect Agent (Claude Opus)"
	@echo "  make developer    - 启动 Developer Agent (GLM-5)"
	@echo "  make test-monitor - 启动测试监控 Agent (Web Dashboard: http://localhost:8765)"
