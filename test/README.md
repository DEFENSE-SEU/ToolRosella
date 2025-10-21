# Code2MCP 测试系统

Code2MCP测试框架，用于验证新版本改进和防止回归。

## 快速开始（3步）

```bash
# 1. 环境检查
python test/check_env.py

# 2. 配置API密钥（如需要）
# 编辑 Code2MCP-latest/.env，参考 test/SETUP_BEFORE_TESTING.md

# 3. 运行测试
python test/test_new_code2mcp.py --quick  # 快速测试（10-15分钟）
python test/test_new_code2mcp.py --all    # 完整测试（50-75分钟）
```

---

## 测试脚本对比

| 脚本 | 功能 | 耗时 | 使用场景 |
|------|------|------|----------|
| `test_new_code2mcp.py` | 端到端测试（Code2MCP转换+MCP测试） | 10-15分钟/case | **测试新版Code2MCP** |
| `test_mcp_basic.py` | 快速导入测试（已有MCP输出） | <1秒/case | 回归测试 |
| `test_mcp_service.py` | MCP服务层深度测试 | 1-2秒/case | 调试mcp_service.py |
| `check_env.py` | 环境验证 | <1秒 | 首次使用/排查问题 |

### 常用命令

```bash
# 测试新版Code2MCP
python test/test_new_code2mcp.py --all         # 所有cases
python test/test_new_code2mcp.py --quick       # 只测golden case
python test/test_new_code2mcp.py --case SPM    # 特定case

# 快速回归测试（不运行Code2MCP）
python test/test_mcp_basic.py --mode=golden    # 测试应该成功的cases
python test/test_mcp_basic.py --mode=all       # 测试所有cases
```

---

## 理解测试结果

测试完成后会自动判断是否接受新版本：

| 结果 | 建议 | 说明 |
|------|------|------|
| ✅ **Fixed cases** | **接受** | 之前失败的case现在通过了 |
| ✅ **All maintained** | 接受 | 没有regression，保持现状 |
| ❌ **Regression** | **拒绝** | 之前通过的case现在失败了 |
| ⚠️ **Still failing** | 视情况 | 没有改进，也没有regression |

### 测试输出示例

```
CODE2MCP-LATEST TEST SUMMARY
============================================================

📊 Overall Statistics:
  Total cases tested: 5
  Code2MCP execution success: 5/5
  MCP tests passed: 4/5

🎯 Comparison with Old Version:
  ✅ Fixed: 1
     - sympy
  ✅ Maintained: 3
     - SPM, obspy, chemlib
  ❌ Regression: 0
  ❌ Still failing: 1
     - TenCirChem

============================================================
✅ IMPROVEMENT DETECTED!
   1 case(s) fixed, 1 case(s) still need work
   ✅ This Code2MCP version can be accepted
```

---

## 典型工作流

### 场景1：测试新版Code2MCP（最常用）

```bash
# Step 1: 快速测试（验证无regression）
python test/test_new_code2mcp.py --quick

# Step 2: 完整测试（如果quick通过）
python test/test_new_code2mcp.py --all

# Step 3: 查看结果决定是否接受
# - 如果有Fixed → 接受 ✅
# - 如果有Regression → 拒绝 ❌
```

### 场景2：调试单个case

```bash
# 重新生成并测试单个case
python test/test_new_code2mcp.py --case sympy

# 查看生成的文件
ls test/test_workspace/workspace/sympy/mcp_output/mcp_plugin/

# 手工测试
cd test/test_workspace/workspace/sympy/mcp_output/mcp_plugin/
python -c "from mcp_service import create_app; print(create_app())"
```

### 场景3：快速回归测试

```bash
# 不运行Code2MCP，只测试已有的MCP输出
python test/test_mcp_basic.py --mode=golden

# 如果失败 → 说明case目录被修改了
```

---

## 文件组织（重要）

**测试不会污染Code2MCP-latest目录！**

所有测试文件都隔离在test/目录下：

```
Easy-Tool/
├── Code2MCP-latest/
│   ├── main.py
│   └── .env                    ← 只需配置这个文件
│
└── test/
    ├── test_workspace/          ← MCP生成的输出（git忽略）
    │   └── workspace/           ← Code2MCP输出重定向到这里
    └── test_output/             ← 测试结果JSON（git忽略）
        └── code2mcp_test_*.json
```

### 清理测试文件

```bash
# 删除所有测试生成的文件
rm -rf test/test_workspace/ test/test_output/

# Code2MCP-latest不受影响
```

详细说明：[FILE_FLOW_DIAGRAM.md](FILE_FLOW_DIAGRAM.md)

---

## 测试用例注册表

所有测试用例在 `test_cases_registry.json` 中定义：

```json
{
  "cases": [
    {
      "name": "SPM",
      "status": "success",           // success | fixed_manually | failed
      "repo_url": "https://github.com/DEFENSE-SEU/SPM",
      "mcp_location": "case/SPM/SPM/mcp_output"
    }
  ]
}
```

当前状态（更新时间：2025-10-21）：
- **Success**: 1/5 (SPM)
- **Fixed manually**: 3/5 (obspy, chemlib, TenCirChem)
- **Failed**: 1/5 (sympy)

---

## 常见问题

### Q: 为什么测试这么慢？
**A**: Code2MCP需要调用LLM API分析代码（每个case约10-15分钟）。使用`--quick`只测试1个case。

### Q: 测试后Code2MCP-latest变乱了？
**A**: 不应该！所有测试文件都在`test/test_workspace/`。如果Code2MCP-latest有新文件，说明有bug。

### Q: .env文件配置在哪里？
**A**: 必须在`Code2MCP-latest/.env`。虽然输出重定向，但Code2MCP运行时需要从自己的目录读取配置。

详细配置：[SETUP_BEFORE_TESTING.md](SETUP_BEFORE_TESTING.md)

### Q: 如何判断是否接受新版本？
**A**:
- 最低要求：无regression
- 改进指标：Fixed cases增加
- 理想状态：所有cases自动通过

### Q: 测试覆盖了什么？
**A**:
- ✅ Code2MCP执行成功
- ✅ 语法正确性（import）
- ✅ 基本可用性（实例化）
- ✅ MCP服务层（create_app）
- ⏳ 功能正确性（未来可扩展）

---

## 文档索引

| 文档 | 用途 |
|------|------|
| [README.md](README.md) | 本文件（总览） |
| [QUICK_START.md](QUICK_START.md) | 5步快速参考 |
| [SETUP_BEFORE_TESTING.md](SETUP_BEFORE_TESTING.md) | 环境配置详细指南 |
| [FILE_FLOW_DIAGRAM.md](FILE_FLOW_DIAGRAM.md) | 可视化文件流向 |
| [fix-reports-index.md](fix-reports-index.md) | 已知问题汇总 |

---

## 目录结构

```
test/
├── README.md                          # 本文件
├── QUICK_START.md                     # 快速参考
├── SETUP_BEFORE_TESTING.md            # 配置指南
├── FILE_FLOW_DIAGRAM.md               # 文件流向图
│
├── test_cases_registry.json           # 测试用例注册表
│
├── test_new_code2mcp.py              # 主测试脚本
├── test_mcp_basic.py                 # 快速测试
├── test_mcp_service.py               # 服务层测试
├── check_env.py                      # 环境检查
│
├── fix-report-template.md            # 问题报告模板
├── fix-reports-index.md              # 问题汇总
│
├── test_workspace/                    # 测试工作空间（git忽略）
└── test_output/                       # 测试结果（git忽略）
```

---

**最后更新**: 2025-10-21
