#!/usr/bin/env python3
"""
MCP Service测试脚本

测试mcp_service.py能否正常启动和工作
这是比test_mcp_basic.py更深入的测试
"""

import sys
import json
import os
import subprocess
import time
import socket
from pathlib import Path
from typing import Dict, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MCPServiceTester:
    """MCP Service测试器 - 测试mcp_service.py层"""

    def __init__(self):
        # 加载测试用例注册表
        registry_path = Path(project_root) / "test" / "test_cases_registry.json"
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

        self.results = {}

    def find_free_port(self) -> int:
        """找到一个可用的端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def test_mcp_service_import(self, case_name: str, mcp_location: str) -> Dict:
        """
        测试mcp_service.py能否导入

        返回测试结果
        """
        print(f"\n{'='*60}")
        print(f"Testing MCP Service Import: {case_name}")
        print(f"Location: {mcp_location}")
        print(f"{'='*60}")

        mcp_plugin_path = Path(project_root) / mcp_location / "mcp_plugin"

        if not mcp_plugin_path.exists():
            error_msg = f"MCP plugin directory not found: {mcp_plugin_path}"
            print(f"❌ {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": "DirectoryNotFound"
            }

        # 临时添加到路径
        sys.path.insert(0, str(mcp_plugin_path))

        try:
            # 测试1: 导入mcp_service模块
            print("  [1/4] Importing mcp_service module...", end=" ")
            import mcp_service
            print("✅")

            # 测试2: 检查create_app函数
            print("  [2/4] Checking create_app function...", end=" ")
            if not hasattr(mcp_service, 'create_app'):
                print("❌")
                return {
                    "status": "fail",
                    "error": "create_app function not found",
                    "error_type": "MissingFunction"
                }
            print("✅")

            # 测试3: 创建app实例
            print("  [3/4] Creating MCP app instance...", end=" ")
            app = mcp_service.create_app()
            if app is None:
                print("❌")
                return {
                    "status": "fail",
                    "error": "create_app returned None",
                    "error_type": "NullApp"
                }
            print("✅")

            # 测试4: 检查有多少工具
            print("  [4/4] Checking MCP tools...", end=" ")

            # 尝试获取工具列表（不同MCP框架方法可能不同）
            tools_count = 0
            try:
                # FastMCP的方式
                if hasattr(app, 'list_tools'):
                    tools = app.list_tools()
                    tools_count = len(tools)
                # 或者检查装饰器
                elif hasattr(app, '_tools'):
                    tools_count = len(app._tools)
                # 或者扫描@mcp.tool装饰的函数
                else:
                    # 扫描模块中所有带@mcp.tool的函数
                    tools = [name for name, obj in vars(mcp_service).items()
                            if callable(obj) and not name.startswith('_')]
                    tools_count = len(tools)

                print(f"✅ ({tools_count} tools)")

            except Exception as e:
                print(f"⚠️  (couldn't enumerate tools: {e})")
                tools_count = "unknown"

            print(f"\n  ✅ MCP Service test PASSED for {case_name}")

            return {
                "status": "pass",
                "tools_count": tools_count,
                "app_type": type(app).__name__
            }

        except ImportError as e:
            error_msg = f"ImportError: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": "ImportError"
            }

        except SyntaxError as e:
            error_msg = f"SyntaxError in mcp_service.py: {str(e)}"
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
            # 清理路径
            if str(mcp_plugin_path) in sys.path:
                sys.path.remove(str(mcp_plugin_path))

            # 清理导入的模块，避免冲突
            if 'mcp_service' in sys.modules:
                del sys.modules['mcp_service']

    def test_mcp_service_startup(self, case_name: str, mcp_location: str, timeout: int = 10) -> Dict:
        """
        测试mcp_service.py能否启动（作为独立进程）

        这个测试会：
        1. 启动MCP服务
        2. 等待几秒看是否crash
        3. 终止服务

        返回测试结果
        """
        print(f"\n{'='*60}")
        print(f"Testing MCP Service Startup: {case_name}")
        print(f"{'='*60}")

        main_py = Path(project_root) / mcp_location / "mcp_plugin" / "main.py"

        if not main_py.exists():
            error_msg = f"main.py not found: {main_py}"
            print(f"❌ {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": "FileNotFound"
            }

        try:
            # 启动MCP服务作为子进程
            print(f"  [1/3] Starting MCP service...", end=" ")

            # 使用随机端口避免冲突
            port = self.find_free_port()

            process = subprocess.Popen(
                [sys.executable, str(main_py)],
                cwd=str(main_py.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print(f"✅ (PID: {process.pid}, Port: {port})")

            # 等待服务启动
            print(f"  [2/3] Waiting {timeout}s to check stability...", end=" ")
            time.sleep(timeout)

            # 检查进程是否还在运行
            poll_result = process.poll()

            if poll_result is None:
                # 进程还在运行，说明服务启动成功
                print("✅ (service still running)")

                # 终止进程
                print(f"  [3/3] Terminating service...", end=" ")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("✅")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print("⚠️  (had to kill)")

                return {
                    "status": "pass",
                    "message": f"Service ran for {timeout}s without crash"
                }

            else:
                # 进程已经退出
                stdout, stderr = process.communicate()
                error_msg = f"Service crashed with exit code {poll_result}\nSTDERR: {stderr[-500:]}"
                print(f"❌\n  {error_msg}")

                return {
                    "status": "fail",
                    "error": error_msg,
                    "error_type": "ServiceCrash",
                    "exit_code": poll_result
                }

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌\n  {error_msg}")
            return {
                "status": "fail",
                "error": error_msg,
                "error_type": type(e).__name__
            }

    def test_case(self, case_name: str, mcp_location: str, test_startup: bool = False):
        """
        测试单个case的MCP service

        参数:
            test_startup: 是否测试服务启动（耗时较长）
        """
        result = {
            "case_name": case_name,
            "import_test": {},
            "startup_test": {}
        }

        # Test 1: Import测试
        import_result = self.test_mcp_service_import(case_name, mcp_location)
        result["import_test"] = import_result

        # Test 2: Startup测试（可选）
        if test_startup and import_result.get("status") == "pass":
            startup_result = self.test_mcp_service_startup(case_name, mcp_location)
            result["startup_test"] = startup_result
        elif test_startup:
            result["startup_test"] = {
                "status": "skipped",
                "reason": "Import test failed"
            }

        # 综合判断
        if import_result.get("status") == "pass":
            if test_startup:
                result["overall_status"] = startup_result.get("status", "unknown")
            else:
                result["overall_status"] = "pass"
        else:
            result["overall_status"] = "fail"

        return result

    def test_all_cases(self, test_startup: bool = False):
        """测试所有cases"""
        print(f"\n{'='*60}")
        print(f"TESTING MCP SERVICE LAYER")
        print(f"Test startup: {test_startup}")
        print(f"{'='*60}")

        for case in self.registry["cases"]:
            result = self.test_case(
                case["name"],
                case["mcp_location"],
                test_startup=test_startup
            )
            self.results[case["name"]] = result

        return self.results

    def print_summary(self):
        """打印测试摘要"""
        if not self.results:
            print("\nNo tests run yet.")
            return

        print("\n" + "="*60)
        print("MCP SERVICE TEST SUMMARY")
        print("="*60)

        passed = [name for name, r in self.results.items() if r["overall_status"] == "pass"]
        failed = [name for name, r in self.results.items() if r["overall_status"] == "fail"]

        print(f"\n✅ PASSED: {len(passed)}/{len(self.results)}")
        for name in passed:
            tools = self.results[name]["import_test"].get("tools_count", "?")
            print(f"  - {name} ({tools} tools)")

        if failed:
            print(f"\n❌ FAILED: {len(failed)}/{len(self.results)}")
            for name in failed:
                error_type = self.results[name]["import_test"].get("error_type", "Unknown")
                print(f"  - {name} ({error_type})")

        print(f"\n" + "="*60)
        if len(passed) == len(self.results):
            print("CONCLUSION: ✅ ALL MCP SERVICES PASSED")
            return 0
        else:
            print(f"CONCLUSION: ⚠️  {len(failed)} MCP SERVICE(S) FAILED")
            return 1

    def save_results(self, output_path: str = None):
        """保存测试结果"""
        if output_path is None:
            output_path = Path(project_root) / "test" / "mcp_service_test_results.json"

        import datetime
        output_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_cases": len(self.results),
            "results": self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Results saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP Service Layer")
    parser.add_argument(
        "--startup",
        action="store_true",
        help="Also test service startup (slower, more thorough)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON"
    )

    args = parser.parse_args()

    tester = MCPServiceTester()

    # 运行测试
    tester.test_all_cases(test_startup=args.startup)

    # 打印摘要
    exit_code = tester.print_summary()

    # 保存结果
    if args.save:
        tester.save_results()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
