import re
import os
from typing import List, Optional, Tuple, Dict
from openai import OpenAI

from LLM_Plan import LLMPlanner
from RAG import GitHubRAG


class LLMNoRepoOptimizer:

    def __init__(self, rag: Optional[GitHubRAG] = None):
        self.rag = rag or GitHubRAG()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        self.model = "deepseek-r1"
        self.planner = LLMPlanner()

    def _llm_redesign(self, query: str, failed_topics: Optional[List[str]] = None) -> str:
        sys_prompt = """You are an expert researcher and query enhancement specialist. 
Your task is to transform a user's brief, high-level request into a much more detailed, comprehensive query that includes all relevant context, specifications, and requirements.

The enhanced query should:
1. Expand on the core request with detailed specifications and context
2. Include relevant technical terms, methodologies, and domain-specific vocabulary
3. Specify desired input/output formats, data types, and expected results
4. Add related concepts, alternatives, and edge cases that should be considered
5. Include practical constraints like performance requirements, scalability needs, or resource limitations
6. Mention relevant standards, protocols, or best practices in the domain
7. Specify any quality criteria, accuracy requirements, or validation methods
8. Add context about typical use cases, applications, or scenarios

For example:
- If asked about "chemical reactions for O=C(OCC)C", expand to include synthesis methods, reaction conditions, catalysts, yields, safety considerations, alternative pathways, etc.

Transform the brief query into a comprehensive, detailed request that captures all the nuances and requirements that would lead to better, more complete results.

Return ONLY the enhanced detailed query as a single, comprehensive paragraph."""


        user_content_parts = [f"Original Query: {query}"]
        
        if failed_topics:
            user_content_parts.append(f"Previously tried topics that didn't work well: {', '.join(failed_topics)}")
            
        user_content = "\n\n".join(user_content_parts)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.5,  
                max_tokens=512,   
            )
            content = resp.choices[0].message.content if resp.choices else ""
        except Exception as e:
            print(f"LLM redesign failed: {e}")
            content = ""
            
        refined_query = (content or "").strip()
        return refined_query if refined_query else query

    def refine_query(self, query: str, prev_topics: Optional[List[str]] = None) -> str:
        failed_topics = prev_topics if prev_topics else None
        refined = self._llm_redesign(query, failed_topics)
        return refined if refined and refined != query else query


