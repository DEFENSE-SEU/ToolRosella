from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


class PlanningAgent:
    """Create and optionally run a Claude-Code-like MCP calling plan."""

    def __init__(self, output_dir: str | Path = "./planning_runs"):
        self.output_dir = Path(output_dir)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = None
        if OpenAI and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )

    def plan(
        self,
        query: str,
        mcp_package: str | Path | list[str | Path] | None,
        execute: bool | None = None,
        previous_result: dict | None = None,
    ) -> dict:
        package_paths = self._normalize_packages(mcp_package)
        tools = self.discover_tools(package_paths)
        mcp_config = self.build_mcp_config(package_paths)
        steps = self._map_tools_to_subtasks(query, tools)
        prompt = self.build_agent_prompt(query, tools, previous_result=previous_result)
        run_dir = self.write_agent_run(query, package_paths, mcp_config, prompt)

        should_execute = (
            execute
            if execute is not None
            else os.getenv("TOOLROSELLA_RUN_PLANNING_AGENT", "false").lower() == "true"
        )
        execution = self.execute_agent(run_dir) if should_execute else {"executed": False}

        if not tools:
            return {
                "query": query,
                "tools": [],
                "steps": [],
                "mcp_config": mcp_config,
                "agent_prompt": prompt,
                "run_dir": str(run_dir) if run_dir else None,
                "execution": execution,
                "message": "No MCP tools were discovered for planning.",
            }

        return {
            "query": query,
            "tools": tools,
            "steps": steps,
            "mcp_config": mcp_config,
            "agent_prompt": prompt,
            "run_dir": str(run_dir) if run_dir else None,
            "execution": execution,
        }

    def discover_tools(self, mcp_package: str | Path | list[str | Path] | None) -> list[dict]:
        package_paths = self._normalize_packages(mcp_package)
        tools: list[dict] = []
        for server_name, package_path in self._package_entries(package_paths):
            service_path = package_path / "mcp_plugin" / "mcp_service.py"
            if not service_path.exists():
                continue
            source = service_path.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r"@mcp\.tool\((.*?)\)\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", source, re.DOTALL):
                decorator_args, function_name = match.groups()
                name_match = re.search(r"name\s*=\s*[\"']([^\"']+)[\"']", decorator_args)
                description_match = re.search(r"description\s*=\s*[\"']([^\"']+)[\"']", decorator_args)
                tools.append(
                    {
                        "server": server_name,
                        "name": name_match.group(1) if name_match else function_name,
                        "function": function_name,
                        "description": description_match.group(1) if description_match else "",
                    }
                )
        return tools

    def build_mcp_config(self, mcp_package: str | Path | list[str | Path] | None) -> dict:
        package_paths = self._normalize_packages(mcp_package)
        if not package_paths:
            return {"mcpServers": {}}
        servers = {}
        for server_name, package_path in self._package_entries(package_paths):
            start_mcp = package_path / "start_mcp.py"
            python_bin = self._find_python(package_path)
            servers[server_name] = {
                "command": python_bin,
                "args": [str(start_mcp)],
                "env": {
                    "MCP_TRANSPORT": "stdio",
                },
            }
        return {"mcpServers": servers}

    def build_agent_prompt(
        self,
        query: str,
        tools: list[dict],
        previous_result: dict | None = None,
    ) -> str:
        tool_lines = "\n".join(
            f"- {tool.get('server', 'mcp')}.{tool['name']}: {tool.get('description') or 'No description'}"
            for tool in tools
        ) or "- No tools discovered."

        previous_context = ""
        if previous_result:
            prev_query = previous_result.get("query", "")
            prev_answer = (previous_result.get("execution") or {}).get("final_answer", "")
            previous_context = (
                f"\nPrevious query: {prev_query}\n"
                f"Previous result:\n{prev_answer[:800] if prev_answer else 'No result available.'}\n\n"
                "Re-evaluate the objectives and constraints based on the above, "
                "then update your plan accordingly.\n"
            )

        return (
            "You are the ToolRosella Planning Agent. You are running in a Claude-Code-like "
            "agent environment with MCP tools already registered.\n\n"
            + previous_context
            + "Task:\n"
            f"{query}\n\n"
            "Available MCP tools:\n"
            f"{tool_lines}\n\n"
            "Plan and execute the task by selecting the smallest necessary sequence of MCP "
            "tool calls. You may combine tools from different MCP servers when the task "
            "requires complementary capabilities. After each call, inspect the result and decide the next action. "
            "Return the final answer with the tool calls used and any important intermediate outputs."
        )

    def write_agent_run(
        self,
        query: str,
        mcp_package: str | Path | list[str | Path] | None,
        mcp_config: dict,
        prompt: str,
    ) -> Path | None:
        package_paths = self._normalize_packages(mcp_package)
        if not package_paths:
            return None
        if len(package_paths) == 1:
            run_dir = package_paths[0] / "planning_agent"
        else:
            common_root = Path(os.path.commonpath([str(path.parent) for path in package_paths]))
            if str(common_root) == common_root.anchor:
                common_root = self.output_dir.resolve()
            run_dir = common_root / "planning_agent"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "mcp.json").write_text(
            json.dumps(mcp_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (run_dir / "task_prompt.md").write_text(prompt, encoding="utf-8")
        (run_dir / "query.txt").write_text(query, encoding="utf-8")
        return run_dir

    def execute_agent(self, run_dir: str | Path | None, timeout: int = 600) -> dict:
        if not run_dir:
            return {"executed": False, "error": "No planning run directory."}
        command = os.getenv("TOOLROSELLA_AGENT_COMMAND", "claude")
        executable = shutil.which(command)
        if not executable:
            return {"executed": False, "error": f"Agent command not found: {command}"}

        run_path = Path(run_dir)
        prompt_path = run_path / "task_prompt.md"
        config_path = run_path / "mcp.json"
        prompt = prompt_path.read_text(encoding="utf-8")
        cmd = [executable, "-p", prompt, "--mcp-config", str(config_path)]
        result = subprocess.run(
            cmd,
            cwd=str(run_path),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        (run_path / "agent_stdout.txt").write_text(result.stdout or "", encoding="utf-8")
        (run_path / "agent_stderr.txt").write_text(result.stderr or "", encoding="utf-8")
        return {
            "executed": True,
            "returncode": result.returncode,
            "final_answer": result.stdout or "",
            "stdout_path": str(run_path / "agent_stdout.txt"),
            "stderr_path": str(run_path / "agent_stderr.txt"),
        }

    def _map_tools_to_subtasks(self, query: str, tools: list[dict]) -> list[dict]:
        if not tools:
            return []
        if not self.client:
            return self._fallback_steps(tools)
        tool_descriptions = "\n".join(
            f"- {t.get('server', 'mcp')}.{t['name']}: {t.get('description') or 'No description'}"
            for t in tools
        )
        system_prompt = (
            "You are a task planning assistant. Given a user task and available MCP tools, "
            "map each necessary tool to a specific subtask and determine execution order. "
            "Only include tools that are actually needed for the task. "
            "Return a JSON object with a \"steps\" array. Each element must have: "
            "\"step\" (int), \"tool\" (server.tool_name), "
            "\"subtask\" (what this step accomplishes), \"reason\" (why this tool is chosen)."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Task: {query}\n\nAvailable tools:\n{tool_descriptions}"},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            content = response.choices[0].message.content.strip() if response.choices else ""
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return self._fallback_steps(tools)
            parsed = json.loads(json_match.group())
            raw_steps = parsed.get("steps") or []
            return [
                {
                    "step": s.get("step", i + 1),
                    "tool": s.get("tool", ""),
                    "subtask": s.get("subtask", ""),
                    "reason": s.get("reason", ""),
                }
                for i, s in enumerate(raw_steps)
                if isinstance(s, dict)
            ]
        except Exception:
            return self._fallback_steps(tools)

    def _fallback_steps(self, tools: list[dict]) -> list[dict]:
        return [
            {
                "step": i + 1,
                "tool": f"{t.get('server', 'mcp')}.{t['name']}",
                "subtask": t.get("description") or t["name"],
                "reason": f"Use `{t.get('server', 'mcp')}.{t['name']}` to handle the corresponding subtask.",
            }
            for i, t in enumerate(tools)
        ]

    def _find_python(self, package_path: Path) -> str:
        candidates = [
            package_path / ".venv" / "bin" / "python",
            package_path / ".venv" / "Scripts" / "python.exe",
            package_path.parent / ".venv" / "bin" / "python",
            package_path.parent / ".venv" / "Scripts" / "python.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return shutil.which("python3") or shutil.which("python") or "python"

    def _normalize_packages(self, mcp_package: str | Path | list[str | Path] | None) -> list[Path]:
        if not mcp_package:
            return []
        if isinstance(mcp_package, (str, Path)):
            packages = [mcp_package]
        else:
            packages = list(mcp_package)
        normalized: list[Path] = []
        for package in packages:
            if not package:
                continue
            path = Path(package).resolve()
            if path not in normalized:
                normalized.append(path)
        return normalized

    def _package_entries(self, package_paths: list[Path]) -> list[tuple[str, Path]]:
        entries: list[tuple[str, Path]] = []
        counts: dict[str, int] = {}
        for package_path in package_paths:
            base_name = package_path.parent.name or package_path.name
            count = counts.get(base_name, 0) + 1
            counts[base_name] = count
            server_name = base_name if count == 1 else f"{base_name}_{count}"
            entries.append((server_name, package_path))
        return entries
