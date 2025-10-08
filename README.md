# AgenticRAG-TOOL-MCP 🤖

A modular pipeline for searching, summarizing, and evaluating GitHub repositories using LLMs and agentic workflows.  
The primary function of this repository is to **find a suitable GitHub repo based on an input query**, then use a **MCP** to package the code as a tool for an **LLM to call and generate answers**.

---

## 📂 Directory Structure

```
AgenticRAG-TOOL-MCP/
│
├── main.py                     # Entry point for pipeline execution
├── LLM_Plan.py                 # Generates search plans and keywords for repo search
├── LLM_Plan_withtext.py        # (Optional) Accepts user-specified GitHub repos
├── RAG.py                      # GitHub repo retrieval and selection logic
├── LLM_Action.py               # Refines queries via LLM if no suitable repo found
├── Repo_summary.py             # Summarizes and analyzes candidate repos
├── MCP.py, MCP_Use.py          # MCP agent logic
├── dataset.py                  # Dataset utilities
├── RepoCheck.py                # Repo validation utilities
│
├── github_json/                # Predefined repo metadata
├── logs/                       # Log files
├── MCP_Memory/                 # Processed repo cache
├── MCP-agent-github-repo-output/  # MCP workflow scripts
└── repos/                      # Cloned repositories
```

---

## 🚀 How to Run

### 1. Create and activate environment

```bash
conda create -n agenticrag python=3.10
conda activate agenticrag
cp env_example.txt .env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# Or install requirements in runnning as needed
```

### 3. Set API keys

Set your GitHub token:

Follow these steps to create a GitHub Personal Access Token:

1. Log in to [GitHub](https://github.com).  
2. Click your avatar → **Settings**.  
3. Scroll down → **Developer settings**.  
4. Go to **Personal access tokens → Tokens (Fine-grained tokens)**.  
5. Click **Generate new token**.

```bash
export GITHUB_TOKEN="your_github_token"
```

Set your OpenAI API key and base URL (may choose gpt-4o, gpt-5, deepseek v3.1, deepseek v3):

```bash
export OPENAI_API_KEY="your_openai_key"
# Aliyun URL
# https://bailian.console.aliyun.com/&tab=doc?spm=5176.29597918.J_SEsSjsNv72yRuRFS2VknO.4.28887b08tpTOpy&tab=home#/home
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
# Or use OpenAI API (OPENAI_BASE_URL)
# https://platform.openai.com/docs/overview
```

### 4. Run the pipeline

```bash
# First modify the input query in main. py (You can see Example Usage below)
# Then run main.py
python main.py
```

## ⚙️ Pipeline Overview

**Topic Extraction**  
`llm_generate_topics(query)` uses an LLM to extract relevant topics from the user query.

**GitHub Search**  
`github_api_search_by_topics(topics)` searches GitHub for repositories that match the extracted topics.

**Repository Evaluation**  
For each candidate repository:
- Clone and read README: `clone_and_read_readme(repo)`
- Strict evaluation: `judge_repo_strict(query, readme)` 
- If suitable, return repo name and URL.

**MCP**

`MCP.py`: use mcp to generate tool

`MCP_Use.py`: mcp with LLM answer

**The overall pipline**
```
topics = llm_generate_topics(query)
repos = github_api_search_by_topics(topics)
for repo in repos:
    readme = clone_and_read_readme(repo)
    if judge_repo_strict(query, readme):
        return repo_name, repo_url
tool = MCP(repo_url)
answer = LLM(tool, query)
```

**Additional optimization measures**

- **Query Refinement**  
If no suitable repository is found, `LLM_Action.py` uses an LLM to refine the query and repeat the search.

- **Repository Summarization**  
`Repo_summary.py`: Optimizes GitHub repository search when direct retrieval does not yield suitable results.



## ✨ Example Usage

```python
query = "Having a protein sequence: 'MENFQKVEKIGEGTYGVVYKA....' and its mutation site: 'Q145G', please help me analyze this protein sequence and predict mutation effects."

# or choose tool（designated repo）
# Firstly choose import LLM_Plan_withtext.py in main.py
query = "Please use xxx(https://github.com/xxx/xxx) to fulfill this task: Having a protein sequence: 'MENFQKVEKIGEGTYGVVYKA....' and its mutation site: 'Q145G', please help me analyze this protein sequence and predict mutation effects."

python main.py
# The pipeline will automatically search, evaluate, 
# and return the best matching GitHub repo to address the query.
```

## 🤝 Contact

For issues or contributions, please open an issue or a pull request on the repository.
