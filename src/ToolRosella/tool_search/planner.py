from __future__ import annotations

from dataclasses import dataclass, field
import os
import re

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in unit tests
    OpenAI = None


@dataclass
class SearchPlan:
    strategy: str = "topics"
    text: str | None = None
    topics: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "text": self.text,
            "topics": list(self.topics),
        }


class LLMPlanner:
    """Build the GitHub search plan for a user task."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = None
        if OpenAI and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )

        self.topic_system_prompt = (
            "You are a professional programmer. Given a query, identify GitHub topics "
            "that can find a repository able to solve it. Return only a comma-separated "
            "list of noun-like topics. Use hyphens for multi-word topics."
        )
        self.text_hint_prompt = (
            "Given the user query, output one single word that is most useful for GitHub "
            "repository text search, such as a repository name or key technical term. "
            "If there is no good word, output exactly NONE."
        )

    def generate_text_hint(self, query: str) -> str:
        match = re.search(r"github\.com/[^/\s)]+/([A-Za-z0-9_.-]+)", query)
        if match:
            return match.group(1).removesuffix(".git")
        if not self.client:
            return ""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.text_hint_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.2,
                max_tokens=16,
            )
            content = response.choices[0].message.content.strip() if response.choices else ""
            return "" if content.upper() == "NONE" else content.split()[0]
        except Exception:
            return ""

    def generate_topics(self, query: str) -> list[str]:
        if not self.client:
            return []
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.topic_system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.2,
                max_tokens=256,
            )
            content = response.choices[0].message.content if response.choices else ""
        except Exception:
            return []

        match = re.search(r"\*+\s*\n(.+?)\n\*+", content, re.DOTALL)
        topic_text = match.group(1) if match else content
        return [topic.strip() for topic in topic_text.split(",") if topic.strip()][:5]

    def get_search_plan(self, query: str, hinted_text: str = "") -> SearchPlan:
        text_hint = hinted_text.strip() if hinted_text else self.generate_text_hint(query)
        topics = self.generate_topics(query)
        return SearchPlan(
            strategy="text_then_topics" if text_hint else "topics",
            text=text_hint or None,
            topics=topics,
        )
