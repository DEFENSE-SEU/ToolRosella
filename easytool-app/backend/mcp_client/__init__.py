"""
MCP Client Module

Provides components for interacting with Model Context Protocol (MCP) services:

Components:
- connection_manager: MCP session management with connection pooling
- config: Configuration loading from mcp.json
- tool_catalog: Tool metadata and caching (Stage 2)
- argument_mapper: Parameter mapping (Stage 2)
- tool_searcher: Tool search and filtering (Stage 3)
- service_inference: Smart service selection (Stage 3)

Quick Start:

```python
from mcp_client import MCPConnectionManager, load_mcp_services

# Load configuration
services_config = load_mcp_services()

# Create manager
mcp_manager = MCPConnectionManager(services_config)
await mcp_manager.initialize()

# List tools
tools = await mcp_manager.list_tools("vaderSentiment")

# Call tool
result = await mcp_manager.call_tool(
    "vaderSentiment",
    "analyze_sentiment",
    {"text": "I love this!"}
)

# Cleanup
await mcp_manager.shutdown()
```
"""

from .connection_manager import MCPConnectionManager, ToolInfo, ToolResult
from .config import ServiceConfig, load_mcp_services

__all__ = [
    "MCPConnectionManager",
    "ToolInfo",
    "ToolResult",
    "ServiceConfig",
    "load_mcp_services",
]

__version__ = "0.1.0"
