#!/usr/bin/env python3
"""
测试新版Code2MCP的完整流程脚本

功能：
1. 用Code2MCP-latest重新转换所有GitHub仓库
2. 测试新生成的MCP服务是否可用
3. 对比新旧版本的差异
4. 生成详细的测试报告

使用方法：
    python test/test_new_code2mcp.py --all              # 测试所有cases
    python test/test_new_code2mcp.py --case SPM         # 只测试指定case
    python test/test_new_code2mcp.py --quick            # 只测试golden case
"""

import sys
import json
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Code2MCPTester:
    """Code2MCP新版本测试器"""

    def __init__(self, code2mcp_path: str = "Code2MCP-latest"):
        self.code2mcp_path = Path(project_root) / code2mcp_path

        # 使用独立的测试工作空间，不污染Code2MCP-latest
        self.test_workspace_dir = Path(project_root) / "test" / "test_workspace"
        self.test_workspace_dir.mkdir(exist_ok=True)

        # 在测试工作空间下创建子目录
        self.output_dir = self.test_workspace_dir / "workspace"
        self.output_dir.mkdir(exist_ok=True)

        # 测试结果保存目录
        self.test_output_dir = Path(project_root) / "test" / "test_output"
        self.test_output_dir.mkdir(exist_ok=True)

        # 加载测试用例注册表
        registry_path = Path(project_root) / "test" / "test_cases_registry.json"
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

        self.results = {}

    def run_code2mcp(self, repo_url: str, case_name: str) -> Tuple[bool, str]:
        """
        运行Code2MCP转换单个仓库

        返回: (是否成功, 错误信息)
        """
        print(f"\n{'='*60}")
        print(f"Running Code2MCP for: {case_name}")
        print(f"Repository: {repo_url}")
        print(f"{'='*60}")

        try:
            # 使用独立的输出目录，避免污染Code2MCP-latest
            output_path = self.test_workspace_dir / "output"
            output_path.mkdir(exist_ok=True)

            # 设置环境变量，让Code2MCP使用测试工作空间
            env = os.environ.copy()
            env['CODE2MCP_WORKSPACE'] = str(self.test_workspace_dir / "workspace")

            cmd = [
                sys.executable,
                "main.py",
                repo_url,
                "--output", str(output_path)
            ]

            print(f"Command: {' '.join(cmd)}")
            print(f"Working directory: {self.code2mcp_path}")
            print(f"Test workspace: {self.test_workspace_dir}")
            print("Running... (this may take 5-15 minutes)")

            # 运行Code2MCP
            result = subprocess.run(
                cmd,
                cwd=str(self.code2mcp_path),
                capture_output=True,
                text=True,
                timeout=900,  # 15分钟超时
                env=env  # 使用自定义环境变量
            )

            if result.returncode == 0:
                print("✅ Code2MCP execution completed successfully")
                return True, ""
            else:
                error_msg = f"Code2MCP failed with return code {result.returncode}\n"
                error_msg += f"STDERR: {result.stderr[-500:]}"  # 最后500字符
                print(f"❌ {error_msg}")
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "Code2MCP execution timeout (>15 minutes)"
            print(f"❌ {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"Exception during Code2MCP execution: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def test_generated_mcp(self, case_name: str, test_mcp_service: bool = True) -> Dict:
        """
        测试生成的MCP服务

        参数:
            test_mcp_service: 是否测试mcp_service.py层（推荐开启）

        返回测试结果字典
        """
        print(f"\n{'='*60}")
        print(f"Testing generated MCP: {case_name}")
        print(f"{'='*60}")

        # 查找生成的mcp_output目录
        workspace_case_dir = self.output_dir / case_name

        if not workspace_case_dir.exists():
            print(f"❌ Workspace directory not found: {workspace_case_dir}")
            return {
                "status": "fail",
                "error": "Workspace directory not found",
                "error_type": "DirectoryNotFound"
            }

        # 查找mcp_output
        mcp_output = workspace_case_dir / "mcp_output"
        if not mcp_output.exists():
            print(f"❌ mcp_output directory not found: {mcp_output}")
            return {
                "status": "fail",
                "error": "mcp_output directory not found",
                "error_type": "DirectoryNotFound"
            }

        # 测试adapter.py
        adapter_path = mcp_output / "mcp_plugin"

        if not adapter_path.exists():
            print(f"❌ mcp_plugin directory not found: {adapter_path}")
            return {
                "status": "fail",
                "error": "mcp_plugin directory not found",
                "error_type": "DirectoryNotFound"
            }

        # 临时添加到路径
        sys.path.insert(0, str(adapter_path))

        result = {}

        try:
            # 测试1: Adapter层
            print("\n  --- Testing Adapter Layer ---")
            print("  [1/3] Importing adapter module...", end=" ")
            from adapter import Adapter
            print("✅")

            print("  [2/3] Creating Adapter instance...", end=" ")
            adapter = Adapter()
            print("✅")

            print("  [3/3] Checking public methods...", end=" ")
            methods = [m for m in dir(adapter) if not m.startswith('_') and callable(getattr(adapter, m))]
            print(f"✅ ({len(methods)} methods)")

            result["adapter_status"] = "pass"
            result["methods_count"] = len(methods)
            result["methods_sample"] = methods[:5]

            # 测试2: MCP Service层（如果启用）
            if test_mcp_service:
                print("\n  --- Testing MCP Service Layer ---")
                print("  [1/3] Importing mcp_service module...", end=" ")

                try:
                    import mcp_service
                    print("✅")

                    print("  [2/3] Checking create_app function...", end=" ")
                    if not hasattr(mcp_service, 'create_app'):
                        print("❌")
                        result["mcp_service_status"] = "fail"
                        result["mcp_service_error"] = "create_app function not found"
                    else:
                        print("✅")

                        print("  [3/3] Creating MCP app instance...", end=" ")
                        app = mcp_service.create_app()
                        if app is None:
                            print("❌")
                            result["mcp_service_status"] = "fail"
                            result["mcp_service_error"] = "create_app returned None"
                        else:
                            print("✅")

                            # 尝试获取工具数量
                            try:
                                tools_count = 0
                                if hasattr(app, 'list_tools'):
                                    tools_count = len(app.list_tools())
                                elif hasattr(app, '_tools'):
                                    tools_count = len(app._tools)

                                result["mcp_service_status"] = "pass"
                                result["mcp_tools_count"] = tools_count
                            except:
                                result["mcp_service_status"] = "pass"
                                result["mcp_tools_count"] = "unknown"

                except ImportError as e:
                    print(f"❌ ({e})")
                    result["mcp_service_status"] = "fail"
                    result["mcp_service_error"] = f"ImportError: {str(e)}"

                except Exception as e:
                    print(f"❌ ({type(e).__name__}: {e})")
                    result["mcp_service_status"] = "fail"
                    result["mcp_service_error"] = f"{type(e).__name__}: {str(e)}"

            # 综合判断
            if result.get("adapter_status") == "pass":
                if test_mcp_service:
                    result["status"] = result.get("mcp_service_status", "unknown")
                else:
                    result["status"] = "pass"
            else:
                result["status"] = "fail"

            result["mcp_output_path"] = str(mcp_output)

            print(f"\n  {'✅' if result['status'] == 'pass' else '❌'} Overall test {'PASSED' if result['status'] == 'pass' else 'FAILED'} for {case_name}")

            return result

        except ImportError as e:
            error_msg = f"ImportError: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": "ImportError"
            }

        except SyntaxError as e:
            error_msg = f"SyntaxError: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": "SyntaxError"
            }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": type(e).__name__
            }

        finally:
            # 清理路径和导入
            if str(adapter_path) in sys.path:
                sys.path.remove(str(adapter_path))

            # 清理导入的模块
            for module in ['adapter', 'mcp_service']:
                if module in sys.modules:
                    del sys.modules[module]

    def compare_with_old_version(self, case_name: str, new_result: Dict) -> Dict:
        """
        对比新旧版本的测试结果

        返回对比结果
        """
        # 读取旧版本测试结果
        old_results_path = Path(project_root) / "test" / "test_results.json"

        if not old_results_path.exists():
            return {
                "comparison": "no_baseline",
                "message": "No baseline test results found"
            }

        with open(old_results_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        old_result = old_data.get('results', {}).get(case_name, {})
        old_status = old_result.get('status', 'unknown')
        new_status = new_result.get('status', 'unknown')

        comparison = {
            "old_status": old_status,
            "new_status": new_status,
            "comparison": "",
            "message": ""
        }

        if old_status == "pass" and new_status == "pass":
            comparison["comparison"] = "maintained"
            comparison["message"] = "✅ Maintained success"
        elif old_status == "fail" and new_status == "pass":
            comparison["comparison"] = "fixed"
            comparison["message"] = "✅✅✅ FIXED! Was failing, now passing"
        elif old_status == "pass" and new_status == "fail":
            comparison["comparison"] = "regression"
            comparison["message"] = "❌❌❌ REGRESSION! Was passing, now failing"
        elif old_status == "fail" and new_status == "fail":
            comparison["comparison"] = "still_failing"
            comparison["message"] = "❌ Still failing (not fixed yet)"
        else:
            comparison["comparison"] = "unknown"
            comparison["message"] = f"⚠️  Status changed: {old_status} → {new_status}"

        return comparison

    def test_case(self, case_name: str, repo_url: str) -> Dict:
        """
        测试单个case的完整流程

        返回完整测试结果
        """
        result = {
            "case_name": case_name,
            "repo_url": repo_url,
            "timestamp": datetime.now().isoformat(),
            "code2mcp_success": False,
            "test_result": {},
            "comparison": {}
        }

        # Step 1: 运行Code2MCP
        success, error = self.run_code2mcp(repo_url, case_name)
        result["code2mcp_success"] = success

        if not success:
            result["code2mcp_error"] = error
            result["test_result"] = {
                "status": "fail",
                "error": f"Code2MCP execution failed: {error}",
                "error_type": "Code2MCPError"
            }
            return result

        # Step 2: 测试生成的MCP
        test_result = self.test_generated_mcp(case_name)
        result["test_result"] = test_result

        # Step 3: 对比新旧版本
        comparison = self.compare_with_old_version(case_name, test_result)
        result["comparison"] = comparison

        return result

    def test_all_cases(self, case_names: List[str] = None):
        """测试所有或指定的cases"""
        if case_names is None:
            cases = self.registry["cases"]
        else:
            cases = [c for c in self.registry["cases"] if c["name"] in case_names]

        print(f"\n{'='*60}")
        print(f"TESTING CODE2MCP-LATEST")
        print(f"Total cases to test: {len(cases)}")
        print(f"{'='*60}")

        for case in cases:
            result = self.test_case(case["name"], case["repo_url"])
            self.results[case["name"]] = result

            # 打印对比结果
            print(f"\n{case['name']}: {result['comparison'].get('message', 'N/A')}")

        return self.results

    def print_summary(self):
        """打印测试摘要"""
        if not self.results:
            print("\nNo tests run yet.")
            return

        print("\n" + "="*60)
        print("CODE2MCP-LATEST TEST SUMMARY")
        print("="*60)

        # 统计
        total = len(self.results)
        code2mcp_success = sum(1 for r in self.results.values() if r["code2mcp_success"])
        test_passed = sum(1 for r in self.results.values() if r["test_result"].get("status") == "pass")

        fixed = [name for name, r in self.results.items() if r["comparison"].get("comparison") == "fixed"]
        regression = [name for name, r in self.results.items() if r["comparison"].get("comparison") == "regression"]
        maintained = [name for name, r in self.results.items() if r["comparison"].get("comparison") == "maintained"]
        still_failing = [name for name, r in self.results.items() if r["comparison"].get("comparison") == "still_failing"]

        print(f"\n📊 Overall Statistics:")
        print(f"  Total cases tested: {total}")
        print(f"  Code2MCP execution success: {code2mcp_success}/{total}")
        print(f"  MCP tests passed: {test_passed}/{total}")

        print(f"\n🎯 Comparison with Old Version:")
        print(f"  ✅ Fixed (was failing, now passing): {len(fixed)}")
        if fixed:
            for name in fixed:
                print(f"     - {name}")

        print(f"  ✅ Maintained (was passing, still passing): {len(maintained)}")
        if maintained:
            for name in maintained:
                print(f"     - {name}")

        print(f"  ❌ Regression (was passing, now failing): {len(regression)}")
        if regression:
            for name in regression:
                print(f"     - {name}")

        print(f"  ❌ Still failing (was failing, still failing): {len(still_failing)}")
        if still_failing:
            for name in still_failing:
                print(f"     - {name}")

        # 结论
        print(f"\n" + "="*60)
        if regression:
            print("🚨 CRITICAL: REGRESSION DETECTED!")
            print(f"   {len(regression)} case(s) that were passing are now failing")
            print("   ❌ DO NOT accept this Code2MCP version!")
            return 1
        elif fixed:
            print("✅ IMPROVEMENT DETECTED!")
            print(f"   {len(fixed)} case(s) fixed")
            if still_failing:
                print(f"   {len(still_failing)} case(s) still need work")
            print("   ✅ This Code2MCP version can be accepted")
            return 0
        elif maintained and not still_failing:
            print("✅ ALL TESTS MAINTAINED")
            print("   No improvement, but no regression either")
            print("   ✅ This Code2MCP version can be accepted")
            return 0
        else:
            print("⚠️  NO CHANGE")
            print("   Test results same as before")
            return 0

    def save_results(self, filename: str = None):
        """保存测试结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"code2mcp_test_results_{timestamp}.json"

        output_path = self.test_output_dir / filename

        output_data = {
            "timestamp": datetime.now().isoformat(),
            "code2mcp_path": str(self.code2mcp_path),
            "total_cases": len(self.results),
            "results": self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved to: {output_path}")
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test new Code2MCP version")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all cases"
    )
    parser.add_argument(
        "--case",
        type=str,
        help="Test specific case (e.g., SPM, sympy)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Only test golden cases (success status)"
    )
    parser.add_argument(
        "--code2mcp-path",
        type=str,
        default="Code2MCP-latest",
        help="Path to Code2MCP directory (default: Code2MCP-latest)"
    )

    args = parser.parse_args()

    tester = Code2MCPTester(code2mcp_path=args.code2mcp_path)

    # 确定要测试的cases
    if args.case:
        case_names = [args.case]
    elif args.quick:
        # 只测试golden cases
        case_names = [c["name"] for c in tester.registry["cases"] if c["status"] == "success"]
        if not case_names:
            print("⚠️  No golden cases found, testing all cases instead")
            case_names = None
    elif args.all:
        case_names = None  # 测试所有
    else:
        print("Please specify --all, --case NAME, or --quick")
        return 1

    # 运行测试
    tester.test_all_cases(case_names)

    # 打印摘要
    exit_code = tester.print_summary()

    # 保存结果
    tester.save_results()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
