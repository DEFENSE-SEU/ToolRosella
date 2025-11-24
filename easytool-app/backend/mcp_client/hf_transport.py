"""
HuggingFace MCP HTTP POST + JSON-RPC 传输层

HuggingFace Spaces 上的 MCP 实现不遵循标准的 SSE 协议，
而是使用 HTTP POST + JSON-RPC 2.0 的方式。

本模块提供专门为 HuggingFace 设计的传输层。
"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Callable, Any

import httpx

logger = logging.getLogger(__name__)


class HFMCPTransport:
    """HuggingFace MCP HTTP 传输层"""

    def __init__(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        timeout: float = 30.0,
        auth: Optional[httpx.Auth] = None,
    ):
        """
        初始化 HF MCP 传输

        Args:
            url: MCP 服务 URL
            headers: 额外的 HTTP 头
            timeout: 请求超时（秒）
            auth: HTTP 认证
        """
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self.auth = auth
        self.client: Optional[httpx.AsyncClient] = None
        self.session_id: Optional[str] = None
        self.request_id_counter = 0

    async def __aenter__(self):
        """进入上下文"""
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            auth=self.auth,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.client:
            await self.client.aclose()
            self.client = None

    def _get_request_id(self) -> str:
        """生成唯一的请求 ID"""
        self.request_id_counter += 1
        return f"{self.request_id_counter}"

    async def _send_jsonrpc_request(
        self,
        method: str,
        params: Optional[dict] = None,
    ) -> dict:
        """
        发送 JSON-RPC 请求并等待响应

        Args:
            method: RPC 方法名
            params: 方法参数

        Returns:
            响应结果

        Raises:
            RuntimeError: 请求失败
        """
        if not self.client:
            raise RuntimeError("Transport not initialized (use async with)")

        request_id = self._get_request_id()

        # 构造 JSON-RPC 请求
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            payload["params"] = params

        logger.debug(f"Sending JSON-RPC request: {method}")

        try:
            # 发送 POST 请求
            response = await self.client.post(
                self.url,
                json=payload,
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                }
            )

            logger.debug(f"Response status: {response.status_code}")

            # 检查响应
            if response.status_code >= 400:
                logger.error(f"Request failed: {response.status_code} {response.text}")
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

            # 解析响应
            # HF 的响应格式可能是多行 event-stream，每行是一个事件
            response_text = response.text.strip()
            if response_text.startswith("event:"):
                # 解析 SSE 格式响应
                lines = response_text.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            result = json.loads(data_str)
                            logger.debug(f"Got response: {result}")
                            return result
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON: {data_str}")
                            raise RuntimeError(f"Invalid JSON in response: {data_str}")
            else:
                # 直接 JSON 响应
                try:
                    result = json.loads(response_text)
                    logger.debug(f"Got response: {result}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response_text}")
                    raise RuntimeError(f"Invalid JSON: {response_text}")

            raise RuntimeError("No valid response data found")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            raise RuntimeError(f"Request failed: {str(e)}") from e

    async def initialize(self) -> dict:
        """
        初始化 MCP 会话

        Returns:
            服务器信息和能力
        """
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "easytool-mcp-client",
                "version": "1.0.0",
            }
        }

        response = await self._send_jsonrpc_request("initialize", params)

        # 提取 session ID（如果有）
        if "result" in response and "serverInfo" in response["result"]:
            logger.info(f"Server: {response['result']['serverInfo']}")

        return response.get("result", {})

    async def list_tools(self) -> dict:
        """
        列举可用工具

        Returns:
            工具列表
        """
        response = await self._send_jsonrpc_request("tools/list")
        return response.get("result", {})

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """
        调用指定工具

        Args:
            name: 工具名
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        params = {
            "name": name,
            "arguments": arguments,
        }

        response = await self._send_jsonrpc_request("tools/call", params)
        return response.get("result", {})
