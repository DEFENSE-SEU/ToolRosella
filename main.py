# from LLM_Plan_withtext import get_search_plan
from LLM_Plan import get_search_plan
from RAG import GitHubRAG
import asyncio
from MCP import process_github_repos
from RepoCheck import GitHubRepoReader
from LLM_Action import LLMNoRepoOptimizer
import os
import json
import sys

def load_env_variables():
    """加载环境变量，优先从根目录.env文件读取"""
    env_file = './.env'
    if os.path.exists(env_file):
        print("Loading environment variables from .env file...")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            print("Used python-dotenv to load .env file (with override)")
        except ImportError:
            print("python-dotenv not found, using manual parsing...")
            # 手动解析.env文件
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 移除引号
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
                        print(f"Loaded {key} = {value[:10]}... from .env file")
    else:
        print("No .env file found, using terminal environment variables...")

# 加载环境变量
load_env_variables()

# import re
# import spacy
# nlp = spacy.load("en_core_web_sm")


# def generate_github_query(tool_text):
#     ...

queries = [
    "Please use aizynthfinder(https://github.com/MolecularAI/aizynthfinder) to fulfill this task: Help me to find available chemical reactions to compose 'O=C(OCC)C'."

           ]

for idx, query in enumerate(queries, 1):
    print(f"========== Query {idx} ==========")
    print(f"Query: {query}\n")

    
    token = os.getenv('GITHUB_TOKEN')
    rag = GitHubRAG()
    # 1) 缓存复用：若存在 ./repo_cache.json，逐个判定 README 是否可用
    cache_path = './repo_cache.json'
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                repo_cache = json.load(f)
            for repo_name, info in repo_cache.items():
                repo_url = info.get('url')
                if not repo_url:
                    continue
                # 克隆并读取 README，然后用严格规则判定
                readme = rag._clone_and_read_readme(repo_url + ('' if repo_url.endswith('.git') else ''), repo_name)
                if readme and rag.judge_repo_by_readme(query, readme):
                    name, clone_url = repo_name, repo_url
                    break
        except Exception:
            pass
    
    # 调试环境变量
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"DEBUG - OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
    if api_key:
        print(f"DEBUG - OPENAI_API_KEY value: {api_key[:10]}...{api_key[-4:]}")
    print(f"DEBUG - OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', 'NOT SET')}")
    print(f"DEBUG - Python executable: {sys.executable}")

    plan = get_search_plan(query, hinted_text="")
    print(f"DEBUG - Generated plan: {plan}")

    text_param = plan.get('text') or ""
    topics_param = plan.get('topics') or []
    print(f"DEBUG - Text parameter: '{text_param}'")
    print(f"DEBUG - Topics parameter: {topics_param}")

    name, clone_url = rag.search_and_judge(
        query=query,
        text=text_param,
        topics=topics_param,
        per_page=50,
    )

    if name and clone_url:
        print(f"Found repository: {name} -> {clone_url}")
        result = asyncio.run(process_github_repos(clone_url))
        print(f"Processed repos: {result['processed_names']}")

        # MCP + LLM 回答 Query

        # if token:
        #     repo_reader = GitHubRepoReader(clone_url, token)
        #     saved_file_path = repo_reader.process_repo()
        #     print(f"File saved to: {saved_file_path}")
        # if check_repo_processed and process_github_repos:
        #     if not check_repo_processed(clone_url):
        #         result = asyncio.run(process_github_repos(clone_url))
        #         print(f"Processed repos: {result['processed_names']}")
    else:
        print("No suitable repository found. Try refine query...")
        optimizer = LLMNoRepoOptimizer(rag)
        new_query = optimizer.refine_query(query, prev_topics=plan.get('topics') or [])
        print(f"Refined Query: {new_query}")
        # 使用原有流程以新的 query 再次搜索
        new_plan = get_search_plan(new_query, hinted_text="")
        name, clone_url = rag.search_and_judge(
            query=new_query,
            text=new_plan.get('text') or "",
            topics=new_plan.get('topics') or [],
            per_page=50,
        )
        if name and clone_url:
            print(f"[Refined] Found repository: {name} -> {clone_url}")
        
            # MCP + LLM 回答 Query
        
        else:
            name, clone_url = rag.search_and_judge_summary(
            query=new_query,
            text=new_plan.get('text') or "",
            topics=new_plan.get('topics') or [],
            per_page=50,
            )
            if name and clone_url:
                print(f"[Refined-Summary] Found repository: {name} -> {clone_url}")
            else:
                print("No suitable repository found after refining.")

    print("="*50 + "\n")
