# MCP + LLM
# A simple case for AiZynthFinder 

from pathlib import Path
import sys
import os

project_root = Path(__file__).parent
mcp_agent_root = project_root / "MCP-agent-github-repo-output"
aiz_mcp_plugin_dir = mcp_agent_root / "workspace/aizynthfinder/mcp_output/mcp_plugin"
aiz_source_path = mcp_agent_root / "workspace/aizynthfinder/source"

for p in [str(aiz_mcp_plugin_dir), str(aiz_source_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

def main():
    print("=== Using Adapter class to call AiZynthFinder tools (local execution) ===")
    print(f"Plugin directory: {aiz_mcp_plugin_dir}")
    print(f"Source directory: {aiz_source_path}")

    try:
        from adapter import Adapter
    except Exception as e:
        print("[Error] Cannot import AiZynthFinder Adapter.\n- Ensure dependencies are installed (e.g., rdkit, tensorflow)\n- Or check sys.path for plugin and source directories")
        print("Exception details:", repr(e))
        return

    adapter = Adapter()
    print(f"Adapter created, mode: {adapter.mode}")

    print("\n--- Available Adapter tools ---")
    adapter_methods = [m for m in dir(adapter) if not m.startswith('_') and callable(getattr(adapter, m))]
    print(f"{len(adapter_methods)} tools found:")
    for i, m in enumerate(adapter_methods, 1):
        print(f"  {i}. {m}")

    print("\n--- Tool documentation ---")
    for m in adapter_methods:
        fn = getattr(adapter, m)
        doc = fn.__doc__
        brief = (doc.strip().split('\n')[0] if doc and doc.strip() else "No description")
        print(f"- {m}: {brief}")

    print("\n--- Testing some tools (minimizing external dependencies) ---")

    try:
        res_policies = adapter.initialize_policies()
        print("Policies initialized:", res_policies.get("status"), res_policies.get("message"))
    except Exception as e:
        print("Failed to initialize Policies:", repr(e))

    try:
        res_scorers = adapter.initialize_scorers()
        print("Scorers initialized:", res_scorers.get("status"), res_scorers.get("message"))
    except Exception as e:
        print("Failed to initialize Scorers:", repr(e))

    try:
        res_exp = adapter.initialize_expansion_strategies()
        print("ExpansionStrategies initialized:", res_exp.get("status"), res_exp.get("message"))
    except Exception as e:
        print("Failed to initialize ExpansionStrategies:", repr(e))

    try:
        res_filter = adapter.initialize_filter_strategies()
        print("FilterStrategies initialized:", res_filter.get("status"), res_filter.get("message"))
    except Exception as e:
        print("Failed to initialize FilterStrategies:", repr(e))

    try:
        res_stock = adapter.initialize_stock()
        print("Stock initialized:", res_stock.get("status"), res_stock.get("message"))
    except Exception as e:
        print("Failed to initialize Stock:", repr(e))

    print("\n--- Demonstrating run_aizynthcli (requires real input/output) ---")
    try:
        demo_input = str(project_root / "demo_input.json")
        demo_output = str(project_root / "demo_output.json")
        res_cli = adapter.run_aizynthcli(demo_input, demo_output)
        print("CLI run result:", res_cli)
    except Exception as e:
        print("CLI run failed (demo environment may lack dependencies or input files):", repr(e))

    print("\n--- Demonstrating run_aizynthapp (GUI, usually not on headless servers) ---")
    try:
        res_gui = adapter.run_aizynthapp()
        print("GUI launch result:", res_gui)
    except Exception as e:
        print("GUI launch failed (environment may not support GUI):", repr(e))

    print("\n--- Instructions ---")
    print("1) For Python-only use, continue calling Adapter methods locally.")
    print("2) To expose as MCP tool, run the service entry points:")
    print("   -", mcp_agent_root / "workspace/aizynthfinder/mcp_output/start_mcp.py")
    print("   - or", aiz_mcp_plugin_dir / "main.py")
    print("3) run_aizynthcli requires valid input/config; GUI works only in graphical environments.")

if __name__ == "__main__":
    main()
