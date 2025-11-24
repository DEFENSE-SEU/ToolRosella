# Chat 模块

一个简单的 LLM 聊天模块，支持持久化历史记录。

## 功能特性

- 兼容 OpenAI API 的大模型集成
- 本地 JSON 文件持久化聊天历史
- 会话管理（创建、加载、删除会话）
- 支持流式响应
- 与展示功能完全分离

## 组件说明

### 1. LLMClient (`llm_client.py`)
处理与 OpenAI 兼容 API 的通信。

通过环境变量配置：
- `OPENAI_API_KEY`: 你的 API 密钥
- `OPENAI_BASE_URL`: API 端点（默认: https://api.openai.com/v1）
- `OPENAI_MODEL`: 模型名称（默认: gpt-4o）

### 2. ChatManager (`chat_manager.py`)
管理对话历史，使用本地文件存储。

功能：
- 创建新的聊天会话
- 向会话添加消息
- 获取对话历史
- 列出所有会话
- 删除会话

### 3. 聊天前端 (`frontend/app_chat.py`)
独立的 Streamlit 聊天界面。

## 使用方法

### 运行聊天界面：

```bash
cd /Users/yuanxujie/Downloads/Easy-Tool/easytool-app/frontend
streamlit run app_chat.py
```

### 编程方式使用：

```python
from chat.llm_client import LLMClient
from chat.chat_manager import ChatManager

# 初始化
llm = LLMClient()
manager = ChatManager()

# 创建会话
session_id = manager.create_session()

# 添加用户消息
manager.add_message(session_id, "user", "你好！")

# 从 LLM 获取响应
messages = manager.get_messages(session_id)
response = llm.chat_completion(messages)

# 保存助手响应
manager.add_message(session_id, "assistant", response)
```

## 文件结构

```
chat/
├── __init__.py           # 模块导出
├── llm_client.py         # LLM API 客户端
├── chat_manager.py       # 对话历史管理器
└── README.md            # 本文件

frontend/
└── app_chat.py          # Streamlit 聊天界面

chat_history/            # 自动创建的会话存储目录
└── YYYYMMDD_HHMMSS_*.json  # 会话文件
```

## 存储格式

聊天会话以 JSON 文件形式存储在 `chat_history/` 目录：

```json
{
  "session_id": "20231124_123456_789012",
  "created_at": "2023-11-24T12:34:56.789012",
  "messages": [
    {
      "role": "user",
      "content": "你好！",
      "timestamp": "2023-11-24T12:34:56.789012"
    },
    {
      "role": "assistant",
      "content": "你好！有什么我可以帮助你的吗？",
      "timestamp": "2023-11-24T12:34:58.123456"
    }
  ]
}
```

## 注意事项

1. 确保 `.env` 文件中配置了正确的 API 密钥
2. 聊天历史会存储在本地，请注意隐私和安全
3. 此模块与 `app_mcp_showcase.py` 完全独立，不会互相干扰
