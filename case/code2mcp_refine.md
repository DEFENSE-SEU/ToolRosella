## 可以在write code后先不测试，首先加一个代码检查的功能

1. 例如 **Adapter.py** 多次出现代码格式错误, adapter.py 文件报错 “invalid syntax”, 问题在**缩进错误**

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

try-except 缩进错误，可以设计一个agent检查一下代码格式问题

---

2. mcp_service.py 基本上都会出现不存在的类导入

例如

```python
from scripts.SequencePatternMatching import SequencePatternMatching
spm = SequencePatternMatching()
result = spm.match(input_sequence, target_sequence)
```

问题原因: 原始SPM源码中没有 SequencePatternMatching 类，只有函数。

需要修改

```python
from scripts.SequencePatternMatching import volumeScoring, volume
result_data = volumeScoring(query_seq_volume, uniprot_info, target_sequence)
```

所以这个可以检查一个源码具体实现的py文件和mcp_service.py导入source写的方法时做一个检查


