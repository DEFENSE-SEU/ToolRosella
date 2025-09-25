import json
import os
import tempfile
import shutil
from typing import Dict, List, Optional, Annotated
from pathlib import Path
import subprocess
from openai import OpenAI


class GitHubRepositoryAnalyzer:
    """
    GitHub repository analyzer that clones and analyzes repositories to generate summaries
    """
    
    def __init__(self, max_important_files_token: int = 2000, api_key: str = None, base_url: str = None):
        """
        Initialize the analyzer
        
        Args:
            max_important_files_token: Token count limit for important files
            api_key: OpenAI API key for LLM calls
            base_url: Base URL for the API
        """
        self.max_important_files_token = max_important_files_token
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = "deepseek-r1"
        
        self.supported_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift',
            '.md', '.txt', '.json', '.yaml', '.yml', '.xml',
            '.html', '.css', '.scss', '.sass', '.vue', '.jsx', '.tsx'
        }
    
    def analyze_repository(self, github_url: str) -> Dict[str, str]:
        """
        Analyze a GitHub repository and generate summary
        
        Args:
            github_url: GitHub repository URL (e.g., https://github.com/user/repo)
            
        Returns:
            Dict[str, str]: Repository summary with file paths as keys and summaries as values
        """
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone repository
            repo_path = self._clone_repository(github_url, temp_dir)
            
            # Extract code files
            code_list = self._extract_code_files(repo_path)
            
            # Generate repository summary
            repository_summary = self._generate_repository_summary(code_list)
            
            return repository_summary
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _clone_repository(self, github_url: str, temp_dir: str) -> str:
        """
        Clone GitHub repository to temporary directory
        
        Args:
            github_url: GitHub repository URL
            temp_dir: Temporary directory path
            
        Returns:
            str: Path to cloned repository
        """
        try:
            # Extract repo name from URL
            repo_name = github_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            
            repo_path = os.path.join(temp_dir, repo_name)
            
            # Clone repository
            subprocess.run(
                ['git', 'clone', github_url, repo_path],
                check=True,
                capture_output=True,
                text=True
            )
            
            return repo_path
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone repository: {e.stderr}")
        except Exception as e:
            raise Exception(f"Error cloning repository: {str(e)}")
    
    def _extract_code_files(self, repo_path: str) -> List[Dict[str, str]]:
        """
        Extract code files from repository
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            List[Dict[str, str]]: List of file information with file_path and file_content
        """
        code_list = []
        repo_path_obj = Path(repo_path)
        
        # Walk through all files in repository
        for file_path in repo_path_obj.rglob('*'):
            # Skip directories and hidden files/folders
            if file_path.is_dir() or any(part.startswith('.') for part in file_path.parts):
                continue
                
            # Check if file extension is supported
            if file_path.suffix.lower() in self.supported_extensions:
                try:
                    # Get relative path from repo root
                    relative_path = file_path.relative_to(repo_path_obj)
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Skip empty files
                    if content.strip():
                        code_list.append({
                            'file_path': str(relative_path),
                            'file_content': content
                        })
                        
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
        
        return code_list
    
    def _generate_repository_summary(self, code_list: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Generate repository summary from code files
        
        Args:
            code_list: List containing code file information
            
        Returns:
            Dict[str, str]: Repository summary
        """
        # Check if all files can fit within token limit
        all_file_content = json.dumps(code_list, ensure_ascii=False)
        if self._get_code_abs_token(all_file_content) < self.max_important_files_token:
            return {file['file_path']: file['file_content'] for file in code_list}
        
        # Get important files
        important_files = []
        for s_code_list in self._split_code_lists(code_list):
            important_files.extend(self._judge_file_is_important(s_code_list))
        
        print(f'Important files: Total={len(code_list)}, Important={len(important_files)}')
        print(f'Important file paths: {[file["file_path"] for file in important_files]}')
        
        # Generate summaries for important files
        repository_summary = {}
        
        for file in important_files:
            file_path = file['file_path']
            file_content = file['file_content']
            
            try:
                summary = self._get_readme_summary(file_content, repository_summary)
                if '<none>' not in str(summary).lower():
                    # Check if adding this summary exceeds token limit
                    if self._get_code_abs_token(
                        json.dumps(repository_summary, ensure_ascii=False) + str(summary)
                    ) > self.max_important_files_token:
                        break
                    repository_summary[file_path] = summary
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue
        
        print(f'Repository summary token count: {self._get_code_abs_token(json.dumps(repository_summary, ensure_ascii=False))}')
        return repository_summary
    
    def _judge_file_is_important(self, code_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Judge which files are important for understanding the repository
        
        Args:
            code_list: List of code files
            
        Returns:
            List[Dict[str, str]]: List of important files
        """
        judge_prompt = """
        You are an assistant that helps developers understand code repositories. Please judge whether the current file is important for understanding the entire repository.
        Output yes for important files, no for unimportant files.
        
        Please judge whether a file is important according to the following rules:
        1. If the file is README.md and the file content contains a description of the entire repository, then consider it very important
        2. If it is a configuration file or test file or example file, then consider it very important
        3. If the file content contains information that is important for understanding the entire repository, then consider it very important, please do not ignore any important information
        4. If several files have completely duplicate file content, possibly with different filenames or languages, then keep only one (output yes) and delete the others (output no)
        
        ## Please note:
        - Please do not ignore any important information
        
        Please return a JSON list (list sorted by importance) format containing judgment of whether files are important:
        [
            {
                "file_path": "File path",
                "is_important": "yes" or "no"
            }
        ]
        """
        
        messages = [
            {"role": "system", "content": judge_prompt},
            {"role": "user", "content": json.dumps(code_list, ensure_ascii=False, indent=2)}
        ]
        
        try:
            # TODO: Replace with your LLM implementation
            response_dict = self._call_llm(messages, json_format=True)
            print('LLM response: ', response_dict)
            
            if not isinstance(response_dict, list):
                return code_list
                
            out_list = []
            for judge_result in response_dict:
                if judge_result['is_important'].lower() == 'yes':
                    for file in code_list:
                        if judge_result['file_path'] == file['file_path']:
                            out_list.append(file)
            return out_list
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return code_list
    
    def _split_code_lists(self, code_list: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        """
        Split code list into chunks based on token count
        
        Args:
            code_list: List of code files
            
        Returns:
            List[List[Dict[str, str]]]: List of code file chunks
        """
        max_token = 50000
        out_code_list = []
        split_code_list = []
        
        for file in code_list:
            if self._get_code_abs_token(str(file)) > max_token:
                continue
                
            split_code_list.append(file)
            if self._get_code_abs_token(json.dumps(split_code_list, ensure_ascii=False, indent=2)) > max_token:
                out_code_list.append(split_code_list[:-1])  # Don't include the last file that exceeded limit
                split_code_list = [file]  # Start new chunk with the current file
                
        if split_code_list:
            out_code_list.append(split_code_list)
            
        return out_code_list
    
    def _get_readme_summary(self, code_content: str, history_summary: Dict[str, str]) -> str:
        """
        Get summary of README.md and other important documentation files
        
        Args:
            code_content: File content
            history_summary: Previously generated summaries
            
        Returns:
            str: File summary
        """
        system_prompt = """
        You are an assistant that helps developers understand code repositories. Please provide an overall understanding of the entire repository based on the provided README and other documentation files and generate a summary.
        
        When generating the summary, please follow these rules:
        1. Focus on the project's main functions, architectural design and usage methods, generate content as concise as possible, but do not miss important code blocks and commands, do not miss any important information (especially model and file download methods and model usage methods)
        2. When encountering important code that can be directly referenced from documentation, use <cite>referenced content</cite> format
        3. Keep the summary concise, comprehensive and informative
        4. Include installation methods, dependencies and example usage (if provided in documentation)
        5. If it's disclaimers or other content unimportant to code repository understanding, then ignore it.
        6. If it duplicates content in history_summary, then no need to output repeatedly.
        """
        
        prompt = f"""
        The following is the README and other important documents in the code repository:
        <code_content>
        {code_content}
        </code_content>
        
        The following is the summary of other important documents:
        <history_summary>
        {history_summary}
        </history_summary>
        
        If it duplicates content in history_summary, then no need to output repeatedly.
        """
        
        response = self._call_llm(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            json_format=True
        )
        return response
    
    def _get_code_abs_token(self, content: str) -> int:
        """
        Get approximate token count for content
        
        Args:
            content: String content
            
        Returns:
            int: Approximate token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        return len(content) // 4
    
    def _call_llm(self, messages: List[Dict[str, str]], json_format: bool = False):
        """
        Call LLM API using OpenAI client
        
        Args:
            messages: List of messages
            json_format: Whether to return JSON format
            
        Returns:
            LLM response
        """
        try:
            if json_format:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.5
                )
            
            content = response.choices[0].message.content
            
            # If json_format is requested, try to parse the JSON
            if json_format:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {e}")
                    print(f"Response content: {content}")
                    # Try to extract JSON from the content
                    import re
                    json_match = re.search(r'\[.*\]|\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass
                    return []  # Return empty list if JSON parsing fails
            
            return content
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            if json_format:
                return []
            return ""


# Usage example
if __name__ == "__main__":
    # Initialize analyzer with your API key
    analyzer = GitHubRepositoryAnalyzer(
        max_important_files_token=2000,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Analyze a GitHub repository
    github_url = "https://github.com/username/repository"
    try:
        summary = analyzer.analyze_repository(github_url)
        print("Repository Summary:")
        for file_path, content in summary.items():
            print(f"\n{file_path}:")
            print(content)
    except Exception as e:
        print(f"Error analyzing repository: {e}")