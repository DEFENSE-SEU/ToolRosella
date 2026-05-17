<a href="ToolRosella.pdf">
  <img src="assets/ToolRosella_preview.png" alt="ToolRosella paper preview" width="220" align="right" />
</a>

# ToolRosella

[![arXiv](https://img.shields.io/badge/arXiv-2603.09290-b31b1b.svg)](https://arxiv.org/abs/2603.09290)

ToolRosella is a three-agent pipeline for finding one or more task-relevant code repositories, converting them into MCP tools, and using the generated MCP tools to solve user tasks.

## Project Structure

```
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
        ├── tool_search/
        │   ├── __init__.py
        │   ├── tool_search_agent.py
        │   ├── repository_finder.py
        │   ├── query_optimizer.py
        │   └── planner.py
        ├── mcp_construction/
        │   ├── __init__.py
        │   ├── mcp_construction_agent.py
        │   └── code2mcp/
        │       ├── workflow.py
        │       ├── model_config.py
        │       ├── utils.py
        │       ├── nodes/
        │       │   ├── download_node.py
        │       │   ├── analysis_node.py
        │       │   ├── env_node.py
        │       │   ├── generate_node.py
        │       │   ├── code_check_node.py
        │       │   ├── run_node.py
        │       │   ├── review_node.py
        │       │   └── finalize_node.py
        │       └── tools/
        │           ├── deepwiki_client.py
        │           └── gitingest_client.py
        └── planning/
            ├── __init__.py
            └── planning_agent.py
```

---

## Quick Start

### 1. Create Environment

Python 3.10+ is recommended.

```bash
conda create -n toolrosella python=3.10 -y
conda activate toolrosella
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the environment template:

```bash
cp env_example.txt .env
```

Set the following in `.env`:

```bash
# Required: GitHub token for repository search
GITHUB_TOKEN=xxx

# Choose one LLM provider — example with OpenAI-compatible configuration
MODEL_PROVIDER=openai
OPENAI_API_KEY=xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5
```

Other providers (DeepSeek, Qwen, Claude, Bedrock, Ollama) are documented in `env_example.txt`.

### 3. Run Without Planning Execution

This mode searches or accepts repositories, builds MCP services, and writes the Planning Agent prompt and config. It does not call the generated MCP tools automatically.

Use provided repositories:

```bash
python3 main.py "Please use https://github.com/xxx/xxx and https://github.com/xxx/yyy to solve xxx."
```

Or let ToolRosella search for repositories:

```bash
python3 main.py "Find Python repositories that can solve xxx, build them as MCP, and answer xxx."
```

### 4. Run With Claude Code CLI

Install and log in to Claude Code CLI, then verify the command is available:

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

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--workspace` | `./workspace` | Directory for cloned repos and MCP output |
| `--memory` | `./MCP_Memory` | Cache for already-processed repositories |
| `--max-repositories` | `3` | Maximum number of repositories to select and wrap |
| `--per-page` | `50` | GitHub search results per page |
| `--no-refine` | — | Disable query refinement on search failure |
| `--hinted-text` | — | One-word GitHub text-search hint |

---

## Outputs

Generated MCP packages are written to `workspace/<repo-name>/mcp_output/`:

| File | Description |
|------|-------------|
| `start_mcp.py` | MCP service entry point |
| `mcp_plugin/mcp_service.py` | Generated MCP service |
| `mcp_plugin/adapter.py` | Repository adapter |
| `requirements.txt` | Service dependencies |
| `README_MCP.md` | Usage documentation |
| `workflow_summary.json` | Construction summary |
| `planning_agent/mcp.json` | MCP config for Planning Agent |
| `planning_agent/task_prompt.md` | Task prompt |
| `planning_agent/agent_stdout.txt` | Agent output |

For multiple repositories, combined Planning Agent files are written to `workspace/planning_agent/`. When Planning Agent execution is enabled, the final answer is available at `result.invocation_plan['execution']['final_answer']`.

---


## Citation

If you find this work useful, please cite our paper:

```bibtex
@misc{di2026toolrosellatranslatingcoderepositories,
      title={ToolRosella: Translating Code Repositories into Standardized Tools for Scientific Agents}, 
      author={Shimin Di and Xujie Yuan and Hanghui Guo and Chaoqian Ouyang and Yongxu Liu and Ling Yue and Zhangze Chen and Libin Zheng and Jia Zhu and Shaowu Pan and Jian Yin and Yong Rui and Min-Ling Zhang},
      year={2026},
      eprint={2603.09290},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2603.09290}, 
}
```
