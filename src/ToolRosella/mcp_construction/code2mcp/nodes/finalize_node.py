from __future__ import annotations

import json
import os
import time
from typing import Any

from ..utils import setup_logging, write_file

logger = setup_logging()


def finalize_node(state: dict[str, Any]) -> dict[str, Any]:
    """Finish Node: consolidate the generated MCP package metadata."""
    repo = state.get("repository", {})
    local_paths = repo.get("local_paths", {})
    repo_root = local_paths.get("repo_root")
    if not repo_root:
        state["status"] = "failed"
        state["workflow_status"] = "failed"
        state["error"] = "Missing repository root during finish stage."
        return state

    mcp_output_dir = os.path.join(repo_root, "mcp_output")
    plugin = state.get("plugin", {})
    run_result = state.get("run_result", {})
    summary = {
        "repository": {
            "name": repo.get("name"),
            "url": repo.get("url"),
        },
        "mcp_package": mcp_output_dir,
        "entrypoint": os.path.join(mcp_output_dir, plugin.get("main_entry", "start_mcp.py")),
        "adapter_mode": plugin.get("adapter_mode"),
        "endpoints": plugin.get("endpoints", []),
        "files": plugin.get("files", {}),
        "code_check": state.get("code_check", {}),
        "tests": state.get("tests", {}),
        "run_result": run_result,
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
        "finished_at": time.time(),
    }

    write_file(
        os.path.join(mcp_output_dir, "workflow_summary.json"),
        json.dumps(summary, ensure_ascii=False, indent=2),
    )

    if run_result.get("success", False):
        state["workflow_status"] = "success"
        state["status"] = "success"
    else:
        state["workflow_status"] = "failed"
        state["status"] = "failed"
        state["error"] = run_result.get("error", "MCP validation failed.")

    logger.info("Finish node completed")
    return state
