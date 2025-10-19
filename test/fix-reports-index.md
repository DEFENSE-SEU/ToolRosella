# Fix Reports Index

本目录索引了所有需要手工修复的MCP case的问题报告。

---

## 快速导航

| Case | 状态 | 主要问题 | 报告位置 | 问题数量 |
|------|------|----------|----------|----------|
| **obspy** | 已手工修复 | 功能识别不完整（仅30%），adapter与service脱节 | [case/obspy/fix_report/ISSUE_REPORT.md](../case/obspy/fix_report/ISSUE_REPORT.md) | 6大类问题 |
| **chemlib** | 已手工修复 | 导入不存在的函数，缺少数据加载 | [case/chemlib/chemlib.md](../case/chemlib/chemlib.md) | 3个主要问题 |
| **TenCirChem** | 已手工修复 | 错误的import，API使用错误 | [case/TenCirChem/TenCirChem.md](../case/TenCirChem/TenCirChem.md) | 5个import/API错误 |

---

## 问题类型统计（跨所有case）

基于现有的3个修复报告，问题分布如下：

### 1. Import错误（最常见）
- **频率**: 3/3 cases (100%)
- **典型问题**:
  - 导入不存在的类/函数（LLM幻觉）
  - 导入路径错误
  - 应该从子模块导入却从顶层导入
- **案例**:
  - chemlib: `from chemlib.chemistry import balance_equation` (不存在)
  - TenCirChem: `from tencirchem.static.hamiltonian import Hamiltonian` (应该用`get_h_from_hf`)
  - obspy: adapter.py有实现但mcp_service.py未导入

### 2. API理解错误（次常见）
- **频率**: 3/3 cases (100%)
- **典型问题**:
  - 使用了不存在的API
  - 调用方式错误
  - 参数类型错误
- **案例**:
  - TenCirChem: 期望`Molecule`类，实际应该用`pyscf.M`
  - chemlib: 调用不存在的`balance_equation()`函数
  - obspy: 只创建对象不调用操作方法

### 3. 功能暴露不完整
- **频率**: 1/3 cases (33%)
- **典型问题**:
  - adapter.py实现了功能但mcp_service.py未暴露
  - 只识别了部分核心功能
- **案例**:
  - obspy: adapter有20+方法，但mcp_service只暴露12个工具

### 4. 数据/配置缺失
- **频率**: 1/3 cases (33%)
- **典型问题**:
  - 未加载必要的数据文件
  - 未处理配置文件
- **案例**:
  - chemlib: 未读取`resources/thermochemistry.csv`

### 5. 语法错误
- **频率**: 见于code2mcp_refine.md
- **典型问题**:
  - try-except缩进错误
- **案例**:
  - SPM: try-except块缩进错误（已在refine文档中记录）

---

## Code2MCP改进优先级建议

基于问题频率，建议改进优先级：

### 🔥 Priority 1: Import路径和API识别（影响100% cases）
- **问题**: LLM经常导入不存在的函数/类
- **建议方案**:
  - 在生成代码后，扫描源码验证import有效性
  - 实现AST解析，识别真实可用的API
  - 参考：code2mcp_refine.md中描述的`code_check_node.py`逻辑

### 🔥 Priority 2: Adapter与Service联动（影响obspy等复杂库）
- **问题**: adapter.py实现了功能，但mcp_service.py未暴露
- **建议方案**:
  - 自动扫描adapter.py中的所有公开方法
  - 为每个方法生成对应的`@mcp.tool`
  - 或至少提示用户哪些adapter方法未被暴露

### ⚠️ Priority 3: 语法检查（避免低级错误）
- **问题**: 生成的代码有语法错误（缩进、括号等）
- **建议方案**:
  - 代码生成后运行`python -m py_compile`检查
  - 使用linter（如flake8）检查基本语法

### 💡 Priority 4: 数据文件识别（提升完整性）
- **问题**: 未识别项目依赖的数据文件
- **建议方案**:
  - 扫描`resources/`, `data/`等目录
  - 在adapter中添加数据加载逻辑

---

## 测试建议

### 回归测试（每次Code2MCP改进后必做）
```bash
# 测试2个golden cases，确保不引入regression
python test/test_mcp_basic.py --mode=golden

# 预期：2/2 passed
```

### 修复验证测试
```bash
# 测试3个已修复的cases，看Code2MCP改进是否解决了问题
python test/test_mcp_basic.py --mode=fixed

# 理想情况：从人工修复 → Code2MCP自动生成正确代码
```

### 完整测试
```bash
# 测试所有5个cases
python test/test_mcp_basic.py --mode=all --save

# 生成完整报告到test_results.json
```

---

## 各Case详细报告

### 1. ObsPy - 地震学数据处理库

**主要问题**: 功能识别不完整

**详细报告**: [case/obspy/fix_report/ISSUE_REPORT.md](../case/obspy/fix_report/ISSUE_REPORT.md)

**核心发现**:
- Code2MCP只暴露了30%的核心功能
- adapter.py已实现的功能未在mcp_service.py中暴露
- 缺少最重要的工作流功能：数据I/O、信号处理、FDSN客户端

**修复工作量**: 需要在mcp_service.py中新增约20个`@mcp.tool`

---

### 2. ChemLib - 化学计算库

**主要问题**: 导入不存在的函数，数据加载缺失

**详细报告**: [case/chemlib/chemlib.md](../case/chemlib/chemlib.md)

**核心发现**:
- 尝试导入不存在的`balance_equation`等函数
- 未读取必要的CSV数据文件（thermochemistry.csv）
- 未处理化学式的相态格式（如H2O(l)）

**修复工作量**: 修改mcp_service.py约5处import + 添加数据加载逻辑

---

### 3. TenCirChem - 量子化学计算库

**主要问题**: 错误的API调用

**详细报告**: [case/TenCirChem/TenCirChem.md](../case/TenCirChem/TenCirChem.md)

**核心发现**:
- 5个主要的import错误（Hamiltonian、Molecule、Optimizer等）
- 应该使用PySCF的API但错误地使用了TenCirChem自定义类
- FastMCP不支持callable类型参数

**修复工作量**: 修改mcp_service.py约5处import + API调用逻辑

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2025-10-19 | 创建fix-reports索引，汇总3个case的问题 |
| - | 统计问题类型分布，提出改进建议 |

---

**维护者**: 请在每次Code2MCP改进后更新此索引，标注哪些问题已被自动修复
