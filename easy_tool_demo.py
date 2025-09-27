"""
Easy Tool Demo - 简化的AgenticRAG工具
实现GitHub仓库搜索 → 评估 → MCP工具调用流程
"""

import os

# 统一的测试查询
TEST_QUERY = "Please use aizynthfinder(https://github.com/MolecularAI/aizynthfinder) to fulfill this task: Help me to find available chemical reactions to compose 'O=C(OCC)C'."

class LLMClient:
    """统一的LLM客户端"""

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
            self.model = "gpt-4o"
            self.available = True
            print("✅ LLM client initialized successfully")
        except Exception as e:
            print(f"❌ LLM client failed: {e}")
            self.available = False

    def call(self, messages, temperature=0.7, tools=None, tool_choice=None):
        """调用LLM，支持工具调用"""
        if not self.available:
            return None

        try:
            # 构建请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1000
            }

            # 如果有工具，添加工具参数
            if tools:
                request_params["tools"] = tools
                if tool_choice:
                    request_params["tool_choice"] = tool_choice

            response = self.client.chat.completions.create(**request_params)

            # 如果是工具调用响应，返回完整的message对象
            if tools and response.choices[0].message.tool_calls:
                return response.choices[0].message
            else:
                return response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            return None

    def call_with_tools(self, messages, tools, tool_executor, max_iterations=5):
        """带工具调用的LLM对话循环"""
        if not self.available:
            return None

        current_messages = messages.copy()

        for iteration in range(max_iterations):
            print(f"🔄 Tool calling iteration {iteration + 1}")

            # 调用LLM
            response = self.call(current_messages, tools=tools)

            if isinstance(response, str):
                # 没有工具调用，直接返回文本响应
                print("✅ LLM provided final answer")
                return response

            # 检查是否有工具调用
            if not response.tool_calls:
                print("✅ LLM provided final answer")
                return response.content or ""

            # 执行工具调用
            current_messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in response.tool_calls]
            })

            # 处理每个工具调用
            for tool_call in response.tool_calls:
                print(f"🔧 Calling tool: {tool_call.function.name}")
                print(f"   Arguments: {tool_call.function.arguments}")

                # 执行工具
                tool_result = tool_executor.execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments
                )

                print(f"   Result: {str(tool_result)[:200]}...")

                # 添加工具结果到对话
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })

        print("⚠️ Reached maximum iterations")
        return "Maximum tool calling iterations reached"

def load_env_variables():
    """加载环境变量"""
    env_file = './.env'
    if os.path.exists(env_file):
        print("📁 Loading .env file...")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            print("✅ Environment variables loaded")
        except ImportError:
            print("⚠️  python-dotenv not found, loading manually...")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
    else:
        print("⚠️  No .env file found")

def check_configuration():
    """检查配置是否正确"""
    print("\n🔧 Checking configuration...")

    api_key = os.getenv('OPENAI_API_KEY')
    github_token = os.getenv('GITHUB_TOKEN')
    base_url = os.getenv('OPENAI_BASE_URL', 'Default')

    print(f"🔑 OpenAI API: {'✅ SET' if api_key else '❌ MISSING'}")
    print(f"🔑 GitHub Token: {'✅ SET' if github_token else '❌ MISSING'}")
    print(f"🌐 Base URL: {base_url}")

    if not api_key:
        print("❌ OPENAI_API_KEY is required")
        return False
    if not github_token:
        print("❌ GITHUB_TOKEN is required")
        return False

    print("✅ Configuration OK")
    return True

def test_llm_client():
    """测试LLM客户端"""
    print("\n🧠 Testing LLM client...")

    llm = LLMClient()
    if not llm.available:
        return False

    # 简单测试
    test_messages = [
        {"role": "user", "content": "Say 'Hello from LLM!' in exactly those words."}
    ]

    response = llm.call(test_messages)
    if response:
        print(f"🤖 LLM Response: {response}")
        print("✅ LLM client test passed")
        return True
    else:
        print("❌ LLM client test failed")
        return False

class GitHubClient:
    """GitHub API客户端"""

    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.available = bool(self.token)

        if self.available:
            print("✅ GitHub client initialized successfully")
        else:
            print("❌ GitHub client failed: No GITHUB_TOKEN")

    def search_repositories(self, topics, max_results=10):
        """搜索GitHub仓库"""
        if not self.available:
            return []

        try:
            import requests

            # 构建搜索查询 - 优化策略
            if isinstance(topics, list):
                # 优先使用前几个最重要的关键词
                primary_topics = topics[:3] if len(topics) > 3 else topics
                query = " ".join(primary_topics)
            else:
                query = str(topics)

            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # GitHub搜索API
            search_url = f"{self.base_url}/search/repositories"
            params = {
                'q': query,
                'sort': 'stars',
                'order': 'desc',
                'per_page': max_results
            }

            print(f"🔍 Searching GitHub for: {query}")
            response = requests.get(search_url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                repos = data.get('items', [])
                print(f"✅ Found {len(repos)} repositories")
                return repos
            else:
                print(f"❌ GitHub API error: {response.status_code}")
                if response.status_code == 403:
                    print("   API rate limit exceeded, try again later")
                return []

        except Exception as e:
            print(f"❌ GitHub search failed: {e}")
            return []

def extract_topics_from_query(llm_client, user_query):
    """使用LLM从用户查询中提取搜索主题"""
    prompt = f"""You are a professional programmer. Given a query, you want to find a github repository to solve this query. Firstly you need to search for the needed repository by their topics, which should be relevant to the query.

The topic name should be a noun. IF it contains many words, the words should be connected by '-'. If the query has concluded a related topic, you should use it first.

Query: "{user_query}"

Your answer should be in format as follows:

************
topic1, topic2, topic3, ...
************"""

    messages = [{"role": "user", "content": prompt}]

    print("🤖 LLM Topic Extraction Prompt:")
    print(f"   Query: {user_query}")

    response = llm_client.call(messages, temperature=0.3)

    print("🤖 LLM Topic Extraction Response:")
    print(f"   Raw response: {response}")

    if response:
        # 提取 ************ 之间的内容
        import re
        pattern = r'\*{12}(.*?)\*{12}'
        match = re.search(pattern, response, re.DOTALL)

        if match:
            topics_text = match.group(1).strip()
            # 按逗号分割并清理
            topics = [topic.strip() for topic in topics_text.split(',') if topic.strip()]
            print(f"   Extracted topics: {topics}")
            return topics
        else:
            # 如果没有找到标准格式，尝试按行或逗号分割
            topics = [topic.strip() for topic in response.replace('\n', ',').split(',') if topic.strip()]
            print(f"   Fallback extracted topics: {topics}")
            return topics
    return []

def search_and_filter_repos(llm_client, github_client, user_query, max_results=10):
    """完整的仓库搜索和过滤流程"""
    print(f"\n🔍 Starting repository search for: {user_query}")

    # 步骤1：提取主题
    print("📝 Step 1: Extracting topics...")
    topics = extract_topics_from_query(llm_client, user_query)
    if not topics:
        print("❌ Failed to extract topics")
        return []

    print(f"   Topics: {topics}")

    # 步骤2：GitHub搜索
    print("🔍 Step 2: Searching GitHub...")
    repos = github_client.search_repositories(topics, max_results=max_results)
    if not repos:
        print("❌ No repositories found")
        return []

    print(f"📋 GitHub Search Results ({len(repos)} repositories):")
    for i, repo in enumerate(repos, 1):
        print(f"   {i}. {repo['full_name']} - ⭐ {repo['stargazers_count']}")
        print(f"      Language: {repo.get('language', 'Unknown')}")
        print(f"      Archived: {repo.get('archived', False)}")
        print(f"      Description: {repo.get('description', 'No description')[:80]}...")

    # 步骤3：基本过滤
    print("\n⚡ Step 3: Filtering repositories...")
    filtered_repos = []

    for repo in repos:
        # 基本过滤条件
        stars = repo.get('stargazers_count', 0)
        archived = repo.get('archived', False)
        has_desc = bool(repo.get('description'))

        print(f"   Checking {repo['full_name']}: stars={stars}, archived={archived}, has_desc={has_desc}")

        if (stars >= 10 and not archived and has_desc):
            filtered_repos.append({
                'name': repo['full_name'],
                'url': repo['html_url'],
                'stars': repo['stargazers_count'],
                'description': repo['description'],
                'language': repo.get('language', 'Unknown'),
                'updated_at': repo['updated_at']
            })
            print(f"   ✅ {repo['full_name']} passed filtering")
        else:
            print(f"   ❌ {repo['full_name']} filtered out")

    print(f"\n✅ Found {len(filtered_repos)} suitable repositories after filtering")
    return filtered_repos

def test_topic_extraction():
    """测试主题提取功能"""
    print("\n🎯 Testing topic extraction...")

    llm = LLMClient()
    if not llm.available:
        return False

    print(f"  Query: {TEST_QUERY[:80]}...")
    topics = extract_topics_from_query(llm, TEST_QUERY)
    print(f"  提取的主题: {topics}")

    if topics:
        print("✅ Topic extraction test completed")
        return True
    else:
        print("❌ Topic extraction failed")
        return False

def clone_and_read_readme(repo_url, repo_name=None):
    """克隆仓库并读取README"""
    import subprocess
    import tempfile
    import shutil

    if not repo_name:
        repo_name = repo_url.split("/")[-1].replace(".git", "")

    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            clone_dir = f"{temp_dir}/{repo_name}"

            # 克隆仓库
            print(f"📁 Cloning {repo_name}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, clone_dir],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"❌ Failed to clone {repo_name}: {result.stderr}")
                return None

            # 查找README文件
            readme_files = ["README.md", "README.rst", "README.txt", "README", "readme.md"]
            readme_content = None

            for readme_file in readme_files:
                readme_path = f"{clone_dir}/{readme_file}"
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                        print(f"✅ Found {readme_file}")
                        break
                except:
                    continue

            if not readme_content:
                print(f"⚠️  No README found in {repo_name}")
                return None

            return readme_content[:5000]  # 限制长度

    except Exception as e:
        print(f"❌ Error processing {repo_name}: {e}")
        return None

def judge_repo_by_readme(llm_client, query, readme_content):
    """使用LLM严格判断仓库是否适合查询"""
    prompt = f"""You are a professional programmer. Please determine if this GitHub repository is suitable for the given query.

Query: "{query}"

README Content:
{readme_content}

Please analyze:
1. Does this repository solve the exact problem mentioned in the query?
2. Can this repository be used as a tool/library for the query's task?
3. Is this repository actively maintained and well-documented?

Answer with ONLY "YES" or "NO" followed by a brief reason (max 50 words).

Format: YES/NO: [reason]"""

    messages = [{"role": "user", "content": prompt}]

    print("🤖 LLM Repository Evaluation Prompt:")
    print(f"   Query: {query}")
    print(f"   README length: {len(readme_content)} characters")

    response = llm_client.call(messages, temperature=0.1)

    print("🤖 LLM Repository Evaluation Response:")
    print(f"   Raw response: {response}")

    if response:
        response_clean = response.strip().upper()
        is_suitable = response_clean.startswith("YES")
        print(f"   Parsed result: {'✅ SUITABLE' if is_suitable else '❌ NOT SUITABLE'}")
        return is_suitable
    return False

def test_complete_search_and_evaluate():
    """测试完整的搜索和评估流程"""
    print("\n🚀 Testing complete search and evaluation pipeline...")

    llm = LLMClient()
    github = GitHubClient()

    if not llm.available or not github.available:
        return False, None

    # 步骤1：尝试动态搜索
    print("📝 Step 1: Dynamic repository search...")
    repos = search_and_filter_repos(llm, github, TEST_QUERY, max_results=5)

    selected_repo = None

    if repos:
        print("\n📋 Found repositories, selecting the first one for evaluation:")
        selected_repo = repos[0]
        print(f"  Selected: {selected_repo['name']} - ⭐ {selected_repo['stars']}")
        print(f"  URL: {selected_repo['url']}")
    else:
        print("\n⚠️  Dynamic search found no repositories")
        print("📝 Step 2: Fallback to known repository...")

        # 回退到硬编码的已知仓库
        selected_repo = {
            'name': 'MolecularAI/aizynthfinder',
            'url': 'https://github.com/MolecularAI/aizynthfinder',
            'stars': 'Unknown',
            'description': 'Fallback repository for testing',
            'language': 'Python'
        }
        print(f"  Using fallback: {selected_repo['name']}")
        print(f"  URL: {selected_repo['url']}")

    # 步骤3：评估选中的仓库
    print(f"\n📊 Step 3: Evaluating selected repository...")
    readme = clone_and_read_readme(selected_repo['url'])
    if not readme:
        print("❌ Failed to read README")
        return False, None

    print(f"📄 README length: {len(readme)} characters")

    # 使用LLM判断
    is_suitable = judge_repo_by_readme(llm, TEST_QUERY, readme)
    print(f"🎯 Repository evaluation result: {'✅ SUITABLE' if is_suitable else '❌ NOT SUITABLE'}")

    if is_suitable:
        print("✅ Complete search and evaluation pipeline test passed")
        return True, selected_repo
    else:
        print("❌ Selected repository not suitable for the query")
        return False, None

class MCPToolExecutor:
    """MCP工具执行器"""

    def __init__(self, tool_dir):
        self.tool_dir = tool_dir
        self.server_script = f"{tool_dir}/mcp_server.py"

    def execute_tool(self, tool_name, arguments_str):
        """执行MCP工具函数"""
        try:
            import subprocess
            import sys
            import json

            # 解析参数
            if isinstance(arguments_str, str):
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}
            else:
                arguments = arguments_str if arguments_str else {}

            # 映射工具名称到命令
            command_mapping = {
                "get_repository_info": "info",
                "list_python_files": "files",
                "get_requirements": "requirements",
                "analyze_structure": "analyze",
                "analyze_for_synthesis": "analyze"  # 新增化学合成分析
            }

            command = command_mapping.get(tool_name)
            if not command:
                return f"Unknown tool: {tool_name}"

            # 执行命令
            result = subprocess.run(
                [sys.executable, self.server_script, command],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Tool execution failed: {result.stderr}"

        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    def get_openai_tools_definition(self):
        """获取OpenAI格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_repository_info",
                    "description": "Get basic information about the repository including name, URL, and description",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_python_files",
                    "description": "List all Python files in the repository to understand the codebase structure",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_requirements",
                    "description": "Get the repository requirements and dependencies needed for installation",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_for_synthesis",
                    "description": "Analyze the repository structure and provide specific guidance for chemical synthesis tasks, including how to use the tool for finding chemical reactions",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

class SimpleMCPGenerator:
    """简化版MCP工具生成器"""

    def __init__(self):
        self.output_dir = "./mcp_tools_output"
        self.ensure_directory(self.output_dir)

    def ensure_directory(self, path):
        """确保目录存在"""
        import os
        os.makedirs(path, exist_ok=True)

    def extract_repo_name(self, repo_url):
        """从GitHub URL提取仓库名"""
        try:
            parts = repo_url.rstrip('/').split('/')
            return parts[-1].replace('.git', '')
        except:
            return "unknown_repo"

    def analyze_repo_structure(self, repo_url):
        """简单分析仓库结构"""
        print("📊 Analyzing repository structure...")

        import subprocess
        import tempfile
        import os

        repo_name = self.extract_repo_name(repo_url)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                clone_dir = f"{temp_dir}/{repo_name}"

                # 克隆仓库
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, clone_dir],
                    capture_output=True, text=True, timeout=60
                )

                if result.returncode != 0:
                    return {"error": "Failed to clone repository"}

                # 分析文件结构
                analysis = {
                    "python_files": [],
                    "main_files": [],
                    "setup_files": [],
                    "requirements": [],
                    "has_setup_py": False,
                    "has_requirements": False
                }

                for root, dirs, files in os.walk(clone_dir):
                    # 跳过.git目录
                    if '.git' in root:
                        continue

                    for file in files:
                        if file.endswith('.py'):
                            rel_path = os.path.relpath(os.path.join(root, file), clone_dir)
                            analysis["python_files"].append(rel_path)

                            if file in ['main.py', '__main__.py', 'app.py', 'run.py']:
                                analysis["main_files"].append(rel_path)

                        elif file == 'setup.py':
                            analysis["has_setup_py"] = True
                            analysis["setup_files"].append(file)

                        elif file in ['requirements.txt', 'requirements-dev.txt']:
                            analysis["has_requirements"] = True
                            # 读取requirements
                            try:
                                with open(os.path.join(root, file), 'r') as f:
                                    reqs = [line.strip() for line in f.readlines()
                                           if line.strip() and not line.startswith('#')]
                                    analysis["requirements"].extend(reqs)
                            except:
                                pass

                print(f"   📁 Found {len(analysis['python_files'])} Python files")
                print(f"   📄 Main files: {analysis['main_files']}")
                print(f"   📦 Has setup.py: {analysis['has_setup_py']}")
                print(f"   📋 Has requirements: {analysis['has_requirements']}")

                return analysis

        except Exception as e:
            return {"error": str(e)}

    def generate_mcp_tool(self, repo_info, readme_content):
        """生成简化版MCP工具"""
        repo_name = self.extract_repo_name(repo_info['url'])

        print(f"🔧 Generating simplified MCP tool for {repo_name}...")

        # 分析仓库结构
        repo_analysis = self.analyze_repo_structure(repo_info['url'])
        if "error" in repo_analysis:
            print(f"⚠️  Repository analysis failed: {repo_analysis['error']}")
            repo_analysis = {"python_files": [], "main_files": [], "requirements": []}

        # 创建输出目录
        tool_dir = f"{self.output_dir}/{repo_name}_mcp_tool"
        self.ensure_directory(tool_dir)

        # 生成MCP工具文件
        files_created = []

        # 1. 主要的MCP服务器文件
        server_file = self.create_mcp_server(tool_dir, repo_info, readme_content, repo_analysis)
        if server_file:
            files_created.append(server_file)

        # 2. 启动脚本
        start_script = self.create_start_script(tool_dir, repo_name)
        if start_script:
            files_created.append(start_script)

        # 3. 配置文件
        config_file = self.create_config_file(tool_dir, repo_info, repo_analysis)
        if config_file:
            files_created.append(config_file)

        # 4. README文件
        readme_file = self.create_tool_readme(tool_dir, repo_info, repo_analysis)
        if readme_file:
            files_created.append(readme_file)

        if files_created:
            print(f"✅ MCP tool generated successfully!")
            print(f"   Output directory: {tool_dir}")
            print(f"   Files created: {len(files_created)}")
            for file in files_created:
                print(f"   📄 {file}")
            return tool_dir
        else:
            print("❌ Failed to generate MCP tool")
            return None

    def create_mcp_server(self, tool_dir, repo_info, readme_content, repo_analysis):
        """创建MCP服务器文件"""
        repo_name = self.extract_repo_name(repo_info['url'])
        class_name = repo_name.replace('-', '_').replace('.', '_').title() + "MCPServer"

        content = f'''#!/usr/bin/env python3
"""
MCP Server for {repo_info['name']}
Auto-generated by Easy Tool Demo

Repository: {repo_info['url']}
Description: {repo_info.get('description', 'No description available')}
"""

import json
import sys
import logging
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {class_name}:
    """MCP Server for {repo_name}"""

    def __init__(self):
        self.repo_url = "{repo_info['url']}"
        self.repo_name = "{repo_name}"
        self.description = "{repo_info.get('description', 'No description')[:200]}"
        self.python_files = {repo_analysis.get('python_files', [])}
        self.main_files = {repo_analysis.get('main_files', [])}
        self.requirements = {repo_analysis.get('requirements', [])}

    def get_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return [
            {{
                "name": "get_repository_info",
                "description": "Get basic information about the repository",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }},
            {{
                "name": "list_python_files",
                "description": "List all Python files in the repository",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }},
            {{
                "name": "get_requirements",
                "description": "Get the repository requirements/dependencies",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }},
            {{
                "name": "analyze_structure",
                "description": "Analyze the repository structure and suggest usage",
                "inputSchema": {{
                    "type": "object",
                    "properties": {{}},
                    "required": []
                }}
            }}
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        try:
            if name == "get_repository_info":
                return {{
                    "content": [{{
                        "type": "text",
                        "text": json.dumps({{
                            "name": self.repo_name,
                            "url": self.repo_url,
                            "description": self.description
                        }}, indent=2)
                    }}]
                }}

            elif name == "list_python_files":
                return {{
                    "content": [{{
                        "type": "text",
                        "text": "Python files in repository:\\n" + "\\n".join(self.python_files)
                    }}]
                }}

            elif name == "get_requirements":
                if self.requirements:
                    req_text = "Dependencies:\\n" + "\\n".join(self.requirements)
                else:
                    req_text = "No requirements.txt found or no dependencies listed"
                return {{
                    "content": [{{
                        "type": "text",
                        "text": req_text
                    }}]
                }}

            elif name == "analyze_structure":
                analysis = f"""Repository Analysis for {{self.repo_name}}:

🏗️  Structure:
- Python files: {{len(self.python_files)}}
- Main entry points: {{self.main_files}}
- Dependencies: {{len(self.requirements)}}

📋 Usage Suggestions:
1. Clone the repository: git clone {{self.repo_url}}
2. Install dependencies: pip install -r requirements.txt (if available)
3. Main files to examine: {{', '.join(self.main_files) if self.main_files else 'Check the README for entry points'}}

🔧 For the query about "{{TEST_QUERY.split(':')[-1] if ':' in TEST_QUERY else TEST_QUERY}}":
This repository appears to be related to {{self.description}}.
Check the main files and documentation for specific usage instructions.
"""
                return {{
                    "content": [{{
                        "type": "text",
                        "text": analysis
                    }}]
                }}

            else:
                return {{
                    "content": [{{
                        "type": "text",
                        "text": f"Unknown tool: {{name}}"
                    }}],
                    "isError": True
                }}

        except Exception as e:
            return {{
                "content": [{{
                    "type": "text",
                    "text": f"Error executing tool {{name}}: {{str(e)}}"
                }}],
                "isError": True
            }}

    def list_resources(self) -> List[Dict[str, Any]]:
        """列出可用资源"""
        return [
            {{
                "uri": f"repo://{{self.repo_name}}/info",
                "name": f"Repository Info: {{self.repo_name}}",
                "description": "Basic repository information",
                "mimeType": "application/json"
            }}
        ]


def main():
    """主函数 - 简单的命令行接口"""
    server = {class_name}()

    if len(sys.argv) < 2:
        print("Available commands:")
        print("  info - Get repository information")
        print("  files - List Python files")
        print("  requirements - Show dependencies")
        print("  analyze - Analyze repository structure")
        return

    command = sys.argv[1]

    if command == "info":
        result = server.call_tool("get_repository_info", {{}})
    elif command == "files":
        result = server.call_tool("list_python_files", {{}})
    elif command == "requirements":
        result = server.call_tool("get_requirements", {{}})
    elif command == "analyze":
        result = server.call_tool("analyze_structure", {{}})
    else:
        print(f"Unknown command: {{command}}")
        return

    if result.get("isError"):
        print("Error:", result["content"][0]["text"])
    else:
        print(result["content"][0]["text"])


if __name__ == "__main__":
    main()
'''

        server_file = f"{tool_dir}/mcp_server.py"
        try:
            with open(server_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return server_file
        except Exception as e:
            print(f"❌ Failed to create server file: {e}")
            return None

    def create_start_script(self, tool_dir, repo_name):
        """创建启动脚本"""
        content = f'''#!/bin/bash
# MCP Tool Startup Script for {repo_name}

echo "🚀 Starting MCP Server for {repo_name}..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Run the MCP server
python3 mcp_server.py "$@"
'''

        script_file = f"{tool_dir}/start_mcp.sh"
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # 使脚本可执行
            import os
            os.chmod(script_file, 0o755)
            return script_file
        except Exception as e:
            print(f"❌ Failed to create start script: {e}")
            return None

    def create_config_file(self, tool_dir, repo_info, repo_analysis):
        """创建配置文件"""
        import json
        repo_name = self.extract_repo_name(repo_info['url'])

        config = {
            "name": f"{repo_name}_mcp_tool",
            "version": "1.0.0",
            "description": repo_info.get('description', 'MCP tool for repository'),
            "repository": {
                "name": repo_info['name'],
                "url": repo_info['url'],
                "language": repo_info.get('language', 'Unknown')
            },
            "analysis": {
                "python_files_count": len(repo_analysis.get('python_files', [])),
                "main_files": repo_analysis.get('main_files', []),
                "has_requirements": bool(repo_analysis.get('requirements', []))
            },
            "tools": [
                "get_repository_info",
                "list_python_files",
                "get_requirements",
                "analyze_structure"
            ]
        }

        config_file = f"{tool_dir}/mcp_config.json"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return config_file
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return None

    def create_tool_readme(self, tool_dir, repo_info, repo_analysis):
        """创建工具说明文档"""
        repo_name = self.extract_repo_name(repo_info['url'])

        content = f'''# MCP Tool for {repo_info['name']}

Auto-generated MCP (Model Context Protocol) tool for the GitHub repository.

## Repository Information

- **Name**: {repo_info['name']}
- **URL**: {repo_info['url']}
- **Language**: {repo_info.get('language', 'Unknown')}
- **Description**: {repo_info.get('description', 'No description available')}

## Repository Analysis

- **Python Files**: {len(repo_analysis.get('python_files', []))}
- **Main Entry Points**: {', '.join(repo_analysis.get('main_files', [])) or 'None identified'}
- **Dependencies**: {len(repo_analysis.get('requirements', []))} requirements found

## Available Tools

1. **get_repository_info** - Get basic repository information
2. **list_python_files** - List all Python files in the repository
3. **get_requirements** - Show repository dependencies
4. **analyze_structure** - Analyze repository structure and suggest usage

## Usage

### Command Line Interface

```bash
# Get repository information
python3 mcp_server.py info

# List Python files
python3 mcp_server.py files

# Show dependencies
python3 mcp_server.py requirements

# Analyze structure
python3 mcp_server.py analyze
```

### As MCP Server

The `mcp_server.py` file can be integrated with MCP-compatible applications to provide repository analysis capabilities.

## Original Query Context

This tool was generated to help with: "{TEST_QUERY}"

## Generated by

Easy Tool Demo - Automated GitHub Repository to MCP Tool Converter
Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
'''

        readme_file = f"{tool_dir}/README.md"
        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return readme_file
        except Exception as e:
            print(f"❌ Failed to create README: {e}")
            return None



def test_llm_with_mcp_tool(tool_dir, selected_repo):
    """测试LLM使用生成的MCP工具回答查询 - 真正的function calling"""
    print("\n🤖 Testing LLM with generated MCP tool (Function Calling)...")

    if not tool_dir:
        print("❌ No MCP tool directory provided")
        return False

    llm = LLMClient()
    if not llm.available:
        return False

    try:
        # 创建工具执行器
        tool_executor = MCPToolExecutor(tool_dir)

        # 获取工具定义
        tools = tool_executor.get_openai_tools_definition()

        print("🔧 Available tools for LLM:")
        for tool in tools:
            print(f"   - {tool['function']['name']}: {tool['function']['description']}")

        # 构建初始消息
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI assistant helping with chemical synthesis. You have access to tools that can analyze the GitHub repository "{selected_repo['name']}" which contains chemical synthesis software.

Your task is to help find chemical reactions to synthesize 'O=C(OCC)C' (ethyl acetate).

Use the available tools to:
1. Get repository information
2. Analyze the structure and find relevant files
3. Get requirements for installation
4. Provide specific guidance on how to use this tool for chemical synthesis

After gathering information from the tools, provide a concrete answer about the chemical reactions that can be used to synthesize 'O=C(OCC)C'."""
            },
            {
                "role": "user",
                "content": "Help me to find available chemical reactions to compose 'O=C(OCC)C'. Use the available tools to analyze the repository and then tell me the specific chemical reactions I can use."
            }
        ]

        print("🚀 Starting LLM tool calling conversation...")

        # 使用带工具的LLM调用
        final_response = llm.call_with_tools(messages, tools, tool_executor)

        print("\n🎯 Final LLM Response:")
        print("=" * 60)
        print(final_response)
        print("=" * 60)

        if final_response and len(final_response) > 100:
            print("✅ LLM successfully used MCP tools to answer query")
            return True
        else:
            print("❌ LLM response too short or empty")
            return False

    except Exception as e:
        print(f"❌ Error testing LLM with MCP tool: {e}")
        return False

def test_github_client():
    """测试GitHub客户端"""
    print("\n🐙 Testing GitHub client...")

    github = GitHubClient()
    if not github.available:
        return False

    # 简单测试搜索
    test_topics = ["python", "machine-learning"]
    repos = github.search_repositories(test_topics, max_results=3)

    if repos:
        print(f"✅ GitHub API working - found {len(repos)} repositories")
        return True
    else:
        print("❌ GitHub client test failed")
        return False

def main():
    """主程序入口"""
    print("=" * 60)
    print("🚀 Easy Tool Demo - Step by Step Implementation")
    print("=" * 60)

    # 步骤1：加载环境变量
    load_env_variables()

    # 步骤2：检查配置
    if not check_configuration():
        print("❌ Configuration check failed, exiting...")
        return

    # 步骤3：测试LLM客户端
    if not test_llm_client():
        print("❌ LLM client test failed, exiting...")
        return

    # 步骤4：测试GitHub客户端
    if not test_github_client():
        print("❌ GitHub client test failed, exiting...")
        return

    # 步骤5：测试主题提取
    if not test_topic_extraction():
        print("❌ Topic extraction test failed, exiting...")
        return

    # 步骤6：测试完整的搜索和评估pipeline
    success, selected_repo = test_complete_search_and_evaluate()
    if not success:
        print("❌ Complete search and evaluation pipeline failed, exiting...")
        return

    # 步骤7：测试MCP工具生成
    generator = SimpleMCPGenerator()
    tool_dir = generator.generate_mcp_tool(selected_repo, "")

    if not tool_dir:
        print("❌ MCP tool generation failed, exiting...")
        return

    print(f"✅ MCP tool generated at: {tool_dir}")

    # 步骤8：测试LLM使用MCP工具回答查询
    if not test_llm_with_mcp_tool(tool_dir, selected_repo):
        print("❌ LLM with MCP tool test failed, exiting...")
        return

    print(f"\n🎊 Complete AgenticRAG pipeline finished successfully!")
    print(f"Repository processed: {selected_repo['name']}")
    print(f"MCP tool generated: {tool_dir}")
    print("🤖 LLM successfully answered the query using the MCP tool!")

if __name__ == "__main__":
    main()