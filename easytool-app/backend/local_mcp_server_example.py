"""
本地 MCP 测试服务器示例（依赖 mcp 内置的 SSE Transport + Starlette，无需 FastAPI）

用途: 在本地验证客户端链路，排除远程/代理问题。

启动:
    conda activate local-mcp
    python local_mcp_server_example.py

端点:
    SSE:      http://127.0.0.1:8001/mcp
    Messages: http://127.0.0.1:8001/mcp/messages/?session_id=...
"""

import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response

from mcp.server import Server
from mcp import types
from mcp.server.sse import SseServerTransport

# 创建 MCP 服务器
mcp_server = Server("local-test-mcp")


@mcp_server.list_tools()
async def list_tools():
    """列出可用的工具"""
    return [
        types.Tool(
            name="hello",
            description="Say hello to someone",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "The name to greet"}},
                "required": ["name"],
            },
        ),
        types.Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict):
    """调用工具"""
    if name == "hello":
        text = f"Hello, {arguments.get('name', 'World')}!"
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        text = f"{a} + {b} = {result}"
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])
    else:
        return types.CallToolResult(content=[types.TextContent(type="text", text=f"Unknown tool: {name}")])


async def handle_root(request):
    return JSONResponse({"service": "local-mcp-test-server", "status": "ok"})


def build_app():
    """
    使用 Starlette + SseServerTransport 提供 /mcp SSE 与 /mcp/messages POST
    """
    sse = SseServerTransport("/mcp/messages")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())
        return Response()

    routes = [
        Route("/", endpoint=handle_root, methods=["GET"]),
        Route("/mcp", endpoint=handle_sse, methods=["GET"]),
        Mount("/mcp/messages", app=sse.handle_post_message),
    ]

    return Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("LOCAL_MCP_PORT", "8001"))
    app = build_app()
    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║        Local MCP Test Server Starting                        ║
╠══════════════════════════════════════════════════════════════╣
║ 服务器地址: http://127.0.0.1:{port:<4}                           ║
║ MCP 端点:   http://127.0.0.1:{port}/mcp                        ║
╚══════════════════════════════════════════════════════════════╝
"""
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
