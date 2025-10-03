## 可以在write code后先不测试，首先加一个代码检查的功能

例如 **Adapter.py** 多次出现代码格式错误, adapter.py 文件报错 “invalid syntax”, 问题在**缩进错误**

```python

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

```

关键代码部分:

```python

for script in scripts:
    try:
        result = subprocess.run(script, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return {"result": f"Script {script} executed successfully", "status": "success"}
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as script_error:
    print(f"Script execution failed {script}: {script_error}")
    continue


```

try-expert部分缩紧错误


