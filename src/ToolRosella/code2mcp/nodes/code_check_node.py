from __future__ import annotations

import ast
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def code_check_node(state: dict[str, Any]) -> dict[str, Any]:
    """Validate generated MCP imports against symbols exported by source modules."""
    repo = state.get("repository", {})
    local_paths = repo.get("local_paths", {})
    source_root = local_paths.get("source_root") or os.path.join(local_paths.get("repo_root", ""), "source")
    mcp_plugin = local_paths.get("mcp_plugin") or os.path.join(
        local_paths.get("repo_root", ""),
        "mcp_output",
        "mcp_plugin",
    )
    available_symbols = _scan_available_symbols(Path(source_root))
    generated_files = [
        Path(mcp_plugin) / "mcp_service.py",
        Path(mcp_plugin) / "adapter.py",
    ]

    issues: list[dict[str, Any]] = []
    for file_path in generated_files:
        if not file_path.exists():
            continue
        file_issues = _validate_imports(file_path, available_symbols)
        if file_issues and os.getenv("TOOLROSELLA_CODECHECK_REPAIR", "false").lower() == "true":
            repaired = _repair_with_llm(file_path, file_issues, available_symbols)
            if repaired:
                file_issues = _validate_imports(file_path, available_symbols)
                state.setdefault("code_check_fixes", []).append(str(file_path))
        issues.extend(file_issues)

    passed = not issues
    state["code_check"] = {
        "passed": passed,
        "issues": issues,
        "available_modules": sorted(available_symbols.keys()),
    }

    repo_root = local_paths.get("repo_root")
    if repo_root:
        report_path = os.path.join(repo_root, "mcp_output", "code_check.json")
        _write_file(report_path, json.dumps(state["code_check"], ensure_ascii=False, indent=2))

    if not passed:
        state.setdefault("errors", []).append(
            {
                "node": "CodeCheckNode",
                "type": "InvalidGeneratedImport",
                "severity": "high",
                "message": f"{len(issues)} invalid generated import reference(s)",
                "details": issues,
                "action_taken": "send_to_review",
            }
        )
        state["run_result"] = {
            "success": False,
            "error_type": "CodeCheckError",
            "error": f"{len(issues)} invalid generated import reference(s)",
            "stderr": json.dumps(issues, ensure_ascii=False),
        }

    state["status"] = "running"
    state["workflow_status"] = state.get("workflow_status", "running")
    return state


def _scan_available_symbols(source_root: Path) -> dict[str, set[str]]:
    symbols: dict[str, set[str]] = {}
    if not source_root.exists():
        return symbols

    for file_path in source_root.rglob("*.py"):
        if any(part in {"__pycache__", ".git", "tests", "test"} for part in file_path.parts):
            continue
        module = ".".join(file_path.relative_to(source_root).with_suffix("").parts)
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        exported = _extract_public_symbols(file_path)
        if exported:
            symbols[module] = exported
    return symbols


def _write_file(file_path: str, content: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(content)


def _extract_public_symbols(file_path: Path) -> set[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return set()
    exported: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            exported.add(node.name)
    return exported


def _validate_imports(file_path: Path, available_symbols: dict[str, set[str]]) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError as exc:
        return [
            {
                "file": str(file_path),
                "type": "syntax_error",
                "message": str(exc),
            }
        ]

    issues: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        module = _normalize_module(node.module)
        if module not in available_symbols:
            continue
        exported = available_symbols[module]
        for alias in node.names:
            if alias.name == "*":
                continue
            if alias.name not in exported:
                issues.append(
                    {
                        "file": str(file_path),
                        "module": module,
                        "symbol": alias.name,
                        "type": "missing_symbol",
                    }
                )
    return issues


def _normalize_module(module: str) -> str:
    if module.startswith("source."):
        return module[len("source.") :]
    if module.startswith("src."):
        return module[len("src.") :]
    return module


def _repair_with_llm(
    file_path: Path,
    issues: list[dict[str, Any]],
    available_symbols: dict[str, set[str]],
) -> bool:
    try:
        from ..utils import get_llm_service

        llm_service = get_llm_service()
        current = file_path.read_text(encoding="utf-8", errors="ignore")
        prompt = (
            "Fix this generated FastMCP service so all imports and tool wrappers match the "
            "available source-code symbols. Return only complete Python source code.\n\n"
            f"File: {file_path}\n"
            f"Issues: {json.dumps(issues, ensure_ascii=False, indent=2)}\n"
            f"Available symbols: {_serialize_symbols(available_symbols)}\n\n"
            f"Current code:\n{current}"
        )
        fixed = llm_service.generate_text(
            prompt,
            "You are a strict Python repair agent. Return only complete Python code.",
        )
        fixed = _strip_code_fences(fixed)
        ast.parse(fixed)
        file_path.write_text(fixed, encoding="utf-8")
        return True
    except Exception as exc:
        logger.warning(f"CodeCheck LLM repair skipped or failed for {file_path}: {exc}")
        return False


def _serialize_symbols(available_symbols: dict[str, set[str]]) -> str:
    serializable = {
        module: sorted(symbols)
        for module, symbols in sorted(available_symbols.items())
    }
    return json.dumps(serializable, ensure_ascii=False, indent=2)


def _strip_code_fences(content: str) -> str:
    content = re.sub(r"^```(?:python)?\s*\n?", "", content or "")
    content = re.sub(r"\n?\s*```\s*$", "", content)
    return content.strip()
