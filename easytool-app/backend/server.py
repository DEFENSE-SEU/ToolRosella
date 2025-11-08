import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="EasyTool Backend", version="0.1.0")


class RunReq(BaseModel):
    query: str


def _bootstrap_paths_and_env() -> Dict[str, Any]:
    here = Path(__file__).resolve()
    project_root = here.parents[2]  # .../Easy-Tool
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Load .env at project root if present
    try:
        from dotenv import load_dotenv
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
    except Exception:
        pass

    return {
        "project_root": project_root,
        "workspace_root": project_root / "MCP-agent-github-repo-output" / "workspace",
    }


@app.get("/")
def root():
    return {"service": "easytool-backend", "status": "ok"}


@app.post("/run")
async def run(req: RunReq):
    ctx = _bootstrap_paths_and_env()
    project_root: Path = ctx["project_root"]
    workspace_root: Path = ctx["workspace_root"]

    try:
        from LLM_Plan import get_search_plan
        from RAG import GitHubRAG
        from MCP import process_github_repos
    except Exception as e:
        return {"success": False, "message": f"Import error: {e}"}

    query = (req.query or "").strip()
    if not query:
        return {"success": False, "message": "Empty query"}

    try:
        rag = GitHubRAG()
        plan = get_search_plan(query, hinted_text="")

        name, clone_url = rag.search_and_judge(
            query=query,
            text=plan.get("text") or "",
            topics=plan.get("topics") or [],
            per_page=50,
        )

        if not (name and clone_url):
            # fallback to summary route
            name, clone_url = rag.search_and_judge_summary(
                query=query,
                text=plan.get("text") or "",
                topics=plan.get("topics") or [],
                per_page=50,
            )

        if not (name and clone_url):
            return {
                "success": False,
                "message": "No suitable repository found",
                "plan": plan,
            }

        result = await process_github_repos(clone_url)
        success = bool(result.get("success"))

        resp: Dict[str, Any] = {
            "success": success,
            "plan": plan,
            "repo": {"name": name, "clone_url": clone_url},
            "processed_names": result.get("processed_names", []),
        }

        # Try to list generated MCP tools if available
        repo_ws_dir = workspace_root / name
        plugin_dir = repo_ws_dir / "mcp_output" / "mcp_plugin"
        start_mcp = repo_ws_dir / "mcp_output" / "start_mcp.py"
        resp["workspace"] = {
            "root": str(repo_ws_dir),
            "plugin_dir": str(plugin_dir),
            "start_mcp": str(start_mcp),
        }

        tools: list[str] = []
        if plugin_dir.exists():
            try:
                sys.path.insert(0, str(plugin_dir))
                from mcp_service import create_app  # type: ignore
                mcp_app = create_app()
                try:
                    tools = list(mcp_app.tools.keys())
                except Exception:
                    tools = []
            except Exception:
                tools = []
        resp["tools"] = tools

        return resp

    except Exception as e:
        return {"success": False, "message": str(e)}



