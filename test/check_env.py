#!/usr/bin/env python3
"""
环境配置检查
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
code2mcp_path = project_root / "Code2MCP-latest"


def check_env_file():
    """检查.env文件是否存在"""
    env_file = code2mcp_path / ".env"

    print("="*60)
    print("1. Checking .env file")
    print("="*60)

    if env_file.exists():
        print(f"✅ .env file found: {env_file}")
        return True
    else:
        print(f"❌ .env file NOT found: {env_file}")
        print(f"\n💡 Solution:")
        print(f"   cp {code2mcp_path}/env_example.txt {env_file}")
        return False


def check_api_keys():
    """检查API密钥是否配置"""
    print("\n" + "="*60)
    print("2. Checking API Keys")
    print("="*60)

    env_file = code2mcp_path / ".env"

    if not env_file.exists():
        print("⚠️  Skipping (no .env file)")
        return False

    # 读取.env文件
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    # 检查MODEL_PROVIDER
    provider = config.get('MODEL_PROVIDER', '').lower()
    print(f"Model Provider: {provider or '(not set)'}")

    if not provider:
        print("⚠️  MODEL_PROVIDER not set, will use default")
        provider = 'openai'

    # 检查对应的API密钥
    api_key_found = False

    if provider == 'openai':
        api_key = config.get('OPENAI_API_KEY', '')
        if api_key and api_key != 'your_openai_api_key_here':
            print(f"✅ OPENAI_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
            api_key_found = True
        else:
            print(f"❌ OPENAI_API_KEY not configured")

    elif provider == 'deepseek':
        api_key = config.get('DEEPSEEK_API_KEY', '')
        if api_key and api_key != 'your_deepseek_api_key_here':
            print(f"✅ DEEPSEEK_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
            api_key_found = True
        else:
            print(f"❌ DEEPSEEK_API_KEY not configured")

    elif provider == 'qwen':
        api_key = config.get('QWEN_API_KEY', '')
        if api_key and api_key != 'your_qwen_api_key_here':
            print(f"✅ QWEN_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
            api_key_found = True
        else:
            print(f"❌ QWEN_API_KEY not configured")

    elif provider == 'claude':
        api_key = config.get('CLAUDE_API_KEY', '')
        if api_key and api_key != 'your_claude_api_key_here':
            print(f"✅ CLAUDE_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
            api_key_found = True
        else:
            print(f"❌ CLAUDE_API_KEY not configured")

    else:
        print(f"⚠️  Unknown provider: {provider}")

    if not api_key_found:
        print(f"\n💡 Solution:")
        print(f"   Edit {env_file}")
        print(f"   Set {provider.upper()}_API_KEY=your_actual_key_here")

    return api_key_found


def check_python_packages():
    """检查必要的Python包"""
    print("\n" + "="*60)
    print("3. Checking Python Packages")
    print("="*60)

    required_packages = [
        'fastmcp',
        'langgraph',
        'openai',
        'requests',
        'python-dotenv'
    ]

    all_installed = True

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} NOT installed")
            all_installed = False

    if not all_installed:
        print(f"\n💡 Solution:")
        print(f"   pip install -r requirements.txt")
        print(f"   # or")
        print(f"   pip install -r Code2MCP-latest/requirements.txt")

    return all_installed


def check_directories():
    """检查目录结构"""
    print("\n" + "="*60)
    print("4. Checking Directory Structure")
    print("="*60)

    # 检查Code2MCP-latest
    if code2mcp_path.exists():
        print(f"✅ Code2MCP-latest found: {code2mcp_path}")
    else:
        print(f"❌ Code2MCP-latest NOT found: {code2mcp_path}")
        print(f"\n💡 Solution:")
        print(f"   Make sure Code2MCP-latest directory exists")
        return False

    # 检查test目录
    test_dir = project_root / "test"
    if test_dir.exists():
        print(f"✅ test directory found: {test_dir}")
    else:
        print(f"❌ test directory NOT found")
        return False

    # 检查测试脚本
    test_script = test_dir / "test_new_code2mcp.py"
    if test_script.exists():
        print(f"✅ test_new_code2mcp.py found")
    else:
        print(f"❌ test_new_code2mcp.py NOT found")
        return False

    return True


def check_workspace_clean():
    """检查测试工作空间是否干净"""
    print("\n" + "="*60)
    print("5. Checking Test Workspace")
    print("="*60)

    test_workspace = project_root / "test" / "test_workspace"

    if test_workspace.exists():
        # 计算大小
        total_size = sum(f.stat().st_size for f in test_workspace.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)

        print(f"⚠️  Test workspace exists: {test_workspace}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"\n💡 Tip: You can clean it before testing:")
        print(f"   rm -rf {test_workspace}")
    else:
        print(f"✅ Test workspace is clean (will be created on first run)")

    return True


def main():
    """主检查流程"""
    print("\n" + "="*60)
    print("CODE2MCP TEST ENVIRONMENT CHECK")
    print("="*60)

    checks = [
        ("Environment file", check_env_file()),
        ("API Keys", check_api_keys()),
        ("Python packages", check_python_packages()),
        ("Directory structure", check_directories()),
        ("Workspace", check_workspace_clean())
    ]

    # 打印总结
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED - READY TO TEST!")
        print("="*60)
        print("\nYou can now run:")
        print("  python test/test_new_code2mcp.py --all")
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease fix the issues above before running tests.")
        print("See: test/SETUP_BEFORE_TESTING.md for detailed instructions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
