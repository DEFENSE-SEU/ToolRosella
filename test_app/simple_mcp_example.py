#!/usr/bin/env python3
"""
简化版本：快速测试 MCP 工具调用

无需 LLM，直接测试工具通信。
"""

import asyncio
import json
import os
from dotenv import load_dotenv

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
except ImportError:
    print("Error: mcp library not found.")
    print("Install with: pip install mcp")
    exit(1)


async def test_single_service(service_name: str, service_url: str):
    """测试连接到单个 MCP 服务"""

    print(f"\n{'='*70}")
    print(f"Testing Service: {service_name}")
    print(f"URL: {service_url}")
    print(f"{'='*70}\n")

    try:
        # 创建 SSE 传输（需要在 async with 中使用）
        print(f"[1/4] Creating SSE transport...")
        async with sse_client(service_url) as (read_stream, write_stream):
            # 创建会话
            print(f"[2/4] Creating client session...")
            async with ClientSession(read_stream, write_stream) as session:

                # 初始化
                print(f"[3/4] Initializing session...")
                await session.initialize()
                print(f"      ✓ Session initialized")

                # 获取工具列表
                print(f"[4/4] Fetching tools...")
                tools = await session.list_tools()
                print(f"      ✓ Found {len(tools.tools)} tools\n")

                # 显示工具
                if tools.tools:
                    print("Available Tools:")
                    for i, tool in enumerate(tools.tools, 1):
                        print(f"  {i}. {tool.name}")
                        print(f"     Description: {tool.description}")
                        if hasattr(tool, 'inputSchema'):
                            print(f"     Input Schema: {json.dumps(tool.inputSchema, indent=2)[:200]}...")
                        print()

                    # 示例：调用第一个工具
                    if tools.tools:
                        first_tool = tools.tools[0]
                        print(f"Attempting to call first tool: {first_tool.name}")
                        print(f"(This is just a test - may fail if tool has required parameters)\n")

                        try:
                            result = await session.call_tool(first_tool.name, {})
                            print(f"Tool Result:")
                            print(f"  {result}")
                        except Exception as e:
                            print(f"Tool call failed (expected if tool requires parameters): {e}")

        print(f"\n✓ Session closed successfully")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_multiple_services():
    """测试连接到多个 MCP 服务"""

    load_dotenv()

    # 你的 MCP 服务列表
    services = {
        "sympy": "https://kabuda777-Code2MCP-sympy.hf.space",
        "vaderSentiment": "https://ArthurY-vaderSentiment.hf.space",
        # "obspy": "https://ArthurY-xujie-mcp.hf.space",
        # "physicsnemo": "https://ArthurY-physicsnemo.hf.space",
    }

    print("="*70)
    print("MCP Service Connection Test")
    print("="*70)
    print(f"\nTesting {len(services)} services...\n")

    results = []
    for service_name, service_url in services.items():
        try:
            await test_single_service(service_name, service_url)
            results.append((service_name, True, None))
        except Exception as e:
            results.append((service_name, False, str(e)))

    # 总结
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    for service_name, success, error in results:
        status = "✓ Success" if success else f"✗ Failed"
        print(f"{status}: {service_name}")
        if error:
            print(f"        {error}")

    passed = sum(1 for _, success, _ in results if success)
    print(f"\nResult: {passed}/{len(services)} services connected successfully")


async def example_tool_call():
    """
    示例：调用具体的工具

    这个例子展示如何调用 sympy 的求解方程工具
    """

    print("\n" + "="*70)
    print("Example: Call Sympy Tool")
    print("="*70 + "\n")

    try:
        # 连接到 sympy 服务
        async with sse_client("https://kabuda777-Code2MCP-sympy.hf.space") as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # 获取工具列表
                tools = await session.list_tools()

                # 查找求解方程的工具
                solve_tool = None
                for tool in tools.tools:
                    if "solve" in tool.name.lower():
                        solve_tool = tool
                        break

                if solve_tool:
                    print(f"Found tool: {solve_tool.name}")
                    print(f"Description: {solve_tool.description}\n")

                    # 调用工具
                    print("Calling tool with parameters:")
                    params = {"equation": "x**2 - 5*x + 6"}
                    print(f"  equation: {params['equation']}\n")

                    result = await session.call_tool(solve_tool.name, params)
                    print(f"Result:")
                    print(json.dumps(result.content[0] if result.content else {}, indent=2))
                else:
                    print("No solve tool found in sympy")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           MCP Service Testing and Tool Calling Examples              ║
║                                                                      ║
║ This script demonstrates:                                            ║
║ 1. Connecting to remote MCP services (like HuggingFace Spaces)      ║
║ 2. Listing available tools                                           ║
║ 3. Calling tools with parameters                                     ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Test 1: 测试多个服务的连接
    await test_multiple_services()

    # Test 2: 具体的工具调用示例（可选，取消注释来运行）
    # await example_tool_call()

    print("\n" + "="*70)
    print("Test completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
