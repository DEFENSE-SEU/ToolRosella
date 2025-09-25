from openai import OpenAI
import re
import os

class LLMPlanner:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        # self.model = "deepseek-r1"
        self.model = "gpt-4o"
        
        # self.system_prompt 
        # self.system_prompt = """You are an intelligent tool selector. ... """
        self.system_prompt = None

        # 用于从查询中抽取 topic 列表的提示
        self.topic_system_prompt = (
            "You are a professional programmer. Given a query, you want to find a github repository to solve this query. "
            "Firstly you need to search for the needed repository by their topics, which should be relevant to the query.\n\n"
            "The topic name should be a noun. IF it contains many words, the words should be connected by '-'. If the query has concluded a related topic, you should use it first.\n\n"
            "Your answer should be in format as follows:\n\n************\n"
            "topic1, topic2, topic3, ...\n************"
        )

# Instructions:
# 1. Analyze the user query carefully
# 2. Think about what kind of tool, method, or approach would be most helpful
# 3. Provide a brief description of the needed tool/capability
# 4. You MUST end your response with EXACTLY this format: <Tool>your_tool_description</Tool>
# 5. Do not use any other format or tags - only <Tool></Tool>

# Examples:
# Query: "Calculate the area of a circle with radius 5"  
# Response: This requires mathematical calculation to compute the area using the formula πr². <Tool>mathematical_calculation</Tool>

    # def select_tool(self, query: str, max_retries: int = 3) -> tuple:
    #     ...

    def _validate_format(self, response: str) -> bool:
        pattern = r'<Tool>(.*?)</Tool>'
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return False
        
        tool_content = match.group(1).strip()
        
        if not tool_content:
            return False
        
        return True

    def _extract_tool_selection(self, response: str) -> str:
        pattern = r'<Tool>(.*?)</Tool>'
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            return "ERROR"

    # def plan_with_query(self, query: str) -> str:
    #     ...

    # 生成 topics
    def generate_topics(self, query: str) -> list:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.topic_system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.5,
                max_tokens=256,
            )
            content = resp.choices[0].message.content if resp.choices else ""
            # 输出主题生成的原始文本，便于调试与复现
            try:
                print(f"LLM topics raw: {content}")
            except Exception:
                pass
            # 兼容两种格式：************ 包裹或直接逗号分隔
            import re as _re
            try:
                topics_str = _re.findall(r"\*\n(.+?)\n\*", content)[0]
            except Exception:
                topics_str = content
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]
            return topics
        except Exception:
            return []

    # 文本优先，失败回退到主题检索。返回 dict，指示使用的策略与参数
    def decide_search_plan(self, query: str, hinted_text: str = "") -> dict:
        # OpenAct：当未复用缓存时，走“找新仓库”并允许 text/topics。此处仅保留 topics 路径（文本优先策略由外层自行控制）。
        plan = {"strategy": "topics", "text": None, "topics": []}
        plan["topics"] = self.generate_topics(query)
        return plan


 # def get_tool_selection(query: str) -> str:
 #     planner = LLMPlanner()
 #     return planner.plan_with_query(query)

# 为上层调用暴露：生成主题与策略
def get_search_plan(query: str, hinted_text: str = "") -> dict:
    planner = LLMPlanner()
    return planner.decide_search_plan(query, hinted_text)
