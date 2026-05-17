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

        failed = f"\nPreviously tried topics: {', '.join(previous_topics)}" if previous_topics else ""
        prompt = (
            "Transform the user's brief tool request into a more searchable GitHub query. "
            "Add relevant technical terms, expected inputs/outputs, and runnable-tool constraints. "
            "Return only one paragraph.\n\n"
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
