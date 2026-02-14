.PHONY: all dev backend frontend docker-up docker-down clean test

# Default target
all: dev

# Start everything for development
dev: docker-up
	@echo "Starting backend..."
	@cd backend && go run ./cmd/api-gateway &
	@cd backend && go run ./cmd/chat-gateway &
	@echo "Starting frontend..."
	@cd frontend && npm run dev

# Backend only
backend:
	@cd backend && go run ./cmd/api-gateway

backend-chat:
	@cd backend && go run ./cmd/chat-gateway

# Frontend only
frontend:
	@cd frontend && npm run dev

# Install dependencies
install:
	@cd backend && go mod download
	@cd frontend && npm install

# Docker
docker-up:
	@cd backend/deployments/docker && docker-compose up -d

docker-down:
	@cd backend/deployments/docker && docker-compose down

docker-logs:
	@cd backend/deployments/docker && docker-compose logs -f

# Database
db-init:
	@cd backend/deployments/docker && PGPASSWORD=nexusops_dev psql -h localhost -U nexusops -d nexusops -f init-db.sql

db-reset:
	@cd backend/deployments/docker && docker-compose down -v && docker-compose up -d postgres

# Build
build-backend:
	@cd backend && go build -o bin/api-gateway ./cmd/api-gateway
	@cd backend && go build -o bin/chat-gateway ./cmd/chat-gateway

build-frontend:
	@cd frontend && npm run build

build: build-backend build-frontend

# Test
test-backend:
	@cd backend && go test ./... -v

test-frontend:
	@cd frontend && npm run test

test: test-backend test-frontend

# Lint
lint-backend:
	@cd backend && go vet ./...

lint-frontend:
	@cd frontend && npm run lint

lint: lint-backend lint-frontend

# Clean
clean:
	@rm -rf backend/bin
	@rm -rf frontend/dist
	@rm -rf frontend/node_modules

# Help
help:
	@echo "Available targets:"
	@echo "  make dev          - Start full development environment"
	@echo "  make backend      - Start API gateway only"
	@echo "  make frontend     - Start frontend only"
	@echo "  make install      - Install all dependencies"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"
	@echo "  make build        - Build all services"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linters"
	@echo "  make clean        - Clean build artifacts"
