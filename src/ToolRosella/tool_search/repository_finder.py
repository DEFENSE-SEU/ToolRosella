from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in unit tests
    OpenAI = None


class GitHubRepositoryFinder:
    """Find GitHub repositories that can be wrapped as MCP tools."""

    def __init__(self, github_token: str | None = None):
        self.github_token = github_token if github_token is not None else os.getenv("GITHUB_TOKEN")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    def extract_github_url(self, query: str) -> str | None:
        urls = self.extract_github_urls(query)
        return urls[0] if urls else None

    def extract_github_urls(self, query: str) -> list[str]:
        urls: list[str] = []
        for owner, repo in re.findall(r"https://github\.com/([^/\s)]+)/([^/\s)]+)", query):
            repo = repo.rstrip(".,;:]}>\"'").removesuffix(".git")
            repo_url = f"https://github.com/{owner}/{repo}"
            if repo_url not in urls:
                urls.append(repo_url)
        return urls

    def to_clone_url(self, repo_url: str) -> str:
        clean_url = self._clean_github_url(repo_url)
        return clean_url if clean_url.endswith(".git") else f"{clean_url}.git"

    def extract_repo_name(self, repo_url: str) -> str:
        clean_url = self._clean_github_url(repo_url)
        parts = clean_url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        return parts[-1].removesuffix(".git")

    def find_repository(
        self,
        query: str,
        plan: Any | None = None,
        per_page: int = 50,
    ) -> tuple[str | None, str | None]:
        repositories = self.find_repositories(
            query=query,
            plan=plan,
            per_page=per_page,
            max_repositories=1,
        )
        if not repositories:
            return None, None
        return repositories[0]["name"], repositories[0]["clone_url"]

    def find_repositories(
        self,
        query: str,
        plan: Any | None = None,
        per_page: int = 50,
        max_repositories: int = 3,
    ) -> list[dict]:
        max_repositories = max(1, max_repositories)
        explicit_urls = self.extract_github_urls(query)
        if explicit_urls:
            return [
                {
                    "name": self.extract_repo_name(url),
                    "clone_url": self.to_clone_url(url),
                    "source": "explicit_url",
                    "reason": "Provided directly in the user query.",
                }
                for url in explicit_urls[:max_repositories]
            ]

        text, topics = self._plan_values(plan)
        candidates = self._collect_candidates(text=text, topics=topics, per_page=per_page)
        selected: list[dict] = []
        for repo in candidates:
            clone_url = repo.get("clone_url")
            name = repo.get("name")
            if not clone_url or not name:
                continue
            readme = self.clone_and_read_readme(clone_url, name)
            if not readme:
                continue
            is_relevant, reason = self.judge_repo_by_readme(query, readme)
            if not is_relevant:
                continue
            selected.append(
                {
                    "name": name,
                    "clone_url": clone_url,
                    "source": repo.get("source", "github_search"),
                    "reason": reason,
                }
            )
            if len(selected) >= max_repositories:
                break
        return selected

    def _collect_candidates(
        self,
        text: str | None,
        topics: list[str],
        per_page: int,
    ) -> list[dict]:
        candidates: list[dict] = []
        seen: set[str] = set()

        def add_items(items: list[dict], source: str) -> None:
            for item in items:
                clone_url = item.get("clone_url")
                if not clone_url or clone_url in seen:
                    continue
                seen.add(clone_url)
                enriched = dict(item)
                enriched["source"] = source
                candidates.append(enriched)

        if text:
            add_items(self.search_by_text(text, top_k=per_page), "text_search")

        for topic in topics:
            add_items(self.search_by_topic(topic, top_k=per_page), f"topic:{topic}")

        return candidates

    def search_by_text(self, text: str, top_k: int = 50) -> list[dict]:
        url = f"https://api.github.com/search/repositories?q={quote(text)}&per_page={top_k}"
        return self._github_search(url)

    def search_by_topic(self, topic: str, top_k: int = 50) -> list[dict]:
        url = f"https://api.github.com/search/repositories?q=topic:{quote(topic)}&per_page={top_k}"
        return self._github_search(url)

    def clone_and_read_readme(self, clone_url: str, repo_name: str) -> str | None:
        temp_parent = Path(tempfile.mkdtemp(prefix="easy-tool-repo-"))
        try:
            destination = temp_parent / repo_name
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(destination)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if result.returncode != 0:
                return None
            for path in destination.iterdir():
                if path.is_file() and "readme" in path.name.lower():
                    return path.read_text(encoding="utf-8", errors="ignore")
            return None
        except Exception:
            return None
        finally:
            shutil.rmtree(temp_parent, ignore_errors=True)

    def judge_repo_by_readme(self, query: str, readme: str) -> tuple[bool, str]:
        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            return self._heuristic_readme_judgement(readme), "Heuristic README judgement."

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        system_judge = (
            "Given a user query and a GitHub README, decide whether the repository is "
            "suitable to solve the query. It must be code-based, runnable locally from "
            "the command line, include setup instructions, and match the task. Return:\n"
            "Reason: <brief reason>\nJudge: Yes/No"
        )
        content = f"Query:\n{query}\n\nREADME:\n{readme[:15000]}"
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": system_judge},
                    {"role": "user", "content": content},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content if response.choices else ""
            match = re.findall(r"\**Judge:\**\s*(\w+)", answer)
            return bool(match and match[0].lower() == "yes"), answer
        except Exception as exc:
            return False, f"LLM judgement failed: {exc}"

    def _github_search(self, url: str) -> list[dict]:
        try:
            response = requests.get(url, headers=self._headers(), timeout=15)
            if response.status_code == 200:
                return response.json().get("items", [])
        except Exception:
            return []
        return []

    def _clean_github_url(self, repo_url: str) -> str:
        match = re.match(r"https://github\.com/([^/\s)]+)/([^/\s)]+)", repo_url)
        if not match:
            return repo_url.rstrip("/")
        owner, repo = match.groups()
        return f"https://github.com/{owner}/{repo.removesuffix('.git')}"

    def _plan_values(self, plan: Any | None) -> tuple[str | None, list[str]]:
        if plan is None:
            return None, []
        if isinstance(plan, dict):
            return plan.get("text"), list(plan.get("topics") or [])
        return getattr(plan, "text", None), list(getattr(plan, "topics", []) or [])

    def _heuristic_readme_judgement(self, readme: str) -> bool:
        text = (readme or "").lower()
        has_setup = any(word in text for word in ["install", "installation", "setup", "requirements"])
        has_usage = any(word in text for word in ["usage", "command", "run", "python ", "cli", "example"])
        return has_setup and has_usage


def load_repo_cache(path: str | Path = "repo_cache.json") -> dict:
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
