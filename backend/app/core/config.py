"""
NexusOps Backend - Configuration
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "NexusOps"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # API
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexusops:nexusops@localhost:5432/nexusops"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "RS256"

    # Agent
    AGENT_EXECUTION_TIMEOUT: int = 30
    AGENT_MAX_CONCURRENT: int = 10

    # External Services
    ARGOCD_URL: str = "https://argocd.example.com"
    ARGOCD_TOKEN: str = ""
    JENKINS_URL: str = "https://jenkins.example.com"
    JENKINS_TOKEN: str = ""
    GITHUB_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
