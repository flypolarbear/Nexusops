"""
NexusOps Adapters - Base Class

All external system adapters must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAdapter(ABC):
    """
    Base class for external system adapters.
    
    Responsibilities:
    1. Encapsulate external API calls
    2. Handle authentication and configuration
    3. Standardize error handling
    4. Return normalized results
    """
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the adapter can connect to the external system.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def _success(
        self, 
        data: Any, 
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a success result"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
    
    def _error(
        self, 
        error: str, 
        code: str = "UNKNOWN",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return an error result"""
        return {
            "success": False,
            "error": error,
            "code": code,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }


# Import all adapters
from app.adapters.kubernetes import KubernetesAdapter

__all__ = [
    "BaseAdapter",
    "KubernetesAdapter",
]
