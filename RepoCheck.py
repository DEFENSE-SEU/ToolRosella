import requests
import base64
import os
import json
from urllib.parse import urlparse
import shutil
import git
import re

class GitHubRepoReader:
    def __init__(self, repo_url, token):
        self.repo_url = repo_url
        self.token = token
        self.owner, self.repo = self._parse_repo_url(repo_url)
        self.headers = {
            "Authorization": f"token {token}"
        }
        self.files_data = {
            "py_files": {},
            "md_files": {}
        }
        self.output_dir = './github_json/'
        self.cache_file = './repo_cache.json'
        self.cache = self._load_cache()

    def _parse_repo_url(self, repo_url):
        parsed_url = urlparse(repo_url)
        path = parsed_url.path.strip('/').split('/')
        if len(path) == 2:
            return path[0], path[1]
        else:
            raise ValueError("Invalid GitHub repository URL")

    def _get_file_content(self, file_url):
        response = requests.get(file_url, headers=self.headers)
        if response.status_code == 200:
            file_content = base64.b64decode(response.json()['content']).decode('utf-8')
            return file_content
        else:
            print(f"Failed to get file content, status code: {response.status_code}")
            return None

    def _is_allowed_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        return ext.lower() in {".md", ".py"}

    def _traverse_repo(self, path=""):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            files = response.json()
            for file in files:
                if file['type'] == 'file':
                    if self._is_allowed_file(file['path']):
                        print(f"Reading file: {file['path']}")
                        content = self._get_file_content(file['url'])
                        if content:
                            if file['path'].endswith('.py'):
                                self.files_data['py_files'][file['path']] = content
                            elif file['path'].endswith('.md'):
                                self.files_data['md_files'][file['path']] = content
                    else:
                        print(f"Skipping file: {file['path']} (not .md or .py)")
                elif file['type'] == 'dir':
                    print(f"Entering folder: {file['path']}")
                    self._traverse_repo(file['path'])
        else:
            print(f"Failed to get folder {path} contents, status code: {response.status_code}")

    def save_files_to_json(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        output_file = os.path.join(self.output_dir, f"{self.repo}.json")
        
        with open(output_file, "w") as f:
            json.dump(self.files_data, f, indent=4)
        
        print(f"File content saved as {output_file}")
        return output_file

    def process_repo(self):
        self._traverse_repo()
        return self.save_files_to_json()

    # ================ 可选逻辑：克隆+README+严格判定 & 简易缓存 ================
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def clone_and_read_readme(self) -> str:
        dst = os.path.join('repos', self.repo)
        try:
            git.Repo.clone_from(self.repo_url + '.git' if not self.repo_url.endswith('.git') else self.repo_url, dst)
        except Exception:
            pass
        try:
            for f in os.listdir(dst):
                if 'readme' in f.lower():
                    with open(os.path.join(dst, f), 'r', encoding='utf-8', errors='ignore') as fh:
                        return fh.read()
            return ""
        except Exception:
            return ""
        finally:
            shutil.rmtree(dst, ignore_errors=True)

    def judge_repo_strict(self, query: str, readme: str) -> bool:
        # 这里采用启发式+可对接外部 LLM（如有）
        text = (readme or '').lower()
        has_env = any(k in text for k in ['install', 'installation', 'setup', 'requirements', 'environment'])
        has_cmd = any(k in text for k in ['usage', 'command', 'run', 'python ', 'cli', 'example', 'examples'])
        return has_env and has_cmd

    def decide_using_cache_or_search(self, query: str) -> tuple:
        # 若缓存中已有被描述过且匹配的仓库，则直接使用
        for name, info in self.cache.items():
            desc = info.get('description') or ''
            if desc and re.search(r"\b" + re.escape(name) + r"\b", desc, re.I):
                return name, info.get('url')
        return None, None

    def update_cache(self, repo_name: str, repo_url: str, description: str = None):
        self.cache[repo_name] = {"url": repo_url, "description": description or ""}
        self._save_cache()


# repo_url = "https://github.com/ghh1125/DOCTOR"
# token =

# repo_reader = GitHubRepoReader(repo_url, token)

# saved_file_path = repo_reader.process_repo()

# print(f"File saved to: {saved_file_path}")
