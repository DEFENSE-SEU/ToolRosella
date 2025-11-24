"""
Simple test script for chat module
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables
project_root = parent_dir.parent
env_file = project_root / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file, override=True)

from chat.llm_client import LLMClient
from chat.chat_manager import ChatManager


def test_llm_client():
    """Test LLM client initialization and basic chat"""
    print("=" * 50)
    print("测试 LLM Client")
    print("=" * 50)

    try:
        client = LLMClient()
        print(f"✓ LLM Client 初始化成功")
        print(f"  - API Base: {client.base_url}")
        print(f"  - Model: {client.model}")

        # Test a simple completion
        messages = [{"role": "user", "content": "你好，请用一句话介绍你自己"}]
        print(f"\n发送测试消息...")
        response = client.chat_completion(messages)
        print(f"✓ 收到响应: {response[:100]}...")

        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_chat_manager():
    """Test chat manager functionality"""
    print("\n" + "=" * 50)
    print("测试 Chat Manager")
    print("=" * 50)

    try:
        # Use a temporary directory for testing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        manager = ChatManager(storage_dir=temp_dir)
        print(f"✓ Chat Manager 初始化成功")
        print(f"  - 存储目录: {temp_dir}")

        # Create a session
        session_id = manager.create_session()
        print(f"\n✓ 创建会话: {session_id}")

        # Add messages
        manager.add_message(session_id, "user", "测试消息1")
        manager.add_message(session_id, "assistant", "测试回复1")
        print(f"✓ 添加消息成功")

        # Get messages
        messages = manager.get_messages(session_id)
        print(f"✓ 获取消息: {len(messages)} 条")
        for msg in messages:
            print(f"  - {msg['role']}: {msg['content']}")

        # List sessions
        sessions = manager.list_sessions()
        print(f"\n✓ 会话列表: {len(sessions)} 个会话")

        # Clean up
        manager.delete_session(session_id)
        print(f"✓ 删除会话成功")

        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_streaming():
    """Test streaming response"""
    print("\n" + "=" * 50)
    print("测试流式响应")
    print("=" * 50)

    try:
        client = LLMClient()
        messages = [{"role": "user", "content": "数到10"}]

        print("开始流式响应:")
        full_response = ""
        for chunk in client.chat_stream(messages):
            print(chunk, end="", flush=True)
            full_response += chunk

        print(f"\n✓ 流式响应完成，共 {len(full_response)} 字符")
        return True
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def main():
    """Run all tests"""
    print("\n开始测试 Chat 模块\n")

    results = []
    results.append(("LLM Client", test_llm_client()))
    results.append(("Chat Manager", test_chat_manager()))
    results.append(("流式响应", test_streaming()))

    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
