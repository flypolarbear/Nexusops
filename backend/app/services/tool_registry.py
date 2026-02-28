"""
NexusOps - Tool Registry Service

Aggregates tools from all built-in agents for LLM Function Calling.
"""

from typing import Dict, List, Any, Optional
import logging

from app.gateway.executor.builtin import BuiltinExecutor

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool Registry for LLM Function Calling.
    
    Aggregates tools from all registered agents and provides
    them in a format suitable for LLM function calling.
    """
    
    def __init__(self):
        self._executor = BuiltinExecutor()
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
    
    def get_all_tools(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all available tools from all agents.
        
        Args:
            refresh: Force refresh the cache
            
        Returns:
            List of tool definitions in LLM function calling format
        """
        if self._tools_cache is not None and not refresh:
            return self._tools_cache
        
        tools = []
        seen_names = set()
        
        for agent_id in self._executor.list_agents():
            agent_info = self._executor.get_agent_info(agent_id)
            if not agent_info:
                continue
            
            agent_tools = agent_info.get("tools", [])
            for tool in agent_tools:
                tool_name = tool.get("name")
                if tool_name and tool_name not in seen_names:
                    # Convert to LLM function calling format
                    llm_tool = self._convert_to_llm_format(tool)
                    tools.append(llm_tool)
                    seen_names.add(tool_name)
        
        self._tools_cache = tools
        logger.info(f"Tool registry loaded {len(tools)} tools from {len(self._executor.list_agents())} agents")
        return tools
    
    def get_tools_for_agents(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get tools for specific agents.
        
        Args:
            agent_ids: List of agent IDs to get tools from
            
        Returns:
            List of tool definitions
        """
        tools = []
        seen_names = set()
        
        for agent_id in agent_ids:
            agent_info = self._executor.get_agent_info(agent_id)
            if not agent_info:
                continue
            
            agent_tools = agent_info.get("tools", [])
            for tool in agent_tools:
                tool_name = tool.get("name")
                if tool_name and tool_name not in seen_names:
                    llm_tool = self._convert_to_llm_format(tool)
                    tools.append(llm_tool)
                    seen_names.add(tool_name)
        
        return tools
    
    def get_agent_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Find which agent owns a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Agent ID that owns the tool, or None if not found
        """
        for agent_id in self._executor.list_agents():
            agent_info = self._executor.get_agent_info(agent_id)
            if not agent_info:
                continue
            
            agent_tools = agent_info.get("tools", [])
            for tool in agent_tools:
                if tool.get("name") == tool_name:
                    return agent_id
        
        return None
    
    def _convert_to_llm_format(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert internal tool format to LLM function calling format.
        
        GLM/OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "Tool description",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
        """
        input_schema = tool.get("inputSchema", {})
        
        return {
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": {
                    "type": input_schema.get("type", "object"),
                    "properties": input_schema.get("properties", {}),
                    "required": input_schema.get("required", []),
                }
            }
        }
    
    def list_available_agents(self) -> List[str]:
        """List all available agent IDs"""
        return self._executor.list_agents()
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        return self._executor.get_agent_info(agent_id)


# Singleton instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the tool registry singleton"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def reset_tool_registry():
    """Reset the tool registry singleton (for testing)"""
    global _tool_registry
    _tool_registry = None
