"""
MCPConnectionManager - MCP 会话管理层

职责：
- 按服务维护持久 MCP 会话（SSE 连接）
- 提供统一的工具调用接口
- 处理连接生命周期和错误恢复
- 完全独立于 FastAPI，可单独使用

设计原则：
- 会话复用：同一服务的连接在内存中持久保存
- 清晰的职责：只负责"连接管理"和"工具调用"，不涉及业务逻辑
- 错误隔离：错误时返回有意义的异常，便于上层处理
"""

import asyncio
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from mcp import ClientSession
from mcp.client.sse import sse_client
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    description: str
    input_schema: dict


@dataclass
class ToolResult:
    """工具调用结果"""
    content: str
    raw_content: Optional[str] = None


class MCPConnectionManager:
    """
    MCP 连接管理器

    按服务维护持久 SSE 连接和 ClientSession，
    避免每次请求都重新建立连接。
    """

    def __init__(self, services_config: Dict[str, dict]):
        """
        初始化连接管理器

        Args:
            services_config: 服务配置字典
                {
                    "service_name": {
                        "url": "https://...",
                        "description": "...",
                        ...
                    },
                    ...
                }
        """
        self.services_config = services_config
        self.sessions: Dict[str, ClientSession] = {}  # 持久会话存储
        self.transports: Dict[str, Tuple] = {}  # 存储 (read_stream, write_stream)
        self.lock = asyncio.Lock()
        self.initialized = False

    async def initialize(self) -> None:
        """初始化管理器（暂时不做自动连接，延迟连接到首次使用）"""
        self.initialized = True
        logger.info(f"MCPConnectionManager 初始化完成，管理 {len(self.services_config)} 个服务")

    async def get_session(self, service_name: str) -> ClientSession:
        """
        获取或创建 MCP 会话

        首次调用时建立连接，之后复用已有连接。

        Args:
            service_name: 服务名称

        Returns:
            ClientSession 对象

        Raises:
            ValueError: 服务不存在
            ConnectionError: 连接失败
        """
        if service_name not in self.services_config:
            raise ValueError(f"未知服务: {service_name}")

        # 如果已有会话，直接返回
        if service_name in self.sessions:
            logger.debug(f"[{service_name}] 复用已有会话")
            return self.sessions[service_name]

        # 需要建立新连接
        async with self.lock:
            # 双检查（防止并发建立多个连接）
            if service_name in self.sessions:
                return self.sessions[service_name]

            logger.info(f"[{service_name}] 建立新的 MCP 会话")
            return await self._create_session(service_name)

    async def _create_session(self, service_name: str) -> ClientSession:
        """
        建立新的 MCP 会话（内部方法，已加锁）

        Args:
            service_name: 服务名称

        Returns:
            ClientSession 对象

        Raises:
            ConnectionError: 握手失败
        """
        config = self.services_config[service_name]
        url = config["url"]

        try:
            logger.debug(f"[{service_name}] 连接到 {url}")

            # 构造握手头；支持可选的 Bearer Token（HuggingFace 私有空间/鉴权）
            auth_token = os.environ.get("MCP_AUTH_TOKEN")
            headers = {
                "Accept": "text/event-stream",  # 纯 SSE，避免触发 JSON-RPC 路由
                "Cache-Control": "no-cache",
                "User-Agent": "easytool-mcp-client/1.0",
                "Accept-Encoding": "identity",  # 避免压缩干扰 SSE
            }
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                logger.debug(f"[{service_name}] 使用 Bearer Token 认证")

            # 建立 SSE 连接；禁用环境代理（trust_env=False）防止本地/内网被错误代理
            transport = sse_client(
                url,
                headers=headers,
                timeout=30,           # HTTP 握手超时
                sse_read_timeout=300, # SSE 读超时
                httpx_client_factory=lambda headers=None, auth=None, timeout=None: httpx.AsyncClient(  # type: ignore
                    headers=headers,
                    auth=auth,
                    timeout=timeout or httpx.Timeout(30.0, read=300.0),
                    follow_redirects=True,
                    trust_env=False,
                ),
            )
            read_stream, write_stream = await transport.__aenter__()

            # 创建 MCP 会话
            session = ClientSession(read_stream, write_stream)
            logger.debug(f"[{service_name}] 会话对象创建完成，进行握手...")

            # 初始化会话（握手）
            await session.initialize()
            logger.info(f"[{service_name}] ✓ 会话初始化成功")

            # 保存会话和传输对象
            self.sessions[service_name] = session
            self.transports[service_name] = (transport, read_stream, write_stream)

            return session

        except Exception as e:
            logger.error(f"[{service_name}] ✗ 会话建立失败: {type(e).__name__}: {str(e)}")
            raise ConnectionError(f"无法连接到 {service_name}: {str(e)}") from e

    async def list_tools(self, service_name: str) -> List[ToolInfo]:
        """
        列举服务的所有工具

        Args:
            service_name: 服务名称

        Returns:
            工具列表

        Raises:
            ValueError: 服务不存在
            ConnectionError: 连接失败
        """
        session = await self.get_session(service_name)

        try:
            logger.debug(f"[{service_name}] 列举工具...")
            tools_response = await session.list_tools()

            tools = [
                ToolInfo(
                    name=tool.name,
                    description=tool.description or "（无描述）",
                    input_schema=tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                )
                for tool in tools_response.tools
            ]

            logger.info(f"[{service_name}] ✓ 获得 {len(tools)} 个工具")
            return tools

        except Exception as e:
            logger.error(f"[{service_name}] ✗ 列举工具失败: {str(e)}")
            raise

    async def call_tool(
        self,
        service_name: str,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """
        调用服务的指定工具

        Args:
            service_name: 服务名称
            tool_name: 工具名称
            arguments: 工具参数字典

        Returns:
            ToolResult 对象

        Raises:
            ValueError: 服务或工具不存在
            ConnectionError: 连接失败
            RuntimeError: 工具执行失败
        """
        session = await self.get_session(service_name)

        try:
            logger.info(f"[{service_name}] 调用工具: {tool_name}")
            logger.debug(f"  参数: {arguments}")

            result = await session.call_tool(tool_name, arguments)

            # 提取结果内容
            if result.content and len(result.content) > 0:
                content = result.content[0]
                result_text = content.text if hasattr(content, 'text') else str(content)
                logger.info(f"[{service_name}] ✓ 工具调用成功")
                return ToolResult(content=result_text, raw_content=str(result))
            else:
                error_msg = "工具返回空结果"
                logger.warning(f"[{service_name}] ⚠️  {error_msg}")
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"[{service_name}] ✗ 工具调用失败: {str(e)}")
            raise

    async def health_check(self, service_name: str) -> bool:
        """
        检查服务连接状态

        Args:
            service_name: 服务名称

        Returns:
            True 如果连接正常，否则 False
        """
        try:
            session = await self.get_session(service_name)
            # 尝试列举工具作为健康检查
            await session.list_tools()
            return True
        except Exception as e:
            logger.warning(f"[{service_name}] 健康检查失败: {str(e)}")
            return False

    async def shutdown(self) -> None:
        """
        关闭所有连接

        通常在应用关闭时调用
        """
        logger.info("关闭所有 MCP 连接...")

        for service_name in list(self.sessions.keys()):
            try:
                session = self.sessions[service_name]
                logger.debug(f"[{service_name}] 关闭会话...")

                # 关闭会话
                await session.close()

                # 关闭传输
                if service_name in self.transports:
                    transport, read_stream, write_stream = self.transports[service_name]
                    try:
                        await transport.__aexit__(None, None, None)
                    except Exception as e:
                        logger.warning(f"[{service_name}] 关闭传输时出错: {str(e)}")

                del self.sessions[service_name]
                del self.transports[service_name]
                logger.debug(f"[{service_name}] ✓ 会话已关闭")

            except Exception as e:
                logger.error(f"[{service_name}] ✗ 关闭时出错: {str(e)}")

        self.initialized = False
        logger.info("所有 MCP 连接已关闭")

    def __repr__(self) -> str:
        active_services = list(self.sessions.keys())
        return (
            f"<MCPConnectionManager "
            f"services={len(self.services_config)}, "
            f"active_connections={len(active_services)}, "
            f"active={active_services}>"
        )
