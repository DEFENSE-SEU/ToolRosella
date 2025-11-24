"""
MCP 握手和工具列表测试脚本

测试与远程 MCP 服务的基本连接能力，排查 HuggingFace 400 错误的具体原因

- 完全独立于 FastAPI，最小化包装
- 详细的日志和错误定位
- 包含简单的重试逻辑
"""

import asyncio
import json
import logging
import sys
import httpx
from typing import List, Tuple, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client

# Python 3.11+ 兼容性处理
try:
    from asyncio import timeout as async_timeout
except ImportError:
    # Python 3.10 及以下使用 asyncio.wait_for
    @asynccontextmanager
    async def async_timeout(seconds):
        """Timeout context manager for Python < 3.11"""
        task = asyncio.current_task()
        handle = asyncio.get_event_loop().call_later(
            seconds, task.cancel
        ) if task else None
        try:
            yield
        finally:
            if handle:
                handle.cancel()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP 服务配置 - 本地 MCP 服务
# 默认指向极简本地示例服务（local_mcp_server_example.py）
SERVICES = {"local-test": "http://127.0.0.1:8001/mcp"}



class TestResult:
    """测试结果"""
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.connection_ok = False
        self.initialization_ok = False
        self.list_tools_ok = False
        self.tools_count = 0
        self.tools: List[dict] = []
        self.error: Optional[str] = None
        self.error_stage = None  # 错误发生在哪一步

    def __str__(self):
        status = "✓" if (self.connection_ok and self.initialization_ok and self.list_tools_ok) else "✗"
        return (
            f"{status} {self.service_name:20} | "
            f"Connection: {'✓' if self.connection_ok else '✗'} | "
            f"Init: {'✓' if self.initialization_ok else '✗'} | "
            f"Tools: {'✓' if self.list_tools_ok else '✗'} ({self.tools_count})"
        )


async def test_service_handshake(
    service_name: str,
    url: str,
    timeout: int = 30,
    retries: int = 1
) -> TestResult:
    """
    测试单个服务的握手和工具列表

    Args:
        service_name: 服务名称
        url: 服务 URL
        timeout: 超时时间（秒）
        retries: 失败重试次数

    Returns:
        TestResult 对象
    """
    result = TestResult(service_name)

    for attempt in range(1, retries + 1):
        if attempt > 1:
            logger.info(f"[{service_name}] 重试 {attempt}/{retries}...")
            await asyncio.sleep(2 ** (attempt - 1))  # 指数退避

        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"[{service_name}] 开始测试")
            logger.info(f"URL: {url}")
            logger.info(f"Attempt: {attempt}/{retries}")
            logger.info(f"{'='*70}")

            # 第一步：建立 SSE 连接（禁用系统代理，避免本地/内网被错误代理）
            logger.info(f"[{service_name}] 1️⃣  建立 SSE 连接...")
            try:
                async with async_timeout(timeout):
                    transport = sse_client(
                        url,
                        httpx_client_factory=lambda headers=None, auth=None, timeout=None: httpx.AsyncClient(  # type: ignore
                            headers=headers,
                            auth=auth,
                            timeout=timeout or httpx.Timeout(30.0, read=300.0),
                            follow_redirects=True,
                            trust_env=False,
                        ),
                    )
                    read_stream, write_stream = await transport.__aenter__()
                    logger.info(f"[{service_name}] ✓ SSE 连接成功")
                    result.connection_ok = True
            except asyncio.TimeoutError:
                logger.error(f"[{service_name}] ✗ SSE 连接超时 ({timeout}s)")
                result.error = f"Connection timeout ({timeout}s)"
                result.error_stage = "SSE connection"
                continue
            except Exception as e:
                logger.error(f"[{service_name}] ✗ SSE 连接失败: {type(e).__name__}: {str(e)[:200]}")
                result.error = f"Connection failed: {str(e)[:200]}"
                result.error_stage = "SSE connection"
                continue

            # 第二步：创建会话并初始化
            logger.info(f"[{service_name}] 2️⃣  创建 MCP 会话并初始化...")
            try:
                async with async_timeout(timeout):
                    session = ClientSession(read_stream, write_stream)
                    await session.initialize()
                    logger.info(f"[{service_name}] ✓ 会话初始化成功")
                    result.initialization_ok = True
            except asyncio.TimeoutError:
                logger.error(f"[{service_name}] ✗ 会话初始化超时 ({timeout}s)")
                result.error = f"Initialization timeout ({timeout}s)"
                result.error_stage = "Session initialization"
                continue
            except Exception as e:
                logger.error(f"[{service_name}] ✗ 会话初始化失败: {type(e).__name__}: {str(e)[:100]}")
                result.error = f"Initialization failed: {str(e)[:100]}"
                result.error_stage = "Session initialization"
                continue

            # 第三步：列举工具
            logger.info(f"[{service_name}] 3️⃣  列举工具...")
            try:
                async with async_timeout(timeout):
                    tools_response = await session.list_tools()
                    logger.info(f"[{service_name}] ✓ 工具列表获取成功")
                    result.list_tools_ok = True
                    result.tools_count = len(tools_response.tools)

                    # 解析工具信息
                    for tool in tools_response.tools:
                        tool_info = {
                            "name": tool.name,
                            "description": tool.description or "(无描述)",
                            "has_input_schema": hasattr(tool, 'inputSchema') and tool.inputSchema is not None,
                        }
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            tool_info["input_schema_keys"] = list(tool.inputSchema.get("properties", {}).keys())
                        result.tools.append(tool_info)

                    logger.info(f"[{service_name}] 📋 工具详情:")
                    for i, tool_info in enumerate(result.tools, 1):
                        logger.info(f"  {i}. {tool_info['name']}")
                        logger.info(f"     描述: {tool_info['description']}")
                        if tool_info['has_input_schema']:
                            logger.info(f"     参数: {tool_info['input_schema_keys']}")

                    # 成功！
                    await session.close()
                    await transport.__aexit__(None, None, None)
                    return result

            except asyncio.TimeoutError:
                logger.error(f"[{service_name}] ✗ 列举工具超时 ({timeout}s)")
                result.error = f"List tools timeout ({timeout}s)"
                result.error_stage = "List tools"
                try:
                    await session.close()
                    await transport.__aexit__(None, None, None)
                except:
                    pass
                continue
            except Exception as e:
                logger.error(f"[{service_name}] ✗ 列举工具失败: {type(e).__name__}: {str(e)[:100]}")
                result.error = f"List tools failed: {str(e)[:100]}"
                result.error_stage = "List tools"
                try:
                    await session.close()
                    await transport.__aexit__(None, None, None)
                except:
                    pass
                continue

        except Exception as e:
            logger.error(f"[{service_name}] ✗ 未预期的错误: {type(e).__name__}: {str(e)}")
            result.error = f"Unexpected error: {str(e)}"

    return result


async def main():
    """主测试函数"""
    logger.info("\n" + "="*70)
    logger.info("MCP 握手和工具列表测试")
    logger.info("="*70)
    logger.info(f"将测试 {len(SERVICES)} 个服务\n")

    # 并发测试所有服务
    tasks = [
        test_service_handshake(service_name, url, timeout=120, retries=1)
        for service_name, url in SERVICES.items()
    ]
    results = await asyncio.gather(*tasks)

    # 汇总结果
    logger.info("\n" + "="*70)
    logger.info("测试结果汇总")
    logger.info("="*70)
    logger.info(f"{'Service':<20} | {'Connection':<12} | {'Init':<12} | {'Tools':<15}")
    logger.info("-"*70)

    successful = 0
    failed = 0

    for result in sorted(results, key=lambda r: r.service_name):
        logger.info(str(result))
        if result.list_tools_ok:
            successful += 1
        else:
            failed += 1
            logger.warning(f"  ⚠️  失败原因: {result.error_stage} - {result.error}")

    logger.info("-"*70)
    logger.info(f"成功: {successful}/{len(SERVICES)}, 失败: {failed}/{len(SERVICES)}\n")

    # 如果有失败，打印诊断信息
    if failed > 0:
        logger.warning("\n" + "="*70)
        logger.warning("诊断信息")
        logger.warning("="*70)

        for result in sorted(results, key=lambda r: not r.list_tools_ok):  # 失败的优先显示
            if not result.list_tools_ok:
                logger.warning(f"\n[{result.service_name}]")
                logger.warning(f"  错误阶段: {result.error_stage}")
                logger.warning(f"  错误信息: {result.error}")
                logger.warning(f"  连接: {'✓' if result.connection_ok else '✗'}")
                logger.warning(f"  初始化: {'✓' if result.initialization_ok else '✗'}")

        logger.warning("\n排查建议:")
        logger.warning("  1. 检查网络连接是否正常")
        logger.warning("  2. 检查 URL 是否正确（应以 /mcp 结尾）")
        logger.warning("  3. 检查远程服务是否在线")
        logger.warning("  4. 增加超时时间（网络慢时）")
        logger.warning("  5. 考虑使用本地 MCP 服务进行测试")

    # 返回退出码
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n测试被中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n致命错误: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
