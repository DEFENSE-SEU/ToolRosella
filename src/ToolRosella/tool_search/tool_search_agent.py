from __future__ import annotations

from dataclasses import dataclass, field

from .planner import LLMPlanner
from .query_optimizer import QueryOptimizer
from .repository_finder import GitHubRepositoryFinder


@dataclass
class RepositoryCandidate:
    name: str
    clone_url: str
    source: str = ""
    reason: str = ""


@dataclass
class ToolSearchResult:
    query_used: str
    repositories: list[RepositoryCandidate] = field(default_factory=list)

    @property
    def repository_name(self) -> str | None:
        return self.repositories[0].name if self.repositories else None

    @property
    def clone_url(self) -> str | None:
        return self.repositories[0].clone_url if self.repositories else None


class ToolSearchAgent:
    """Retrieve task-relevant GitHub repositories for ToolRosella."""

    def __init__(
        self,
        planner: LLMPlanner | None = None,
        finder: GitHubRepositoryFinder | None = None,
        optimizer: QueryOptimizer | None = None,
    ):
        self.planner = planner or LLMPlanner()
        self.finder = finder or GitHubRepositoryFinder()
        self.optimizer = optimizer or QueryOptimizer()

    def search(
        self,
        query: str,
        hinted_text: str = "",
        per_page: int = 50,
        max_repositories: int = 3,
        refine_on_failure: bool = True,
    ) -> list[RepositoryCandidate]:
        result = self.search_with_metadata(
            query=query,
            hinted_text=hinted_text,
            per_page=per_page,
            max_repositories=max_repositories,
            refine_on_failure=refine_on_failure,
        )
        return result.repositories

    def search_with_metadata(
        self,
        query: str,
        hinted_text: str = "",
        per_page: int = 50,
        max_repositories: int = 3,
        refine_on_failure: bool = True,
    ) -> ToolSearchResult:
        if self.finder.extract_github_url(query):
            repositories = self._to_candidates(self.finder.find_repositories(
                query=query,
                plan=None,
                per_page=per_page,
                max_repositories=max_repositories,
            ))
            return ToolSearchResult(query_used=query, repositories=repositories)

        plan = self.planner.get_search_plan(query, hinted_text=hinted_text)
        repositories = self._to_candidates(self.finder.find_repositories(
            query=query,
            plan=plan,
            per_page=per_page,
            max_repositories=max_repositories,
        ))
        if repositories:
            return ToolSearchResult(query_used=query, repositories=repositories)

        if not refine_on_failure:
            return ToolSearchResult(query_used=query, repositories=[])

        refined_query = self.optimizer.refine_query(query, previous_topics=list(plan.topics))
        if refined_query == query:
            return ToolSearchResult(query_used=query, repositories=[])

        refined_plan = self.planner.get_search_plan(refined_query, hinted_text="")
        repositories = self._to_candidates(self.finder.find_repositories(
            query=refined_query,
            plan=refined_plan,
            per_page=per_page,
            max_repositories=max_repositories,
        ))
        return ToolSearchResult(query_used=refined_query, repositories=repositories)

    def _to_candidates(self, repositories: list[dict]) -> list[RepositoryCandidate]:
        candidates: list[RepositoryCandidate] = []
        for repo in repositories:
            name = repo.get("name")
            clone_url = repo.get("clone_url")
            if not name or not clone_url:
                continue
            candidates.append(
                RepositoryCandidate(
                    name=name,
                    clone_url=clone_url,
                    source=repo.get("source", ""),
                    reason=repo.get("reason", ""),
                )
            )
        return candidates
