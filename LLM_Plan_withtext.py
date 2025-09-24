from openai import OpenAI
import re

class LLMPlanner:
    def __init__(self):
        self.client = OpenAI(
            api_key="xxx",  
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "deepseek-v3"
        
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

        # 生成用于“text 检索”的简单提示：若可用，返回一个单词；否则返回 NONE
        self.text_hint_prompt = (
            "You are helping to find a GitHub repository by text matching. "
            "Given the user query, if you can derive a SINGLE WORD most suitable for GitHub text search (e.g., repo name or key term), output that word. "
            "If you cannot, output EXACTLY 'NONE'. Return ONLY the word with no explanation."
        )

        # 模拟 OpenAct gpt4_functions 的函数调用规范：输出 JSON {"name":..., "arguments":{...}}
        self.dispatcher_instruction = (
            "You will be provided the functions that you can use to solve the problem. "
            "Your answer MUST be a function call JSON with the function name and the arguments, in the exact format: \n\n"
            "{\n  \"name\": \"function_name\",\n  \"arguments\": {\n    \"argument1\": \"value1\",\n    \"argument2\": \"value2\"\n  }\n}\n\n"
        )
        self.functions_spec_text = (
            "Function 0:\n" 
            "Function Name: use_existing_repository\n"
            "Function Description: If an existed repository can solve your problem, you can use this function to use it\n"
            "Argument: thought\nArgument Type: string\nArgument Description: Internal reasoning\n"
            "Argument: repo_name\nArgument Type: string\nArgument Description: name of the repository\n\n"
            "Function 1:\n"
            "Function Name: find_a_new_repository\n"
            "Function Description: If existed repositories cannot solve your problem, find a new tool\n"
            "Argument: thought\nArgument Type: string\nArgument Description: Internal reasoning\n"
            "Argument: text\nArgument Type: string\nArgument Description: single word for text search (optional)\n"
            "Argument: topics\nArgument Type: string\nArgument Description: topics separated by ', ' (optional)\n"
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

    # 生成一个 text 提示词（单词），若无法生成则返回空字符串
    def generate_text_hint(self, query: str) -> str:
        # 1) 直接从 URL 中提取 repo 名称（若存在）
        import re as _re
        m = _re.search(r"github\.com/[^/]+/([A-Za-z0-9_.-]+)", query)
        print("m = ", m)
        if m:
            return m.group(1)
        # 2) 调用 LLM 生成单词，否则 NONE
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.text_hint_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.5,
                max_tokens=8,
            )
            content = resp.choices[0].message.content.strip() if resp.choices else ""
            print("content = ", content)
            try:
                print(f"LLM text hint raw: {content}")
            except Exception:
                pass
            return "" if content.upper() == "NONE" else content.split()[0]
        except Exception:
            return ""

    def decide_repo_action(self, query: str, cache: dict) -> dict:
        content = "Query: " + query
        if cache and any(("description" in repo and repo["description"] is not None) for repo in cache.values()):
            sys_prompt = (
                "You are a professional programmer. Given a task, you want to find a github repository to solve the task. \n"
                + self.dispatcher_instruction
            )
            # 列出可选仓库
            for repo_name, repo in cache.items():
                if "description" in repo and repo["description"] is not None:
                    content += ("\nRepository's name: " + repo_name + "\nDescription: " + repo["description"] + "\n\n")
            func_text = self.functions_spec_text
        else:
            sys_prompt = (
                "You are a professional programmer. Given a task, you want to find a github repository to solve the task. \n"
                + self.dispatcher_instruction
            )
            # 找新仓库：允许 text 与 topics
            # 这里不提前注入 topics/text，由模型自行决定；我们仍会作为备用生成
            func_text = self.functions_spec_text
        # 让模型输出函数调用 JSON
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content + "\n\n" + func_text},
        ]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=256,
            )
            raw = resp.choices[0].message.content if resp.choices else ""
            try:
                print(f"LLM dispatcher raw: {raw}")
            except Exception:
                pass
            import json as _json, re as _re
            match = _re.search(r"\{[\s\S]*\}$", raw.strip())
            text = match.group(0) if match else raw
            func_call = _json.loads(text)
            return func_call
        except Exception as e:
            return {"name": "find_a_new_repository", "arguments": _json.dumps({"thought": f"fallback due to error: {e}"})}

    # 文本优先，失败回退到主题检索。返回 dict，指示使用的策略与参数
    def decide_search_plan(self, query: str, hinted_text: str = "") -> dict:
        # OpenAct：找新仓库允许 text 或 topics，这里同时尝试，两者并存时先 text 后 topics
        plan = {"strategy": "topics", "text": None, "topics": []}
        # 文本提示优先：若外层已给 hinted_text，则直接用；否则尝试自动生成
        print("hinted_text = ", hinted_text)
        text_hint = hinted_text.strip() if hinted_text else self.generate_text_hint(query)
        if text_hint:
            plan["text"] = text_hint
            plan["strategy"] = "text_then_topics"
        plan["topics"] = self.generate_topics(query)
        return plan


 # def get_tool_selection(query: str) -> str:
 #     planner = LLMPlanner()
 #     return planner.plan_with_query(query)

# 为上层调用暴露：生成主题与策略
def get_search_plan(query: str, hinted_text: str = "") -> dict:
    planner = LLMPlanner()
    return planner.decide_search_plan(query, hinted_text)

def decide_repo_action(query: str, cache: dict) -> dict:
    planner = LLMPlanner()
    return planner.decide_repo_action(query, cache)
