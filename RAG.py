import requests
import json
import re
from typing import List, Dict, Tuple, Optional
from urllib.parse import quote
import os
import shutil
import git

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

class GitHubRAG:
    def __init__(self):
        self.api_keys = {
            'github_token': os.getenv('GITHUB_TOKEN', 'xxx')
        }

    def set_api_key(self, service: str, key: str, cx: str = None):
        if service in self.api_keys:
            self.api_keys[service] = key

    # 保留入口：如需纯文本查询直接返回仓库网页链接
    def search_github_repos(self, query: str, top_k: int = 5) -> List[str]:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.api_keys['github_token']:
            headers['Authorization'] = f"token {self.api_keys['github_token']}"
        url = f'https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc&per_page={top_k}'
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return [repo['html_url'] for repo in data.get('items', [])]
        except Exception:
            pass
        return []

    # 文本检索：返回 items（完整对象用于后续判定）
    def search_by_text(self, text: str, top_k: int = 50) -> List[Dict]:
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.api_keys['github_token']:
            headers['Authorization'] = f'token {self.api_keys["github_token"]}'
        url = f'https://api.github.com/search/repositories?q={quote(text)}&per_page={top_k}'
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json().get('items', [])
            return []
        except Exception:
            return []

    # 主题检索：按 topic 查询
    def search_by_topic(self, topic: str, top_k: int = 50) -> List[Dict]:
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.api_keys['github_token']:
            headers['Authorization'] = f'token {self.api_keys["github_token"]}'
        url = f'https://api.github.com/search/repositories?q=topic:{quote(topic)}&per_page={top_k}'
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json().get('items', [])
            return []
        except Exception:
            return []

    # 克隆并读取 README
    def _clone_and_read_readme(self, clone_url: str, repo_name: str) -> Optional[str]:
        dst = os.path.join('repos', repo_name)
        try:
            git.Repo.clone_from(clone_url, dst)
        except Exception:
            pass
        try:
            for f in os.listdir(dst):
                if 'readme' in f.lower():
                    with open(os.path.join(dst, f), 'r', encoding='utf-8', errors='ignore') as fh:
                        return fh.read()
            return None
        except Exception:
            return None
        finally:
            shutil.rmtree(dst, ignore_errors=True)


    from Repo_summary import GitHubRepositoryAnalyzer
    def judge_repo_by_Repo_summary(self, query: str, repo_url: str) -> Tuple[bool, str]:
        analyzer = self.GitHubRepositoryAnalyzer(repo_url)
        summary = analyzer.summarize_repository()
        if not summary:
            return False, "Failed to summarize repository."
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY', 'sk-af2e975fd0ef4245bbe404a137d49ade'),
            base_url=os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        )
        system_judge = (
        "You are a professional programmer. Given a user query and the summary of a GitHub repository, "
        "decide whether this repository is suitable to solve the query. "
        "Evaluation rules: "
        "1. The repository must be a downloadable, code-based project that can be set up and run locally with command line commands. "
        "   It cannot be just an API, SDK, or an online platform. "
        "2. The summary must explicitly include: environment setup or installation instructions, and command line commands showing how to run the program. "
        "3. The repository’s functionality must align with the requirements of the query. "
        "4. If any of the above criteria are not met, your judgment must be 'No'. "
        "Your response must strictly follow this format:\n\n"
        "Reason: <brief reason for your judgment>\n"
        "Judge: Yes/No"
        )

        content = f"Query:'''{query}'''\n\nSummary of the repository:'''{summary}'''"
        try:
            resp = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'deepseek-v3'),
                messages=[
                    {"role": "system", "content": system_judge},
                    {"role": "user", "content": content},
                ],
                temperature=0.5,
                max_tokens=2048,
            )
            print("API调用使用的模型:", resp.model)
            ans = resp.choices[0].message.content if resp.choices else ''
            import re as _re
            m = _re.findall(r"Judge:\s*(\w+)$", ans)
            ok = bool(m and m[0].lower() == 'yes')
            return ok, ans
        except Exception as e:
            return False, f"LLM error: {e}"
            content = f"Error: {e}"
            content = "Error: LLM request failed."
        return content

    def judge_repo_by_readme(self, query: str, readme: str) -> Tuple[bool, str]:
        if not OpenAI:
            text = (readme or '').lower()
            ok = ('install' in text or 'setup' in text) and ('usage' in text or 'run' in text)
            explanation = "Heuristic judgement (no LLM available)."
            return ok, explanation
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY', 'xxx'),
            base_url=os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        )
        # system_judge = (
        #     "You are a professional programmer. Given a query and the readme file of a github repository, your task is to assess whether this repository is suitable to solve this query. "
        #     "It must be runnable locally via command line and the readme must include environment setup and command-line usage instructions. Respond strictly with 'Judge: Yes' or 'Judge: No' at the end."
        # )

        system_judge = (
    "You are a professional programmer. Given a query and the readme file of a github repository, your task is to assess whether this repository is suitable to solve this query. "
    "You should evaluate whether the functionality of the repository aligns with the requirements of the query. "
    "Note that the repository shouldn't be a software or an online platform, it should be a program that can be downloaded to setup and run with command line commands. "
    "The readme must contain how to set up the environment and how to use it with command line commands. "
    "The repository should be code_based but not API_based. "
    "If the readme doesn't contain command line commands to run existing program(s) to use the functions of this repository to solve the query, your judge must be No. "
    "Your response should be structured as follows:\n\n"
    "Reason: <reason of your judgement>\n"
    "Judge: Yes/No"
)

        content = f"Query:'''{query}'''\n\nReadme of the repository:'''{(readme or '')[:15000]}...'''"
        try:
            resp = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'deepseek-v3'),
                messages=[
                    {"role": "system", "content": system_judge},
                    {"role": "user", "content": content},
                ],
                temperature=0.0,
                max_tokens=64,
            )
            ans = resp.choices[0].message.content if resp.choices else ''
            import re as _re
            m = _re.findall(r"Judge:\s*(\w+)$", ans)
            ok = bool(m and m[0].lower() == 'yes')
            return ok, ans
        except Exception as e:
            return False, f"LLM error: {e}"

    # 综合：若提供 text，先文本检索→判定；失败再按 topics 逐一检索→判定
    def search_and_judge(self, query: str, text: str = "", topics: List[str] = None, per_page: int = 50) -> Tuple[Optional[str], Optional[str]]:
        topics = topics or []
        print(f"Searching GitHub with text: '{text}' and topics: {topics}")
        # 文本优先
        if text:
            items = self.search_by_text(text, top_k=per_page)
            for repo in items:
                clone_url = repo.get('clone_url')
                name = repo.get('name')
                if not clone_url or not name:
                    continue
                readme = self._clone_and_read_readme(clone_url, name)
                if readme:
                    ok, ans = self.judge_repo_by_readme(query, readme)
                    print(f"LLM judgement for {name}: {ans}")
                    if ok:
                        return name, clone_url
        # 主题回退
        for topic in topics:
            items = self.search_by_topic(topic, top_k=per_page)
            for repo in items:
                clone_url = repo.get('clone_url')
                name = repo.get('name')
                if not clone_url or not name:
                    continue
                readme = self._clone_and_read_readme(clone_url, name)
                if readme:
                    ok, ans = self.judge_repo_by_readme(query, readme)
                    # ok, ans = self.judge_repo_by_Repo_summary(query, clone_url)
                    print(f"LLM judgement for {name}: {ans}")
                    if ok:
                        return name, clone_url
        return None, None
        
    def search_and_judge_summary(self, query: str, text: str = "", topics: List[str] = None, per_page: int = 50) -> Tuple[Optional[str], Optional[str]]:
        topics = topics or []
        print(f"Searching GitHub with text: '{text}' and topics: {topics}")
        # 文本优先
        if text:
            items = self.search_by_text(text, top_k=per_page)
            for repo in items:
                clone_url = repo.get('clone_url')
                name = repo.get('name')
                if not clone_url or not name:
                    continue
                readme = self._clone_and_read_readme(clone_url, name)
                if readme:
                    ok, ans = self.judge_repo_by_readme(query, readme)
                    print(f"LLM judgement for {name}: {ans}")
                    if ok:
                        return name, clone_url
        # 主题回退
        for topic in topics:
            items = self.search_by_topic(topic, top_k=per_page)
            for repo in items:
                clone_url = repo.get('clone_url')
                name = repo.get('name')
                if not clone_url or not name:
                    continue
                readme = self._clone_and_read_readme(clone_url, name)
                if readme:
                    # ok, ans = self.judge_repo_by_readme(query, readme)
                    ok, ans = self.judge_repo_by_Repo_summary(query, clone_url)
                    print(f"LLM judgement for {name}: {ans}")
                    if ok:
                        return name, clone_url
                
        return None, None

    def _is_github_repo_url(self, url: str) -> bool:
        pattern = r'https://github\.com/[^/]+/[^/]+/?'
        return bool(re.match(pattern, url))

    def _clean_github_url(self, url: str) -> str:
        if '/tree/' in url or '/blob/' in url or '/issues' in url or '/pulls' in url:
            parts = url.split('/')
            if len(parts) >= 5:
                return f"https://github.com/{parts[3]}/{parts[4]}"
        return url

def search_github_tools(tool_description: str, top_k: int = 5, api_keys: Dict = None) -> List[str]:
    del api_keys
    rag = GitHubRAG()
    return rag.search_github_repos(tool_description, top_k)
