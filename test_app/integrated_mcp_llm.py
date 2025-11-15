#!/usr/bin/env python3
"""
完整的端到端 LLM + 远程 MCP 工具系统
支持 HuggingFace Space 部署的远程 MCP 服务（通过官方 MCP SSE 客户端）

1. 从 URL 配置加载远程 MCP 服务
2. 通过 MCP SSE 协议与远程 MCP 服务通信
3. LLM 自动选择合适的工具
4. 调用远程工具并获取结果
5. LLM 生成最终答案

使用方式：
只需配置 URL，例如：
{
    "sympy": {"url": "https://kabuda777-Code2MCP-sympy.hf.space"},
    "obspy": {"url": "https://ArthurY-xujie-mcp.hf.space"},
    "vaderSentiment": {"url": "https://ArthurY-vaderSentiment.hf.space"}
}

安装依赖：
pip install mcp httpx openai python-dotenv
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from dotenv import load_dotenv

# 导入 MCP 官方库
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError:
    print("Error: mcp library not found.")
    print("Install with: pip install mcp")
    sys.exit(1)


# ============================================================================
# MCP 服务配置和管理
# ============================================================================

@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str          # 服务名，如 "sympy", "obspy"
    url: str          # 服务 URL，如 "https://xxx.hf.space"


class MCPClientManager:
    """
    MCP 官方客户端管理器

    使用 mcp 库的 sse_client 连接到远程 MCP 服务
    支持多个并发连接（延迟连接模式）
    """

    def __init__(self):
        self.configs: Dict[str, MCPServerConfig] = {}
        self.tool_to_service: Dict[str, str] = {}  # 工具名 -> 服务名
        self.service_tools: Dict[str, List[Any]] = {}  # 缓存每个服务的工具列表

    async def discover_tools(self, config: MCPServerConfig) -> bool:
        """
        发现一个 MCP 服务提供的工具（不保持持久连接）

        Args:
            config: MCP 服务配置

        Returns:
            是否成功发现工具
        """
        try:
            sse_url = config.url.rstrip("/")

            # 临时连接以获取工具列表
            async with sse_client(sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()

                    if not tools.tools:
                        print(f"✗ No tools found in '{config.name}'")
                        return False

                    # 保存配置和工具列表
                    self.configs[config.name] = config
                    self.service_tools[config.name] = tools.tools

                    # 建立工具 -> 服务映射
                    for tool in tools.tools:
                        self.tool_to_service[tool.name] = config.name

                    print(f"✓ Discovered '{config.name}' with {len(tools.tools)} tools")
                    return True

        except Exception as e:
            print(f"✗ Error discovering tools from '{config.name}' at {config.url}: {e}")
            return False

    async def load_from_config_async(self, config_dict: Dict[str, Dict[str, str]]) -> int:
        """
        从配置字典加载多个服务并发现工具（异步版本）

        Args:
            config_dict: 配置字典，格式如:
                {
                    "sympy": {"url": "https://xxx.hf.space"},
                    "obspy": {"url": "https://yyy.hf.space"}
                }

        Returns:
            成功加载的服务数量
        """
        configs = []
        for name, settings in config_dict.items():
            if "url" in settings:
                config = MCPServerConfig(
                    name=name,
                    url=settings["url"]
                )
                configs.append(config)

        # 异步并发加载所有服务
        results = await asyncio.gather(*[self.discover_tools(cfg) for cfg in configs])

        return sum(results)

    def load_from_config(self, config_dict: Dict[str, Dict[str, str]]) -> int:
        """
        从配置字典加载多个服务并发现工具（同步包装器）

        Args:
            config_dict: 配置字典，格式如:
                {
                    "sympy": {"url": "https://xxx.hf.space"},
                    "obspy": {"url": "https://yyy.hf.space"}
                }

        Returns:
            成功加载的服务数量
        """
        # 如果已经有运行的事件循环，直接调用异步版本
        try:
            loop = asyncio.get_running_loop()
            # 已经在事件循环中，返回 0 并提示需要使用异步版本
            print("⚠️  Error: Cannot use load_from_config() inside an async function.")
            print("   Please use 'await manager.load_from_config_async()' instead.")
            return 0
        except RuntimeError:
            # 没有运行的事件循环，创建新的
            return asyncio.run(self.load_from_config_async(config_dict))

    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有服务的工具列表（聚合，转换为 OpenAI function calling 格式）

        Returns:
            所有可用工具（OpenAI function calling 格式）
        """
        all_tools = []

        for service_name, tools in self.service_tools.items():
            for tool in tools:
                # 转换为 OpenAI function calling 格式
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": f"[{service_name}] {tool.description}",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
                all_tools.append(openai_tool)

        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        调用指定的工具（建立临时连接）

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果（JSON 字符串）
        """
        if tool_name not in self.tool_to_service:
            return json.dumps({
                "status": "error",
                "error": f"Tool '{tool_name}' not found"
            }, ensure_ascii=False)

        service_name = self.tool_to_service[tool_name]
        config = self.configs[service_name]
        sse_url = config.url.rstrip("/")

        try:
            # 建立临时连接调用工具
            async with sse_client(sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # 调用远程工具
                    result = await session.call_tool(tool_name, arguments)

                    # 处理结果
                    if result.content:
                        # 获取第一个内容块
                        content = result.content[0] if result.content else {}
                        return json.dumps({
                            "status": "success",
                            "result": content.text if hasattr(content, 'text') else str(content)
                        }, ensure_ascii=False)
                    else:
                        return json.dumps({
                            "status": "error",
                            "error": "Tool returned empty result"
                        }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            }, ensure_ascii=False)


# ============================================================================
# LLM with Remote MCP Tools
# ============================================================================

class LLMWithRemoteTools:
    """
    支持远程 MCP 工具的 LLM

    工作流：
    1. 从多个远程 MCP 服务获取工具列表
    2. LLM 分析用户问题并选择合适的工具
    3. 调用远程工具获取结果
    4. LLM 根据结果生成最终答案
    """

    def __init__(self, client_manager: MCPClientManager, model: str = "gpt-4"):
        self.client = AsyncOpenAI()
        self.model = model
        self.client_manager = client_manager
        self.max_iterations = 5

    async def chat_with_tools(self, user_message: str) -> str:
        """
        与远程工具的对话

        Args:
            user_message: 用户消息

        Returns:
            LLM 的最终答案
        """
        # 获取所有可用的工具
        tools = await self.client_manager.get_all_tools()

        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        print(f"\n{'='*70}")
        print(f"User Query: {user_message}")
        print(f"Available Tools: {len(tools)} from {len(self.client_manager.configs)} services")
        print(f"{'='*70}\n")

        for iteration in range(self.max_iterations):
            print(f"[Iteration {iteration + 1}] Calling LLM...")

            # 调用 LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.7
            )

            assistant_message = response.choices[0].message

            # 判断 LLM 是否决定调用工具
            if assistant_message.tool_calls:
                print(f"LLM decided to use {len(assistant_message.tool_calls)} tool(s):")

                # 添加 LLM 的响应到消息历史
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        }
                        for call in assistant_message.tool_calls
                    ]
                })

                # 执行工具调用
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_params = json.loads(tool_call.function.arguments)

                    print(f"  → Calling tool: {tool_name}")
                    print(f"    Parameters: {json.dumps(tool_params, ensure_ascii=False)[:100]}...")

                    # 调用远程工具
                    result = await self.client_manager.call_tool(tool_name, tool_params)

                    print(f"    Result: {result[:200]}..." if len(result) > 200 else f"    Result: {result}")

                    tool_results.append({
                        "type": "tool",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })

                # 将工具结果添加到消息历史
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # LLM 没有调用工具，返回最终答案
                final_answer = assistant_message.content
                print(f"\n[Final Answer]\n{final_answer}")
                return final_answer

        return "Max iterations reached without final answer"


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """端到端示例：多个远程 MCP 服务 + LLM 工具调用"""

    # 加载环境变量
    load_dotenv()

    print("="*70)
    print("Integrated LLM + Remote MCP Tools (HuggingFace Spaces)")
    print("="*70)

    # 1. 创建客户端管理器
    manager = MCPClientManager()

    # 2. 加载远程 MCP 服务配置（类似 Cursor 的配置）
    mcp_servers_config = {
        "sympy": {
            "url": "https://kabuda777-Code2MCP-sympy.hf.space"
        },
        "vaderSentiment": {
            "url": "https://ArthurY-vaderSentiment.hf.space"
        },
        "physicsnemo": {
            "url": "https://ArthurY-physicsnemo.hf.space"
        },
        # 你可以继续添加更多服务
        # "obspy": {
        #     "url": "https://ArthurY-xujie-mcp.hf.space"
        # },
    }

    print("\nDiscovering MCP services...")
    loaded_count = await manager.load_from_config_async(mcp_servers_config)
    print(f"\nSuccessfully discovered {loaded_count}/{len(mcp_servers_config)} services\n")

    if loaded_count == 0:
        print("No services discovered. Please check your configuration and URLs.")
        return

    # 3. 创建支持工具调用的 LLM
    llm = LLMWithRemoteTools(manager, model="gpt-4")

    # 4. 示例查询
    queries = [
        "Use sympy to solve the equation: x^2 - 5*x + 6 = 0",
        "Analyze the sentiment of this text: 'I absolutely love this product! It's amazing!'",
    ]

    for query in queries:
        try:
            answer = await llm.chat_with_tools(query)
            print(f"\n{'='*70}\n")
        except Exception as e:
            print(f"Error processing query: {e}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
