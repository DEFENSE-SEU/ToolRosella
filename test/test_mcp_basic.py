#!/usr/bin/env python3
"""
MCP服务基础测试脚本
测试目标：验证MCP服务的adapter.py能否成功导入和创建实例
用途：回归测试，确保Code2MCP改进不会破坏已有的成功case
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MCPBasicTester:
    """MCP服务基础测试器"""

    def __init__(self, registry_path: str = None):
        if registry_path is None:
            registry_path = Path(__file__).parent / "test_cases_registry.json"

        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

        self.results = {}

    def test_case_import(self, case_name: str, mcp_location: str) -> Dict[str, Any]:
        """
        测试单个case的adapter是否能导入

        返回:
            {
                "status": "pass" | "fail",
                "error": str (if failed),
                "methods_count": int (if passed),
                "methods_sample": list (if passed)
            }
        """
        print(f"\n{'='*60}")
        print(f"Testing: {case_name}")
        print(f"Location: {mcp_location}")
        print(f"{'='*60}")

        # 构造adapter路径
        adapter_path = Path(project_root) / mcp_location / "mcp_plugin"

        if not adapter_path.exists():
            error_msg = f"MCP plugin directory not found: {adapter_path}"
            print(f"❌ {error_msg}")
            return {"status": "fail", "error": error_msg}

        # 临时添加到路径
        sys.path.insert(0, str(adapter_path))

        try:
            # 尝试导入adapter
            print("  [1/3] Importing adapter module...", end=" ")
            from adapter import Adapter
            print("✅")

            # 尝试创建实例
            print("  [2/3] Creating Adapter instance...", end=" ")
            adapter = Adapter()
            print("✅")

            # 检查有哪些公开方法
            print("  [3/3] Checking public methods...", end=" ")
            methods = [m for m in dir(adapter) if not m.startswith('_') and callable(getattr(adapter, m))]
            print(f"✅ ({len(methods)} methods found)")

            # 显示前5个方法作为样本
            methods_sample = methods[:5]
            print(f"\n  Sample methods: {', '.join(methods_sample)}")
            if len(methods) > 5:
                print(f"  ... and {len(methods) - 5} more")

            result = {
                "status": "pass",
                "methods_count": len(methods),
                "methods_sample": methods_sample
            }

            print(f"\n  ✅ Test PASSED for {case_name}")
            return result

        except ImportError as e:
            error_msg = f"ImportError: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {"status": "fail", "error": error_msg, "error_type": "ImportError"}

        except SyntaxError as e:
            error_msg = f"SyntaxError in adapter.py: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {"status": "fail", "error": error_msg, "error_type": "SyntaxError"}

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {"status": "fail", "error": error_msg, "error_type": type(e).__name__}

        finally:
            # 清理路径
            if str(adapter_path) in sys.path:
                sys.path.remove(str(adapter_path))

    def test_golden_cases(self):
        """测试所有成功的golden cases"""
        golden_cases = [c for c in self.registry["cases"] if c["status"] == "success"]

        print("\n" + "="*60)
        print(f"GOLDEN CASES REGRESSION TEST")
        print(f"Testing {len(golden_cases)} cases that should always pass")
        print("="*60)

        for case in golden_cases:
            result = self.test_case_import(case["name"], case["mcp_location"])
            self.results[case["name"]] = result

        return self.results

    def test_fixed_cases(self):
        """测试已经手工修复的cases"""
        fixed_cases = [c for c in self.registry["cases"] if c["status"] == "fixed_manually"]

        print("\n" + "="*60)
        print(f"FIXED CASES TEST")
        print(f"Testing {len(fixed_cases)} manually fixed cases")
        print("="*60)

        for case in fixed_cases:
            result = self.test_case_import(case["name"], case["mcp_location"])
            self.results[case["name"]] = result

        return self.results

    def test_all_cases(self):
        """测试所有cases"""
        print("\n" + "="*60)
        print(f"COMPLETE TEST SUITE")
        print(f"Testing all {len(self.registry['cases'])} cases")
        print("="*60)

        for case in self.registry["cases"]:
            result = self.test_case_import(case["name"], case["mcp_location"])
            self.results[case["name"]] = result

        return self.results

    def print_summary(self):
        """打印测试摘要"""
        if not self.results:
            print("\nNo tests run yet.")
            return

        passed = [name for name, result in self.results.items() if result["status"] == "pass"]
        failed = [name for name, result in self.results.items() if result["status"] == "fail"]

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        print(f"\n✅ PASSED: {len(passed)}/{len(self.results)}")
        for name in passed:
            methods_count = self.results[name].get("methods_count", 0)
            print(f"  - {name} ({methods_count} methods)")

        if failed:
            print(f"\n❌ FAILED: {len(failed)}/{len(self.results)}")
            for name in failed:
                error_type = self.results[name].get("error_type", "Unknown")
                print(f"  - {name} ({error_type})")
                print(f"    Error: {self.results[name].get('error', 'Unknown error')[:100]}...")

        # 检查回归
        golden_cases = [c["name"] for c in self.registry["cases"] if c["status"] == "success"]
        golden_results = {name: self.results[name] for name in golden_cases if name in self.results}

        if golden_results:
            golden_passed = sum(1 for r in golden_results.values() if r["status"] == "pass")
            print(f"\n🎯 REGRESSION CHECK (Golden Cases):")
            if golden_passed == len(golden_results):
                print(f"  ✅ All {len(golden_results)} golden cases passed - No regression!")
            else:
                print(f"  ⚠️  WARNING: {len(golden_results) - golden_passed}/{len(golden_results)} golden cases failed!")
                print(f"  🚨 REGRESSION DETECTED - Code2MCP changes may have broken existing functionality")

        # 总体结论
        print(f"\n" + "="*60)
        if len(passed) == len(self.results):
            print("CONCLUSION: ✅ ALL TESTS PASSED")
            return 0
        elif failed:
            print(f"CONCLUSION: ⚠️  {len(failed)} TEST(S) FAILED")
            return 1

    def save_results(self, output_path: str = None):
        """保存测试结果到JSON"""
        if output_path is None:
            output_path = Path(__file__).parent / "test_results.json"

        import datetime
        output_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_cases": len(self.results),
            "passed": sum(1 for r in self.results.values() if r["status"] == "pass"),
            "failed": sum(1 for r in self.results.values() if r["status"] == "fail"),
            "results": self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved to: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Basic Test Suite")
    parser.add_argument(
        "--mode",
        choices=["golden", "fixed", "all"],
        default="all",
        help="Test mode: golden (success cases only), fixed (manually fixed cases), all (everything)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to test_results.json"
    )

    args = parser.parse_args()

    tester = MCPBasicTester()

    # 根据模式运行测试
    if args.mode == "golden":
        tester.test_golden_cases()
    elif args.mode == "fixed":
        tester.test_fixed_cases()
    else:
        tester.test_all_cases()

    # 打印摘要
    exit_code = tester.print_summary()

    # 保存结果
    if args.save:
        tester.save_results()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
