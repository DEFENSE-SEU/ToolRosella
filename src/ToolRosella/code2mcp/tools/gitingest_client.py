# GitHub Repository Preprocessing Client - Using gitingest library or zip fallback solution
import os
import io
import zipfile
import logging
import time
from typing import Dict, Any, Tuple
from urllib.parse import urlparse
from urllib.request import urlopen

logger = logging.getLogger(__name__)

import logging

for logger_name in ["gitingest", "gitingest.clone", "gitingest.entrypoint", "gitingest.ingestion", "gitingest.utils"]:
    logger = logging.getLogger(logger_name)
    logger.disabled = True
    logger.propagate = False
    logger.handlers = []

original_callHandlers = logging.Logger.callHandlers

def smart_filtered_callHandlers(self, record):
    if not record.name.startswith('gitingest'):
        return original_callHandlers(self, record)
    
    message = str(record.getMessage())
    
    essential_keywords = [
        "Starting git clone operation",
        "Git clone completed successfully",
        "Repository cloned, starting file processing",
        "Processing files and generating output",
        "Directory processing completed"
    ]
    
    if any(keyword.lower() in message.lower() for keyword in essential_keywords):
        return original_callHandlers(self, record)
    
    return

logging.Logger.callHandlers = smart_filtered_callHandlers

try:
    from gitingest import ingest
    GITINGEST_AVAILABLE = True
    logger.info("gitingest imported successfully")
except ImportError:
    GITINGEST_AVAILABLE = False
    logger.warning("gitingest not installed, will use fallback solution")

class GitingestClient:
    
    def __init__(self):
        self.available = GITINGEST_AVAILABLE
        self.max_tokens = int(os.getenv("ANALYSIS_MAX_TOKENS", "8000"))
        self.max_file_tokens = int(os.getenv("ANALYSIS_MAX_FILE_TOKENS", "2000"))
        self.min_chars = int(os.getenv("ANALYSIS_MIN_CHARS", "500"))
        
        if not self.available:
            logger.warning("gitingest not available, will use fallback repository analysis solution")
        else:
            logger.info(f"gitingest client initialized successfully, token limit: {self.max_tokens}")
    
    def is_github_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc in ['github.com', 'www.github.com']
    
    def preprocess_repository_sync(self, repo_url: str) -> Dict[str, Any]:
        if not self.is_github_url(repo_url):
            logger.warning(f"Non-GitHub URL: {repo_url}")
            return self._create_fallback_result(repo_url)
        
        if not self.available:
            logger.warning("gitingest not available, using zip fallback solution")
            zip_ok, result = self._fallback_via_zip(repo_url)
            if zip_ok:
                return result
            return self._create_fallback_result(repo_url, error=result.get("error") if isinstance(result, dict) else str(result))

        try:
            logger.info(f"Using gitingest to preprocess repository: {repo_url}")
            attempts = 0
            last_err = None
            while attempts < 3:
                attempts += 1
                try:
                    logger.info(f"Attempting to call gitingest.ingest({repo_url}) - attempt {attempts}")

                    import os
                    os.environ['PYTHONIOENCODING'] = 'utf-8'

                    import platform
                    if platform.system() == 'Windows':
                        import warnings
                        warnings.filterwarnings("ignore", category=ResourceWarning)
                        warnings.filterwarnings("ignore", message=".*unclosed transport.*")
                        warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
                        warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
                        import asyncio

                        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

                        import logging
                        logging.getLogger("asyncio").setLevel(logging.ERROR)

                    result_data = ingest(repo_url)
                    logger.info(f"gitingest return data type: {type(result_data)}, length: {len(result_data) if isinstance(result_data, (tuple, list)) else 'N/A'}")
                    
                    try:
                        if isinstance(result_data, tuple):
                            if len(result_data) >= 3:
                                summary, tree, content = result_data[:3]
                            elif len(result_data) == 2:
                                summary, tree = result_data
                                content = {}
                            else:
                                summary = result_data[0] if result_data else "gitingest processing result"
                                tree = {}
                                content = {}
                        else:
                            summary = str(result_data) if result_data else "gitingest processing result"
                            tree = {}
                            content = {}
                    except Exception as unpack_error:
                        logger.error(f"Failed to unpack gitingest return value: {unpack_error}, original data: {result_data}")
                        summary = "gitingest processing result"
                        tree = {}
                        content = {}
                    
                    limited_content = {}
                    if isinstance(content, dict):
                        for file_path, file_content in content.items():
                            if isinstance(file_content, str):
                                if len(file_content) > 1000:
                                    limited_content[file_path] = file_content[:1000] + "..."
                                else:
                                    limited_content[file_path] = file_content
                            else:
                                limited_content[file_path] = str(file_content)[:500] + "..." if len(str(file_content)) > 500 else str(file_content)
                        if len(limited_content) > 50:
                            limited_content = dict(list(limited_content.items())[:50])
                    
                    result = {
                        "repository_url": repo_url,
                        "summary": summary,
                        "file_tree": tree,
                        "content": limited_content,
                        "processed_by": "gitingest",
                        "success": True
                    }
                    logger.info(f"gitingest preprocessing completed, extracted {len(content) if content else 0} files, retained {len(limited_content)} files after limitation")
                    return result
                except Exception as e:
                    last_err = e
                    backoff = min(60, 5 * attempts) 
                    logger.warning(f"gitingest failed ({attempts}/3): {type(e).__name__}: {e}, retrying in {backoff}s")
                    time.sleep(backoff)

            logger.error(f"gitingest preprocessing failed continuously, will try zip fallback. Last error: {type(last_err).__name__}: {last_err}")
        except Exception as e:
            logger.error(f"gitingest preprocessing exception, will try zip fallback: {type(e).__name__}: {e}")

        logger.info("Trying zip fallback solution")
        zip_ok, result = self._fallback_via_zip(repo_url)
        if zip_ok:
            return result
        return self._create_fallback_result(repo_url, error=result.get("error") if isinstance(result, dict) else str(result))

    def preprocess_repository(self, repo_url: str) -> Dict[str, Any]:
        return self.preprocess_repository_sync(repo_url)
    
    def _create_fallback_result(self, repo_url: str, error: str = None) -> Dict[str, Any]:
        return {
            "repository_url": repo_url,
            "summary": f"Unable to preprocess repository: {repo_url}",
            "file_tree": {},
            "content": {},
            "processed_by": "fallback",
            "success": False,
            "error": error
        }

    def _fallback_via_zip(self, repo_url: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            try:
                owner, repo = self._parse_owner_repo(repo_url)
            except Exception as e:
                logger.error(f"Failed to parse repository address: {e}")
                return False, {"error": f"Failed to parse repository address: {e}"}
            if not owner:
                return False, {"error": "Unable to parse GitHub repository address"}
            candidates = [
                f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
                f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
                f"https://github.com/{owner}/{repo}/archive/main.zip",
                f"https://github.com/{owner}/{repo}/archive/master.zip",
            ]
            data = None
            last_err = None
            for url in candidates:
                try:
                    logger.info(f"Attempting zip fallback download: {url}")
                    
                    import urllib.request
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    
                    with urlopen(req, timeout=120) as resp:
                        data = resp.read()
                        break
                except Exception as e:
                    last_err = e
                    logger.warning(f"zip download failed: {type(e).__name__}: {e}")
            if not data:
                return False, {"error": f"zip download failed: {last_err}"}

            try:
                content, tree = self._extract_zip_content(data)
            except Exception as e:
                logger.error(f"Failed to extract zip content: {e}")
                return False, {"error": f"Failed to extract zip content: {e}"}
            summary = f"Imported via zip fallback, file count: {len(content)}"
            result = {
                "repository_url": repo_url,
                "summary": summary,
                "file_tree": tree,
                "processed_by": "zip_fallback",
                "success": True
            }
            logger.info(f"zip fallback successful, extracted file count: {len(content)}")
            return True, result
        except Exception as e:
            logger.error(f"zip fallback failed: {e}")
            return False, {"error": str(e)}

    def _parse_owner_repo(self, repo_url: str) -> Tuple[str, str]:
        parsed = urlparse(repo_url)
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) >= 2:
            return parts[0], parts[1].replace('.git', '')
        return "", ""

    def _extract_zip_content(self, data: bytes) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        zf = zipfile.ZipFile(io.BytesIO(data))
        content: Dict[str, str] = {}
        tree: Dict[str, Any] = {}

        max_file_bytes = 512 * 1024
        root_prefix = None
        for name in zf.namelist():
            if root_prefix is None:
                root_prefix = name.split('/')[0]
            rel = name[len(root_prefix):].lstrip('/') if root_prefix else name
            if not rel or rel.endswith('/'):
                continue
            if not self._is_text_like(name):
                continue
            try:
                with zf.open(name) as fp:
                    data = fp.read(max_file_bytes + 1)
                    if len(data) > max_file_bytes:
                        text = data[:max_file_bytes].decode('utf-8', errors='ignore') + "\n[File content truncated]"
                    else:
                        text = data.decode('utf-8', errors='ignore')
                content[rel] = text
                tree[rel] = {"size": len(text)}
            except Exception:
                continue
        return content, tree

    def _extract_zip_tree(self, data: bytes) -> Dict[str, Any]:
        zf = zipfile.ZipFile(io.BytesIO(data))
        tree: Dict[str, Any] = {}

        root_prefix = None
        for name in zf.namelist():
            if root_prefix is None:
                root_prefix = name.split('/')[0]
            rel = name[len(root_prefix):].lstrip('/') if root_prefix else name
            if not rel or rel.endswith('/'):
                continue
            if not self._is_text_like(name):
                continue
            try:
                file_info = zf.getinfo(name)
                tree[rel] = {"size": file_info.file_size}
            except Exception:
                continue
        return tree

    def _is_text_like(self, filename: str) -> bool:
        lower = filename.lower()
        text_exts = ('.py', '.md', '.txt', '.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.java', '.js', '.ts')
        return lower.endswith(text_exts)
    
    def extract_key_files(self, content: Dict[str, Any], max_tokens: int = None) -> Dict[str, Any]:
        if not content:
            return {}
        
        if max_tokens is None:
            max_tokens = self.max_tokens
        priority_patterns = [
            ("main.py", 100), ("app.py", 100), ("server.py", 100), ("index.py", 100), ("run.py", 100),
            ("requirements.txt", 90), ("pyproject.toml", 90), ("setup.py", 90), ("package.json", 90),
            ("README.md", 85), ("README.txt", 85), ("docs/", 80),
            ("src/", 70), ("lib/", 70), ("core/", 70), ("api/", 70), ("app/", 70),
            ("test/", 60), ("tests/", 60), ("spec/", 60),
            (".py", 50), (".js", 50), (".ts", 50), (".java", 50), (".go", 50)
        ]
        
        file_scores = {}
        for file_path, file_content in content.items():
            priority = self._calculate_priority(file_path, priority_patterns)
            size = len(file_content)
            
            score = priority + (size / 1000)
            
            file_scores[file_path] = {
                "content": file_content,
                "size": size,
                "priority": priority,
                "score": score
            }
        
        sorted_files = dict(sorted(
            file_scores.items(), 
            key=lambda x: x[1]["score"], 
            reverse=True
        ))
        
        selected_files = {}
        current_tokens = 0
        
        for file_path, file_info in sorted_files.items():
            estimated_tokens = len(file_info["content"]) * 1.3
            
            if current_tokens + estimated_tokens <= max_tokens:
                selected_files[file_path] = file_info
                current_tokens += estimated_tokens
            else:
                if file_info["priority"] >= 80:
                    max_content_length = int((max_tokens - current_tokens) / 1.3)
                    if max_content_length > self.min_chars:
                        selected_files[file_path] = {
                            **file_info,
                            "content": file_info["content"][:max_content_length],
                            "truncated": True
                        }
                        current_tokens += max_content_length * 1.3
                        break
        
        logger.info(f"Intelligently selected {len(selected_files)} files, estimated token count: {current_tokens:.0f}")
        return selected_files
    
    def _calculate_priority(self, file_path: str, patterns: list) -> int:
        priority = 0
        for pattern, score in patterns:
            if pattern in file_path:
                priority = max(priority, score)
        return priority
    
    def create_analysis_prompt(self, gitingest_result: Dict[str, Any], max_tokens: int = None) -> str:
        if not gitingest_result.get("success"):
            return "Please analyze the basic structure of this code repository."
        
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        summary = gitingest_result.get("summary", "")
        key_files = self.extract_key_files(gitingest_result.get("content", {}), max_tokens - 2000)
        
        prompt = f"""
Based on the following code repository information for analysis:

Repository Summary:
{summary}

Key Files:
"""
        
        for file_path, file_info in key_files.items():
            content = file_info["content"]
            if file_info.get("truncated", False):
                content += "\n[File content truncated]"
            prompt += f"\nFile: {file_path}\nContent:\n{content}\n"
        
        prompt += """
Please strictly return analysis results in the following JSON format, do not add any other text:
{
    "Project Function Analysis": "Main function description of the project",
    "Technology Stack": ["Technology 1", "Technology 2"],
    "Main Dependencies": ["Dependency 1", "Dependency 2"],
    "API Endpoints": ["Endpoint 1", "Endpoint 2"],
    "Architecture Recommendations": "Recommended architecture design",
    "MCP Tool Suggestions": [
        {
            "name": "Tool name",
            "description": "Tool description",
            "parameters": {},
            "return_type": "str"
        }
    ]
}
"""
        
        return prompt


async def preprocess_github_repo(repo_url: str) -> Dict[str, Any]:
    client = GitingestClient()
    return await client.preprocess_repository(repo_url)


def is_github_repo(url: str) -> bool:
    client = GitingestClient()
    return client.is_github_url(url)


def get_analysis_config() -> Dict[str, Any]:
    import os
    return {
        "max_tokens": int(os.getenv("ANALYSIS_MAX_TOKENS", "8000")),
        "max_file_tokens": int(os.getenv("ANALYSIS_MAX_FILE_TOKENS", "2000")),
        "min_chars": int(os.getenv("ANALYSIS_MIN_CHARS", "500"))
    }


def print_analysis_config():
    config = get_analysis_config()
    print("=== Code Analysis Configuration ===")
    print(f"Maximum Token Count: {config['max_tokens']}")
    print(f"Maximum Token Count per File: {config['max_file_tokens']}")
    print(f"Minimum Character Retention: {config['min_chars']}")
    print("==================================") 