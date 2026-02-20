"""
NexusOps Backend - Main Application

Phase 3: 后端集成
- BE-001: 版本管理 API
- BE-002: ArgoCD 集成
- BE-003: CI/CD 集成
- BE-004: Agent Gateway
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, agent_market, cicd, deployments, projects, kubeconfig, integrations
from app.api.ws_endpoint import router as ws_router
from app.api.ws_endpoint import rest_router as ws_rest_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup - skip DB for demo
    # await init_db()
    yield
    # Shutdown
    # await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NexusOps Backend API - AI Native Operations Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix=settings.API_PREFIX)
app.include_router(deployments.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(cicd.router, prefix=settings.API_PREFIX)
app.include_router(agent_market.router, prefix=settings.API_PREFIX)
app.include_router(kubeconfig.router, prefix=settings.API_PREFIX)
app.include_router(integrations.router, prefix=settings.API_PREFIX)
app.include_router(ws_rest_router, prefix=settings.API_PREFIX)

# WebSocket endpoint (no prefix)
app.include_router(ws_router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    # Start WebSocket ping task
    from app.api.websocket import ws_manager
    await ws_manager.start_ping_task(interval=30)

    # Start demo task (for development)
    if settings.DEBUG:
        await ws_manager.start_demo_task()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": settings.API_PREFIX,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
