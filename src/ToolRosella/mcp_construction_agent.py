from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


class MCPConstructionAgent:
    """Transform a GitHub repository into a validated MCP package."""

    def __init__(
        self,
        workspace_dir: str | Path = "./workspace",
        memory_dir: str | Path = "./MCP_Memory",
    ):
        self.workspace_dir = Path(workspace_dir)
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.processed_repos_file = self.memory_dir / "processed_repos.json"
        self.processed_repos = self._load_processed_repos()

    async def construct(self, repo_url: str) -> dict:
        repo_name = self.extract_repo_name(repo_url)
        existing = self._successful_record(repo_name)
        if existing:
            return {
                "success": True,
                "processed_names": [repo_name],
                "mcp_package": existing.get("mcp_package"),
                "message": "Repository already processed.",
            }

        from .code2mcp.workflow import WorkflowOrchestrator

        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        orchestrator = WorkflowOrchestrator(workspace_dir=str(self.workspace_dir))
        result = await orchestrator.run_workflow(repo_url)
        success = bool(result.get("success"))
        mcp_package = self._extract_mcp_package(result)
        self._record_repo(repo_name, repo_url, success, result.get("message", ""), mcp_package)
        return {
            "success": success,
            "processed_names": [repo_name] if success else [],
            "mcp_package": mcp_package,
            "message": result.get("message", ""),
            "state": result.get("state"),
        }

    async def construct_many(self, repo_urls: list[str]) -> dict:
        results: list[dict] = []
        seen: set[str] = set()
        for repo_url in repo_urls:
            if repo_url in seen:
                continue
            seen.add(repo_url)
            try:
                repo_name = self.extract_repo_name(repo_url)
                result = await self.construct(repo_url)
            except Exception as exc:
                repo_name = repo_url
                result = {
                    "success": False,
                    "processed_names": [],
                    "mcp_package": None,
                    "message": str(exc),
                }
            result["repo_url"] = repo_url
            result["repo_name"] = repo_name
            results.append(result)

        successful = [result for result in results if result.get("success")]
        mcp_packages = [
            result["mcp_package"]
            for result in successful
            if result.get("mcp_package")
        ]
        processed_names: list[str] = []
        for result in successful:
            processed_names.extend(result.get("processed_names") or [])

        return {
            "success": bool(successful),
            "repositories": results,
            "processed_names": processed_names,
            "mcp_packages": mcp_packages,
            "mcp_package": mcp_packages[0] if mcp_packages else None,
            "message": self._summarize_many(results),
        }

    def extract_repo_name(self, github_url: str) -> str:
        parsed = urlparse(github_url.removesuffix(".git"))
        if parsed.netloc != "github.com":
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        return parts[1]

    def _extract_mcp_package(self, result: dict) -> str | None:
        state = result.get("state") or {}
        plugin = state.get("plugin") or {}
        mcp_dir = plugin.get("mcp_dir")
        if mcp_dir:
            return str(Path(mcp_dir).parent)
        repo_root = ((state.get("repository") or {}).get("local_paths") or {}).get("repo_root")
        if repo_root:
            return str(Path(repo_root) / "mcp_output")
        return None

    def _successful_record(self, repo_name: str) -> dict | None:
        for repo in self.processed_repos:
            if repo.get("name") == repo_name and repo.get("status") == "success":
                return repo
        return None

    def _load_processed_repos(self) -> list[dict]:
        if not self.processed_repos_file.exists():
            return []
        try:
            return json.loads(self.processed_repos_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_processed_repos(self) -> None:
        self.processed_repos_file.write_text(
            json.dumps(self.processed_repos, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _record_repo(
        self,
        repo_name: str,
        repo_url: str,
        success: bool,
        message: str,
        mcp_package: str | None,
    ) -> None:
        self.processed_repos.append(
            {
                "name": repo_name,
                "url": repo_url,
                "processed_time": datetime.now().isoformat(),
                "status": "success" if success else "failed",
                "message": message,
                "mcp_package": mcp_package,
            }
        )
        self._save_processed_repos()

    def _summarize_many(self, results: list[dict]) -> str:
        if not results:
            return "No repositories were processed."
        success_count = sum(1 for result in results if result.get("success"))
        return f"MCP construction completed for {success_count}/{len(results)} repositories."


async def construct_mcp_package(
    github_url: str,
    workspace_dir: str | Path = "./workspace",
) -> dict:
    return await MCPConstructionAgent(workspace_dir=workspace_dir).construct(github_url)
