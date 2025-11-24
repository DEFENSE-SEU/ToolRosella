"""
EasyTool Backend with Remote MCP Service Integration

支持直接调用已部署在 HuggingFace Space 上的远程 MCP 服务
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入 MCP 连接管理器
try:
    from mcp_client import MCPConnectionManager, load_mcp_services
except ImportError:
    print("Error: mcp_client module not found. Make sure mcp_client/ is in the same directory.")
    sys.exit(1)


# ============================================================================
# 数据模型
# ============================================================================

class RunReq(BaseModel):
    """运行请求"""
    query: str
    service: Optional[str] = None  # 可选：指定使用的服务


class ToolCallReq(BaseModel):
    """工具调用请求"""
    tool_name: str
    arguments: Dict[str, Any] = {}


# ============================================================================
# 全局配置和管理器
# ============================================================================

# MCP 服务配置 - 从 mcp.json 加载
services_config: Dict[str, dict] = {}
mcp_manager: Optional[MCPConnectionManager] = None




# ============================================================================
# FastAPI 应用生命周期
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global services_config, mcp_manager

    # 启动事件
    print("Starting EasyTool Backend with MCP Integration...")
    try:
        services_config = load_mcp_services("mcp.json")
        print(f"Loaded {len(services_config)} MCP services from mcp.json")

        mcp_manager = MCPConnectionManager(services_config)
        await mcp_manager.initialize()
        print("MCP Manager initialized")
    except Exception as e:
        print(f"Error initializing MCP Manager: {e}")
        raise

    yield

    # 关闭事件
    print("Shutting down MCP Manager...")
    if mcp_manager:
        await mcp_manager.shutdown()
    print("Shutdown complete")


app = FastAPI(
    title="EasyTool Backend with MCP Integration",
    version="0.2.0",
    lifespan=lifespan
)

# 添加 CORS 支持（前端需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API 端点
# ============================================================================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "easytool-backend-mcp",
        "status": "ok",
        "version": "0.2.0"
    }


@app.get("/services")
async def list_services():
    """列出所有可用的 MCP 服务"""
    return {
        "services": {
            name: {
                "description": config.get("description", ""),
                "icon": config.get("icon", "🔧"),
                "url": config.get("url", "")
            }
            for name, config in services_config.items()
        }
    }


@app.get("/services/{service_name}/tools")
async def list_service_tools(service_name: str):
    """列出特定服务的所有工具"""
    if service_name not in services_config:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager not initialized")

    try:
        tools = await mcp_manager.list_tools(service_name)

        return {
            "success": True,
            "service": service_name,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema
                }
                for tool in tools
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_all_tools():
    """列出所有服务的工具"""
    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager not initialized")

    all_tools = {}

    for service_name in services_config.keys():
        try:
            tools = await mcp_manager.list_tools(service_name)
            all_tools[service_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                }
                for tool in tools
            ]
        except Exception as e:
            print(f"Warning: Failed to list tools from {service_name}: {e}")
            all_tools[service_name] = []

    return {
        "success": True,
        "tools": all_tools
    }


@app.post("/services/{service_name}/call")
async def call_tool(service_name: str, req: ToolCallReq):
    """调用指定服务的工具"""
    if service_name not in services_config:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")

    if not mcp_manager:
        raise HTTPException(status_code=500, detail="MCP Manager not initialized")

    try:
        # 调用工具
        result = await mcp_manager.call_tool(service_name, req.tool_name, req.arguments)

        return {
            "success": True,
            "service": service_name,
            "tool": req.tool_name,
            "result": result.content
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
async def run(req: RunReq):
    """
    运行查询 - 智能路由到合适的服务并执行

    这个端点可以：
    1. 如果指定了 service，直接使用该服务
    2. 如果没指定，根据查询内容智能选择服务并尝试执行
    """
    if not mcp_manager:
        return {"success": False, "error": "MCP Manager not initialized"}

    query = (req.query or "").strip()
    if not query:
        return {"success": False, "error": "Empty query"}

    # 确定要使用的服务
    if req.service:
        if req.service not in services_config:
            return {"success": False, "error": f"Unknown service: {req.service}"}
        services_to_try = [req.service]
    else:
        # 根据查询推断服务
        services_to_try = infer_services_from_query(query)

    # 尝试在每个推荐的服务中找到合适的工具
    results = []
    errors = []

    for service_name in services_to_try:
        try:
            # 列出服务的所有工具
            tools = await mcp_manager.list_tools(service_name)
            if not tools:
                errors.append(f"{service_name}: No tools available")
                continue

            # 对于简单的查询，尝试使用第一个工具（这里可以改进为更智能的选择）
            tool = tools[0]
            print(f"[{service_name}] Calling tool: {tool.name}")

            # 准备参数 - 简化版本，将整个查询作为第一个参数
            arguments = {"text": query} if query else {}

            try:
                result = await mcp_manager.call_tool(service_name, tool.name, arguments)

                results.append({
                    "service": service_name,
                    "tool": tool.name,
                    "result": result.content
                })
                # 返回第一个成功的结果
                return {
                    "success": True,
                    **results[0]
                }
            except Exception as tool_error:
                errors.append(f"{service_name}/{tool.name}: {str(tool_error)}")

        except Exception as e:
            errors.append(f"{service_name}: {str(e)}")
            continue

    # 如果有成功的结果就返回
    if results:
        return {
            "success": True,
            **results[0]
        }

    # 如果没有成功的结果
    return {
        "success": False,
        "error": f"Failed to execute query: {query}",
        "tried_services": services_to_try,
        "errors": errors
    }


# ============================================================================
# 辅助函数
# ============================================================================

def infer_services_from_query(query: str) -> List[str]:
    """根据查询推断合适的服务"""
    query_lower = query.lower()

    # 简单的关键词匹配
    recommendations = []

    if any(word in query_lower for word in ["equation", "solve", "math", "sympy", "symbolic"]):
        recommendations.append("sympy")

    if any(word in query_lower for word in ["sentiment", "emotion", "feeling", "opinion", "vader"]):
        recommendations.append("vaderSentiment")

    if any(word in query_lower for word in ["physics", "quantum", "particle", "energy", "nemo"]):
        recommendations.append("physicsnemo")

    if any(word in query_lower for word in ["earthquake", "seismic", "wave", "obspy", "geology"]):
        recommendations.append("obspy")

    # 如果没有匹配到，返回所有服务
    if not recommendations:
        recommendations = list(services_config.keys())

    return recommendations


# ============================================================================
# 开发服务器运行
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
