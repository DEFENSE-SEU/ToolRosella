import json
import subprocess
import os
import sys
from typing import Dict, Any

source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "source")
sys.path.insert(0, source_path)

class Adapter:
    """Blackbox mode adapter"""
    
    def __init__(self):
        self.mode = "blackbox"
    
    def core(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Blackbox mode core function"""
        try:
            scripts = [
                ["python", "main.py"],
                ["python", "-m", "pytest", "--help"],
                ["python", "setup.py", "test"]
            ]
            
            for script in scripts:
                try:
                    result = subprocess.run(script, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return {"result": f"Script {script} executed successfully", "status": "success"}
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as script_error:
                    print(f"Script execution failed {script}: {script_error}")
                    continue
            
            return {"result": "no_executable_script_found", "status": "warning"}
        except Exception as e:
            return {"error": str(e), "status": "error"}