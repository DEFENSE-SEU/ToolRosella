from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .mcp_construction import MCPConstructionAgent
from .planning import PlanningAgent
from .tool_search import ToolSearchAgent


@dataclass
class PipelineResult:
    success: bool
    repository_name: str | None = None
    clone_url: str | None = None
    repositories: list[dict] = field(default_factory=list)
    clone_urls: list[str] = field(default_factory=list)
    processed_names: list[str] = field(default_factory=list)
    mcp_package: str | None = None
    mcp_packages: list[str] = field(default_factory=list)
    invocation_plan: dict | None = None
    message: str = ""


class ToolRosellaPipeline:
    """Coordinate Tool-search, MCP-construction, and Planning agents."""

    def __init__(
        self,
        tool_search_agent: Any | None = None,
        mcp_construction_agent: Any | None = None,
        planning_agent: Any | None = None,
    ):
        self.tool_search_agent = tool_search_agent or ToolSearchAgent()
        self.mcp_construction_agent = mcp_construction_agent or MCPConstructionAgent()
        self.planning_agent = planning_agent or PlanningAgent()

    async def run(
        self,
        query: str,
        hinted_text: str = "",
        per_page: int = 50,
        max_repositories: int = 3,
        refine_on_failure: bool = True,
    ) -> PipelineResult:
        search_result = self.tool_search_agent.search_with_metadata(
            query=query,
            hinted_text=hinted_text,
            per_page=per_page,
            max_repositories=max_repositories,
            refine_on_failure=refine_on_failure,
        )
        repositories = list(search_result.repositories)
        if not repositories:
            return PipelineResult(False, message="No suitable repository found.")

        clone_urls = [repo.clone_url for repo in repositories]
        construction = await self.mcp_construction_agent.construct_many(clone_urls)
        if not construction.get("success"):
            return PipelineResult(
                success=False,
                repository_name=repositories[0].name,
                clone_url=repositories[0].clone_url,
                repositories=[repo.__dict__ for repo in repositories],
                clone_urls=clone_urls,
                mcp_package=construction.get("mcp_package"),
                mcp_packages=list(construction.get("mcp_packages") or []),
                message=construction.get("message", "MCP construction failed."),
            )

        mcp_packages = list(construction.get("mcp_packages") or [])
        mcp_package = construction.get("mcp_package")
        invocation_plan = self.planning_agent.plan(query=query, mcp_package=mcp_packages)
        return PipelineResult(
            success=True,
            repository_name=repositories[0].name,
            clone_url=repositories[0].clone_url,
            repositories=[repo.__dict__ for repo in repositories],
            clone_urls=clone_urls,
            processed_names=list(construction.get("processed_names") or [repo.name for repo in repositories]),
            mcp_package=mcp_package,
            mcp_packages=mcp_packages,
            invocation_plan=invocation_plan,
            message="MCP services generated and invocation plan created.",
        )
