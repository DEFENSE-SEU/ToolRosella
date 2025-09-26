#!/usr/bin/env python3

import os
import sys
import asyncio
import warnings
import platform
from pathlib import Path
import logging
from loguru import logger
import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse

logging.getLogger("gitingest").setLevel(logging.CRITICAL)
logging.getLogger("gitingest.entrypoint").setLevel(logging.CRITICAL)
logging.getLogger("gitingest.clone").setLevel(logging.CRITICAL)
logging.getLogger("gitingest.ingestion").setLevel(logging.CRITICAL)
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG", 
    filter=lambda record: not record["name"].startswith("gitingest")
)

def load_env_file():
    env_file = './MCP-agent-github-repo-output/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

if platform.system() == 'Windows':
    import warnings
    warnings.simplefilter("ignore")
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    import logging
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("asyncio.base_subprocess").setLevel(logging.ERROR)
    logging.getLogger("asyncio.proactor_events").setLevel(logging.ERROR)
    def _suppress_asyncio_warnings(*args, **kwargs): pass
    import asyncio.base_subprocess
    import asyncio.proactor_events
    if hasattr(asyncio.base_subprocess, '_warn'): asyncio.base_subprocess._warn = _suppress_asyncio_warnings
    if hasattr(asyncio.proactor_events, '_warn'): asyncio.proactor_events._warn = _suppress_asyncio_warnings

project_root = Path(__file__).parent
mcp_agent_root = project_root / "MCP-agent-github-repo-output"
sys.path.append(str(mcp_agent_root))

try:
    from dotenv import load_dotenv
    env_file = mcp_agent_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"Environment file not found: {env_file}")
except ImportError:
    print("python-dotenv not installed, please set environment variables manually")

import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class MCPGitHubProcessor:
    def __init__(self, output_dir="./MCP-agent-github-repo-output/output"):
        self.memory_dir = Path("./MCP_Memory")
        self.memory_dir.mkdir(exist_ok=True)
        self.processed_repos_file = self.memory_dir / "processed_repos.json"
        self.output_dir = Path(output_dir)
        self.workspace_path = "./MCP-agent-github-repo-output/workspace"
        self.processed_repos = self.load_processed_repos()
        
        provider = os.getenv("MODEL_PROVIDER", "openai").lower()
        if provider == "deepseek":
            self.default_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif provider == "qwen":
            self.default_model = os.getenv("QWEN_MODEL", "qwen-turbo")
        elif provider == "claude":
            self.default_model = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
        else:
            self.default_model = os.getenv("DEEPWIKI_MODEL", "deepseek-r1")
    
    def load_processed_repos(self) -> List[Dict]:
        if self.processed_repos_file.exists():
            try:
                with open(self.processed_repos_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_processed_repos(self):
        try:
            with open(self.processed_repos_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_repos, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Unable to save processing record: {e}")
    
    def is_repo_processed(self, repo_name: str) -> bool:
        return any(repo['name'] == repo_name for repo in self.processed_repos)
    

    def extract_repo_name(self, github_url: str) -> str:
        try:
            parsed = urlparse(github_url)
            if parsed.netloc != "github.com":
                raise ValueError("Invalid GitHub URL")
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError("Incorrect URL format")
            
            repo_name = path_parts[1]
            return repo_name
        except Exception as e:
            raise ValueError(f"Unable to parse GitHub URL: {e}")
    
    async def process_repo(self, repo_url: str) -> bool:
        try:
            repo_name = self.extract_repo_name(repo_url)
            
            if self.is_repo_processed(repo_name):
                print(f"Repository {repo_name} already processed, skipping...")
                return True
            
            print(f"Processing repository: {repo_name}")
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            from src.workflow import WorkflowOrchestrator as ClassicWorkflowOrchestrator
            
            orchestrator = ClassicWorkflowOrchestrator(
                output_dir=str(self.output_dir), config=None
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running MCP-Agent workflow...", total=None)
                try:
                    workflow_options = {
                        "deepwiki_model": self.default_model,
                    }
                    result = await orchestrator.run_workflow(repo_url, options=workflow_options)
                    progress.update(task, completed=True)
                    
                    if result.get("success"):
                        console.print("[bold green]Workflow executed successfully![/bold green]")
                        
                        repo_info = {
                            "name": repo_name,
                            "url": repo_url,
                            "processed_time": datetime.now().isoformat(),
                            "status": "success"
                        }
                        self.processed_repos.append(repo_info)
                        self.save_processed_repos()
                        return True
                    else:
                        console.print("[bold red]Workflow execution failed![/bold red]")
                        
                        repo_info = {
                            "name": repo_name,
                            "url": repo_url,
                            "processed_time": datetime.now().isoformat(),
                            "status": "failed",
                            "error": "Workflow execution failed"
                        }
                        self.processed_repos.append(repo_info)
                        self.save_processed_repos()
                        return False
                        
                except Exception as e:
                    progress.update(task, completed=True)
                    print(f"Error in workflow: {e}")
                    
                    repo_info = {
                        "name": repo_name,
                        "url": repo_url,
                        "processed_time": datetime.now().isoformat(),
                        "status": "failed",
                        "error": str(e)
                    }
                    self.processed_repos.append(repo_info)
                    self.save_processed_repos()
                    return False
                    
        except Exception as e:
            print(f"Error processing repository: {e}")
            return False
    
    def get_processed_repo_names(self) -> List[str]:
        return [repo['name'] for repo in self.processed_repos if repo['status'] == 'success']
    
async def process_github_repos(github_url: str, output_dir="./MCP-agent-github-repo-output/output") -> Dict:
    processor = MCPGitHubProcessor(output_dir)
    success = await processor.process_repo(github_url)
    
    result = {
        "success": success,
        "processed_names": [processor.extract_repo_name(github_url)] if success else []
    }
    return result