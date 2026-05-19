from __future__ import annotations

import os

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in unit tests
    OpenAI = None


class QueryOptimizer:
    """Refine a task query when repository search fails."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = None
        if OpenAI and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )

    def refine_query(self, query: str, previous_topics: list[str] | None = None) -> str:
        if not self.client:
            return query

        failed = f"\nPreviously tried topics (all returned no results): {', '.join(previous_topics)}" if previous_topics else ""
        prompt = (
            "The following GitHub repository search query returned no useful results. "
            "Reformulate it to improve recall by removing overly specific scenario descriptions, "
            "domain constraints, or contextual details that are unlikely to appear in repository "
            "names, topics, or README files. Preserve the core task intent. "
            "Return only the reformulated query as one concise sentence.\n\n"
            f"Original query: {query}{failed}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You improve GitHub tool-search queries."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=512,
            )
            refined = response.choices[0].message.content.strip() if response.choices else ""
            return refined or query
        except Exception:
            return query
