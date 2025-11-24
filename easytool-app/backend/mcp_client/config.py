"""
配置管理模块

从 mcp.json 读取 MCP 服务配置，并进行验证和补充默认值。
这是"单一事实来源"，避免配置在代码和文件之间重复。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ServiceConfig:
    """MCP 服务配置管理"""

    @staticmethod
    def load_from_file(config_path: str = "mcp.json") -> Dict[str, dict]:
        """
        从 mcp.json 读取配置

        Args:
            config_path: 配置文件路径，默认为当前目录的 mcp.json

        Returns:
            服务配置字典
            {
                "service_name": {
                    "url": "https://...",
                    "description": "...",
                    ...
                },
                ...
            }

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误或缺少必要字段
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        logger.info(f"读取配置文件: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {str(e)}")

        # 提取 mcpServers 节点
        mcp_servers = config_data.get("mcpServers", {})

        if not mcp_servers:
            logger.warning("⚠️  配置文件中没有 mcpServers")
            return {}

        # 验证和补充配置
        services = {}
        for service_name, service_config in mcp_servers.items():
            try:
                services[service_name] = ServiceConfig._validate_service_config(
                    service_name,
                    service_config
                )
            except ValueError as e:
                logger.warning(f"⚠️  跳过服务 {service_name}: {str(e)}")
                continue

        logger.info(f"✓ 成功加载 {len(services)} 个服务: {', '.join(services.keys())}")

        return services

    @staticmethod
    def _validate_service_config(service_name: str, config: dict) -> dict:
        """
        验证单个服务配置

        Args:
            service_name: 服务名称
            config: 服务配置字典

        Returns:
            验证并补充后的配置字典

        Raises:
            ValueError: 配置缺少必要字段或格式错误
        """
        if not isinstance(config, dict):
            raise ValueError(f"{service_name}: 配置必须是字典")

        if "url" not in config:
            raise ValueError(f"{service_name}: 缺少 'url' 字段")

        validated_config = {
            "url": str(config["url"]),
            "description": config.get("description", f"MCP Service: {service_name}"),
            "icon": config.get("icon", "🔧"),
        }

        # 验证 URL 格式
        if not validated_config["url"].startswith(("http://", "https://")):
            raise ValueError(f"{service_name}: URL 必须以 http:// 或 https:// 开头")

        # 验证 URL 是否包含 /mcp 路径（MCP SSE 端点）
        if not "/mcp" in validated_config["url"]:
            logger.warning(
                f"⚠️  {service_name}: URL 中没有 /mcp 路径，"
                f"可能无法正常工作。URL: {validated_config['url']}"
            )

        return validated_config

    @staticmethod
    def create_sample_config(output_path: str = "mcp.json.sample") -> None:
        """
        创建示例配置文件

        Args:
            output_path: 输出文件路径
        """
        sample_config = {
            "mcpServers": {
                "sympy": {
                    "url": "https://kabuda777-Code2MCP-sympy.hf.space/mcp",
                    "description": "数学符号计算 - 解方程、求导、积分等",
                    "icon": "📐"
                },
                "vaderSentiment": {
                    "url": "https://ArthurY-vaderSentiment.hf.space/mcp",
                    "description": "情感分析 - 分析文本情感倾向",
                    "icon": "💭"
                },
                "physicsnemo": {
                    "url": "https://ArthurY-physicsnemo.hf.space/mcp",
                    "description": "物理模拟 - 量子物理、粒子模拟",
                    "icon": "⚛️"
                },
                "obspy": {
                    "url": "https://ArthurY-xujie-mcp.hf.space/mcp",
                    "description": "地震学分析 - 地震波处理、地震事件分析",
                    "icon": "🌍"
                },
                "socialsim": {
                    "url": "https://ArthurY-socialsim.hf.space/mcp",
                    "description": "社交模拟 - 社交网络分析和模拟",
                    "icon": "👥"
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ 样例配置已写入: {output_path}")


# 便利函数：直接从环境或文件加载配置
def load_mcp_services(config_path: Optional[str] = None) -> Dict[str, dict]:
    """
    快速加载 MCP 服务配置

    Args:
        config_path: 配置文件路径。如果为 None，尝试在以下位置查找：
                    1. 当前目录的 mcp.json
                    2. 环境变量 MCP_CONFIG_PATH 指定的位置

    Returns:
        服务配置字典

    Raises:
        FileNotFoundError: 无法找到配置文件
    """
    import os

    if config_path is None:
        # 尝试默认位置
        if Path("mcp.json").exists():
            config_path = "mcp.json"
        else:
            config_path = os.environ.get("MCP_CONFIG_PATH", "mcp.json")

    return ServiceConfig.load_from_file(config_path)
