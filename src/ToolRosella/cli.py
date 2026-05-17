from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .env import load_env_file
from .mcp_construction import MCPConstructionAgent
from .pipeline import ToolRosellaPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ToolRosella",
        description="Find GitHub tools for a task and wrap them as MCP services.",
    )
    parser.add_argument("query", nargs="*", help="Task query or GitHub repository URL(s)")
    parser.add_argument("--query", dest="query_option", help="Task query string")
    parser.add_argument("--hinted-text", default="", help="Optional one-word GitHub text-search hint")
    parser.add_argument("--workspace", default="./workspace", help="Workspace for cloned repos and MCP output")
    parser.add_argument("--memory", default="./MCP_Memory", help="Processed repository cache directory")
    parser.add_argument("--per-page", type=int, default=50, help="GitHub search page size")
    parser.add_argument("--max-repositories", type=int, default=3, help="Maximum repositories to select and wrap")
    parser.add_argument("--no-refine", action="store_true", help="Disable query refinement after search failure")
    parser.add_argument("--env-file", default=".env", help="Environment file to load before running")
    return parser


async def async_main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    query = args.query_option or " ".join(args.query)
    if not query.strip():
        parser.error("provide a query or GitHub repository URL")

    load_env_file(Path(args.env_file))
    mcp_construction_agent = MCPConstructionAgent(workspace_dir=args.workspace, memory_dir=args.memory)
    pipeline = ToolRosellaPipeline(mcp_construction_agent=mcp_construction_agent)
    result = await pipeline.run(
        query=query,
        hinted_text=args.hinted_text,
        per_page=args.per_page,
        max_repositories=args.max_repositories,
        refine_on_failure=not args.no_refine,
    )

    if result.success:
        print("Repositories:")
        for repo in result.repositories:
            print(f"- {repo['name']} -> {repo['clone_url']}")
        print(f"Processed: {', '.join(result.processed_names)}")
        for package in result.mcp_packages:
            print(f"MCP package: {package}")
        print(f"Workspace: {Path(args.workspace).resolve()}")
        return 0

    print(result.message)
    return 1


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(async_main(argv))
