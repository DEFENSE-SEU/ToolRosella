## 可以在write code后先不测试，首先加一个代码检查的功能

1. 例如 遇到多次code2mcp后 **Adapter.py** 出现代码格式错误, adapter.py 文件报错 “invalid syntax”, 问题在**缩进错误**

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

**try-except 缩进错误，可以设计一个agent检查一下代码格式问题**

---

2. code2mcp后，mcp_service.py 基本上都会出现不存在的类，方法导入，可能是LLM出现写代码的幻觉（喜欢自我发挥）

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

还有存在尝试调用不存在的方法 spm.match()，目前需要手动去source文件中查找，

```python
result = spm.match(input_sequence, target_sequence)
```

**修复:** 直接调用真实的 SPM 算法函数 volumeScoring()。

```python
result_data = volumeScoring(query_seq_volume, uniprot_info, target_sequence)
```

**所以这个可以重新学习一下源码（source）具体实现的py文件，然后对mcp_service.py导入source实现的方法时做一个检查，来修改mcp_service.py出现虚幻的代码**

----

src/node/code_check_node.py代码，当发现 import error 时，系统会通过以下步骤查找正确的 import：

## 查找流程

### 1. **扫描源代码目录** (`_scan_source_directory`)
```python
source_dir = os.path.join(repo_root, "source")
```
- 遍历 `source/` 目录下的所有 Python 文件
- 提取每个文件中的公共函数和类
- 构建 `available_symbols` 字典，记录每个模块的可用符号

### 2. **检查 import 有效性** (`_check_import_validity`)
- 提取生成代码中的所有 import 语句
- 对比 `available_symbols`，查找：
  - 模块是否存在
  - 导入的函数/类是否在该模块中

### 3. **读取源代码文件** (`_read_source_files_for_module`)
当发现错误时，会读取实际的源代码：
```python
# 尝试两个路径：
file_path = os.path.join(source_dir, module_path.replace('.', os.sep) + '.py')
init_path = os.path.join(source_dir, module_path.replace('.', os.sep), '__init__.py')
```

### 4. **智能修复** (`_learn_from_source_and_fix`)
这是核心修复逻辑：

1. **读取源代码**：找到错误模块的实际源文件
2. **解析源代码**：使用 AST 提取函数签名、类定义
3. **分析函数用途**：调用 LLM 分析每个函数的目的、参数、返回值
4. **提供完整上下文给 LLM**：
   - 错误信息
   - 源代码片段
   - 函数分析结果
   - 所有可用的符号列表

5. **LLM 重写代码**：基于源代码分析结果，重新生成正确的 import 语句和代码

## 示例

如果代码尝试 `from my_module import NonExistentFunction`：

1. ✅ 扫描找到 `source/my_module.py` 中有 `actual_function()`
2. ❌ 检测到 `NonExistentFunction` 不存在
3. 📖 读取 `source/my_module.py` 的完整源代码
4. 🔍 使用 LLM 分析 `actual_function()` 的用途
5. 🤖 LLM 基于分析结果重写 import，改为正确的函数名

## 关键

- **不是简单的字符串匹配**，而是理解源代码的语义
- **LLM 分析函数用途**，确保生成的代码在逻辑上也是正确的
- **提供完整上下文**，包括函数签名、文档字符串和用途分析
