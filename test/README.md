# MCP测试系统

本目录包含用于测试Code2MCP生成的MCP服务的测试框架和工具。

---

## 📁 目录结构

```
test/
├── README.md                      # 本文件
├── test_cases_registry.json       # 所有测试用例的注册表
├── test_mcp_basic.py             # 基础测试脚本（import + 实例化）
├── fix-report-template.md        # 修复报告模板
├── fix-reports-index.md          # 所有修复报告的索引和统计
└── test_results.json             # 测试结果（运行后生成）
```

---

## 🚀 快速开始

### 1. 运行回归测试（最常用）

每次Code2MCP改进后，先跑这个确保没有破坏已有功能：

```bash
cd /Users/yuanxujie/Downloads/Easy-Tool
python test/test_mcp_basic.py --mode=golden
```

**预期输出**:
```
Golden cases: 2/2 passed ✅
- sympy (75 methods)
- SPM (X methods)

REGRESSION CHECK: ✅ No regression detected
```

如果出现失败，说明Code2MCP的改进破坏了之前成功的case！

---

### 2. 测试修复效果

验证Code2MCP的改进是否解决了已知问题：

```bash
python test/test_mcp_basic.py --mode=fixed
```

**目标**: 看3个手工修复的case（obspy、chemlib、TenCirChem）是否现在能自动通过

**成功标准**:
- 如果仍然失败 → Code2MCP还未解决该问题
- 如果通过 → Code2MCP成功修复！可以移入golden cases

---

### 3. 完整测试（定期运行）

```bash
python test/test_mcp_basic.py --mode=all --save
```

这会：
- 测试所有5个cases
- 生成详细报告到`test_results.json`
- 可用于追踪长期改进趋势

---

## 📊 测试用例管理

### test_cases_registry.json 结构

```json
{
  "cases": [
    {
      "name": "sympy",
      "status": "success",           // success | fixed_manually | failed
      "repo_url": "...",
      "mcp_location": "case/sympy/mcp_output",
      "test_query": "...",
      "manual_fixes_needed": false,
      "known_issues": [],
      "fix_report_location": "..."
    }
  ]
}
```

### 如何添加新case

1. 在`case/`目录下添加新的转换结果
2. 在`test_cases_registry.json`中添加条目：

```json
{
  "name": "new_case",
  "status": "success",  // 或 "failed"
  "repo_url": "https://github.com/...",
  "mcp_location": "case/new_case/mcp_output",
  "test_query": "测试这个case的查询",
  "manual_fixes_needed": false
}
```

3. 运行测试验证：
```bash
python test/test_mcp_basic.py --mode=all
```

---

## 📝 问题报告流程

### 当发现新问题时

1. **记录问题**：根据`fix-report-template.md`创建报告
2. **更新registry**：在`test_cases_registry.json`中标记case状态
3. **手工修复**（如需要）：修改mcp_output中的代码
4. **记录修复**：在fix-report中详细说明修改内容
5. **提交给Code2MCP开发者**：将报告发送给他们

### 报告内容应包括

- 错误类型（ImportError / SyntaxError / LogicError等）
- 完整错误信息
- 问题原因分析
- 手工修改的具体内容（diff格式）
- 给Code2MCP的改进建议

参考：[fix-reports-index.md](fix-reports-index.md)

---

## 🎯 测试级别说明

当前实现的是 **Level 1-2** 测试：

### ✅ Level 1: 语法正确性（已实现）
- MCP服务代码能否成功导入？
- adapter.py语法是否正确？

### ✅ Level 2: 基本可用性（已实现）
- Adapter实例能否创建？
- 有哪些公开方法？

### ⏳ Level 3: 功能正确性（待实现）
- 工具调用是否返回正确结果？
- 是否能真正解决原始query？

**未来扩展**: 可以为每个case编写功能测试用例

---

## 📈 测试结果解读

### 示例输出

```
=============================================================
GOLDEN CASES REGRESSION TEST
Testing 2 cases that should always pass
=============================================================

Testing: sympy
✅ Test PASSED for sympy

Testing: SPM
✅ Test PASSED for SPM

=============================================================
TEST SUMMARY
=============================================================

✅ PASSED: 2/2
  - sympy (75 methods)
  - SPM (12 methods)

🎯 REGRESSION CHECK (Golden Cases):
  ✅ All 2 golden cases passed - No regression!

CONCLUSION: ✅ ALL TESTS PASSED
```

### 如果出现regression

```
❌ FAILED: 1/2
  - sympy (ImportError)
    Error: ModuleNotFoundError: No module named 'mpmath'

🎯 REGRESSION CHECK (Golden Cases):
  ⚠️  WARNING: 1/2 golden cases failed!
  🚨 REGRESSION DETECTED - Code2MCP changes may have broken existing functionality
```

**行动**: 立即通知Code2MCP开发者，不要合并这次改进！

---

## 🔄 典型工作流

### Code2MCP开发者改进后的测试流程

```bash
# Step 1: 快速回归测试（30秒）
python test/test_mcp_basic.py --mode=golden

# 如果通过 ✅ → 继续
# 如果失败 ❌ → 回滚改进，调试

# Step 2: 测试修复效果（1分钟）
python test/test_mcp_basic.py --mode=fixed

# 检查有多少之前失败的case现在通过了
# 记录改进效果：如 "3个fixing cases中2个已修复"

# Step 3: 完整测试 + 保存结果（2分钟）
python test/test_mcp_basic.py --mode=all --save

# 生成报告，对比历史趋势
```

### 追踪改进进度

创建一个改进日志：

| 日期 | Code2MCP版本 | Golden通过率 | Fixed通过率 | 总通过率 | 备注 |
|------|--------------|--------------|-------------|----------|------|
| 2025-10-15 | v0.3.1 | 2/2 | 0/3 | 2/5 | 初始状态 |
| 2025-10-20 | v0.3.2 | 2/2 | 1/3 | 3/5 | 修复了chemlib的import |
| 2025-10-25 | v0.3.3 | 2/2 | 2/3 | 4/5 | 修复了TenCirChem |
| 目标 | v1.0.0 | 5/5 | - | 5/5 | 所有case自动通过 |

---

## 🛠️ 扩展测试系统

### 添加功能测试（未来）

为特定case添加语义测试：

```python
# test/test_mcp_functional.py
def test_sympy_solve_equation():
    """测试sympy能否真正求解方程"""
    from adapter import Adapter
    adapter = Adapter()
    result = adapter.solve_equation("x**2 + 2*x + 1 = 0")
    assert result == {"solution": "x = -1"}  # 验证语义正确性
```

### 添加性能测试

```python
def test_performance():
    """测试MCP服务的响应时间"""
    import time
    start = time.time()
    adapter.some_method()
    elapsed = time.time() - start
    assert elapsed < 5.0  # 确保5秒内完成
```

---

## 📚 相关文档

- **Fix Reports索引**: [fix-reports-index.md](fix-reports-index.md)
- **问题模板**: [fix-report-template.md](fix-report-template.md)
- **Code2MCP改进建议**: [../case/code2mcp_refine.md](../case/code2mcp_refine.md)
- **ObsPy详细报告**: [../case/obspy/fix_report/ISSUE_REPORT.md](../case/obspy/fix_report/ISSUE_REPORT.md)

---

## ❓ FAQ

### Q: 测试失败了怎么办？
A:
1. 查看错误类型（ImportError / SyntaxError等）
2. 检查是golden case还是fixing case
3. 如果是golden case失败 → 回归！立即调查
4. 如果是fixing case失败 → 正常，这些本来就需要修复

### Q: 如何判断Code2MCP改进是否成功？
A:
- **最低要求**: Golden cases全部通过（无regression）
- **改进指标**: Fixed cases通过率提升
- **理想目标**: 所有cases都能自动通过，无需人工修复

### Q: 为什么只测试import，不测试功能？
A:
- Level 1-2测试快速（几秒），适合频繁运行
- 大部分问题在import阶段就能发现
- 功能测试需要为每个case编写expected output，工作量大
- 未来可以逐步添加功能测试

---

**维护者**: 请在每次测试框架更新后同步更新本README
**最后更新**: 2025-10-19
