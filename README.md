# ToolRosella

ToolRosella is a three-agent pipeline for finding one or more task-relevant code repositories, converting them into MCP tools, and using the generated MCP tools to solve user tasks.

## Three Agents

### Tool-search Agent

The Tool-search Agent selects one or more repositories for the user task. Direct GitHub URLs are used as provided; otherwise, the agent extracts task topics, searches GitHub, checks candidate repositories, and keeps up to `--max-repositories` complementary repositories.

### MCP-construction Agent

The MCP-construction Agent converts each selected repository into an MCP service:

```text
Download -> Analysis -> Env -> Generate -> Code check -> Run -> Review -> Finish
```

It clones each repository, analyzes reusable functions, prepares dependencies, generates MCP wrappers, validates the generated code, runs the service, repairs failures when needed, and writes MCP packages.

### Planning Agent

The Planning Agent discovers tools from all generated MCP packages, writes a combined MCP config, and builds a ReAct-style tool-use prompt. If execution is enabled, it calls an external MCP-capable CLI such as Claude Code and returns the CLI output as `final_answer`.

## Project Structure

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── env_example.txt
├── README.md
└── src/
    └── ToolRosella/
        ├── __init__.py
        ├── cli.py
        ├── env.py
        ├── pipeline.py
        ├── tool_search_agent.py
        ├── repository_finder.py
        ├── planner.py
        ├── query_optimizer.py
        ├── mcp_construction_agent.py
        ├── planning_agent.py
        └── code2mcp/
            ├── workflow.py
            ├── model_config.py
            ├── utils.py
            ├── nodes/
            │   ├── download_node.py
            │   ├── analysis_node.py
            │   ├── env_node.py
            │   ├── generate_node.py
            │   ├── code_check_node.py
            │   ├── run_node.py
            │   ├── review_node.py
            │   └── finalize_node.py
            └── tools/
                ├── deepwiki_client.py
                └── gitingest_client.py
```

## Quick Start

### 1. Create Environment

Python 3.10+ is recommended.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `python3.10` is not available, use your local Python 3.10+ executable.

### 2. Configure API Keys

Copy the environment template:

```bash
cp env_example.txt .env
```

Set a GitHub token for repository search:

```bash
GITHUB_TOKEN=xxx
```

Choose one LLM provider in `.env`. Example with OpenAI-compatible configuration:

```bash
MODEL_PROVIDER=openai
OPENAI_API_KEY=xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5
```

Other provider options are listed in `env_example.txt`, including DeepSeek, Qwen, Claude, Bedrock, and Ollama.

### 3. Run Without Planning Execution

This mode searches or accepts repositories, builds MCP services, and writes the Planning Agent prompt/config. It does not call the generated MCP tools automatically.

Use provided repositories:

```bash
python3 main.py "Please use https://github.com/xxx/xxx and https://github.com/xxx/yyy to solve xxx."
```

Or let ToolRosella search for repositories:

```bash
python3 main.py "Find Python repositories that can solve xxx, build them as MCP, and answer xxx."
```

### 4. Run With Claude Code CLI

Install and log in to Claude Code CLI first, then make sure the command is available:

```bash
claude --help
```

Enable Planning Agent execution:

```bash
export TOOLROSELLA_RUN_PLANNING_AGENT=true
export TOOLROSELLA_AGENT_COMMAND=claude
```

Then run ToolRosella:

```bash
python3 main.py "Please use https://github.com/xxx/xxx and https://github.com/xxx/yyy to solve xxx."
```

Internally, the Planning Agent writes:

```text
workspace/<repo-name>/mcp_output/planning_agent/mcp.json
workspace/<repo-name>/mcp_output/planning_agent/task_prompt.md
```

For one generated MCP package, it calls the external agent in this form:

```bash
claude -p "<task prompt>" --mcp-config workspace/<repo-name>/mcp_output/planning_agent/mcp.json
```

For multiple generated MCP packages, ToolRosella writes one combined config under `workspace/planning_agent/mcp.json`. The Claude Code CLI can then load all generated MCP servers, call tools across them, and return the final answer.

Useful options:

```bash
python3 main.py --workspace ./workspace --memory ./MCP_Memory --per-page 20 "xxx"
python3 main.py --max-repositories 3 "xxx"
python3 main.py --no-refine "xxx"
python3 main.py --hinted-text "xxx" "xxx"
```

## Outputs

Generated MCP packages are written to:

```text
workspace/<repo-name>/mcp_output/
```

Important files:

```text
start_mcp.py
mcp_plugin/mcp_service.py
mcp_plugin/adapter.py
requirements.txt
README_MCP.md
workflow_summary.json
planning_agent/mcp.json
planning_agent/task_prompt.md
planning_agent/agent_stdout.txt
planning_agent/agent_stderr.txt
```

For multiple repositories, the combined Planning Agent files are written to:

```text
workspace/planning_agent/mcp.json
workspace/planning_agent/task_prompt.md
workspace/planning_agent/agent_stdout.txt
workspace/planning_agent/agent_stderr.txt
```

When Planning Agent execution is enabled, the final result is available in:

```text
planning_result.execution.final_answer
```
