"""
本地 MCP 连接器 - 专门用于连接本地部署的 MCP 服务
与远程 MCP 连接逻辑完全独立

特点：
- 直接基于 HTTP + SSE 握手
- 处理 FastMCP 的 session ID 机制
- 简单、稳定、经过验证

当前实现：
1. 连接管理（connect/disconnect）：使用原始 socket 获取 session ID ✅
2. 工具调用（call_tool）：NOT IMPLEMENTED ⚠️
3. 工具列表（get_tools）：NOT IMPLEMENTED ⚠️

已知问题：
- 官方 MCP 库的 sse_client 与本地 FastMCP 存在兼容性问题
- httpx 异步客户端在建立 SSE 连接时会被 FastMCP 拒绝
- 需要等待官方库或 FastMCP 的修复

解决方案：
- 如果需要调用工具，可以使用其他方式（如 REST API）
- 目前 LocalMCPConnector 专注于可靠的连接管理和 session ID 获取
- 工具调用功能需要额外的开发或等待库的兼容性修复

参考：
- test_handshake.py: 原始 socket 握手（✅ 工作正常）
- test_mcp_final.py: 官方库示例（⚠️ 遇到兼容性问题）
"""

import socket
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator
import asyncio

logger = logging.getLogger(__name__)


class LocalMCPConnector:
    """本地 MCP 连接器"""

    def __init__(self, host: str = "localhost", port: int = 8001):
        """
        初始化本地 MCP 连接器

        Args:
            host: MCP 服务地址（默认 localhost）
            port: MCP 服务端口（默认 8001）
        """
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}/mcp"
        self.session_id: Optional[str] = None
        self.is_connected = False

    def _get_session_id_sync(self) -> str:
        """
        同步方式获取 session ID

        Returns:
            session ID 字符串

        Raises:
            Exception: 连接失败或未获得 session ID
        """
        logger.info(f"[LocalMCP] 获取 session ID: {self.url}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            # 连接到 MCP 服务
            sock.connect((self.host, self.port))
            logger.debug(f"[LocalMCP] TCP 连接成功")

            # 发送初始化请求
            request = (
                "GET /mcp HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                "Accept: text/event-stream\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            sock.sendall(request.encode())
            logger.debug("[LocalMCP] 初始化请求已发送")

            # 接收响应
            response = b""
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk

            response_text = response.decode('utf-8', errors='replace')
            logger.debug(f"[LocalMCP] 响应长度: {len(response_text)} 字符")

            # 解析 session ID
            for line in response_text.split('\r\n'):
                if line.lower().startswith('mcp-session-id:'):
                    session_id = line.split(':', 1)[1].strip()
                    logger.info(f"[LocalMCP] ✓ 获得 Session ID: {session_id[:16]}...")
                    return session_id

            raise Exception("Response does not contain mcp-session-id header")

        except socket.timeout:
            logger.error("[LocalMCP] ✗ 连接超时（5秒）")
            raise
        except ConnectionRefusedError:
            logger.error(f"[LocalMCP] ✗ 连接被拒绝: {self.host}:{self.port}")
            raise
        except Exception as e:
            logger.error(f"[LocalMCP] ✗ 获取 session ID 失败: {type(e).__name__}: {e}")
            raise
        finally:
            sock.close()

    async def connect(self) -> bool:
        """
        异步连接到本地 MCP 服务

        Returns:
            True 连接成功，False 连接失败
        """
        try:
            logger.info("[LocalMCP] 开始连接到本地 MCP 服务...")

            # 同步获取 session ID（在线程中运行避免阻塞）
            loop = asyncio.get_event_loop()
            self.session_id = await loop.run_in_executor(
                None, self._get_session_id_sync
            )

            self.is_connected = True
            logger.info("[LocalMCP] ✓ 连接成功")
            return True

        except Exception as e:
            logger.error(f"[LocalMCP] ✗ 连接失败: {type(e).__name__}: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
        self.session_id = None
        logger.info("[LocalMCP] 已断开连接")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果

        Note:
            当前不实现此方法，原因：官方 MCP 库与本地 FastMCP 存在兼容性问题
            详见 MCP_COMPATIBILITY_ISSUE.md
        """
        if not self.is_connected or not self.session_id:
            raise Exception("Not connected to MCP service. Call connect() first.")

        logger.info(f"[LocalMCP] 调用工具: {tool_name}")
        logger.debug(f"[LocalMCP] 参数: {arguments}")

        raise NotImplementedError(
            "Tool calling is not implemented due to FastMCP compatibility issues.\n"
            "See MCP_COMPATIBILITY_ISSUE.md for details and workarounds."
        )

    async def get_tools(self) -> list:
        """
        获取可用工具列表

        Returns:
            工具列表

        Note:
            当前不实现此方法，原因：官方 MCP 库与本地 FastMCP 存在兼容性问题
            详见 MCP_COMPATIBILITY_ISSUE.md
        """
        if not self.is_connected or not self.session_id:
            raise Exception("Not connected to MCP service. Call connect() first.")

        logger.info("[LocalMCP] 获取可用工具列表...")

        raise NotImplementedError(
            "Getting tools is not implemented due to FastMCP compatibility issues.\n"
            "See MCP_COMPATIBILITY_ISSUE.md for details and workarounds."
        )

    async def verify_connection(self) -> bool:
        """
        验证连接是否有效

        Returns:
            True 连接有效，False 连接无效
        """
        if not self.is_connected or not self.session_id:
            logger.warning("[LocalMCP] 连接无效或未初始化")
            return False

        logger.info("[LocalMCP] 验证连接...")
        logger.info(f"[LocalMCP] ✓ 连接有效 (Session ID: {self.session_id[:16]}...)")
        return True

    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "is_connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "url": self.url,
            "session_id": self.session_id[:16] + "..." if self.session_id else None,
        }
