"""
Chat Manager for managing conversation history
Stores chat history locally using JSON files
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class ChatManager:
    """
    Manages chat conversations and history
    Stores conversations in a local directory as JSON files
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize ChatManager

        Args:
            storage_dir: Directory to store chat history files
                        Defaults to ./chat_history in the current working directory
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), "chat_history")

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> str:
        """
        Create a new chat session

        Returns:
            Session ID (timestamp-based)
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_file = self.storage_dir / f"{session_id}.json"

        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to a session

        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata for the message
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            raise ValueError(f"Session {session_id} does not exist")

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            message["metadata"] = metadata

        session_data["messages"].append(message)

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get all messages from a session

        Args:
            session_id: Session ID

        Returns:
            List of messages (only role and content for LLM compatibility)
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            raise ValueError(f"Session {session_id} does not exist")

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Return only role and content for LLM API compatibility
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session_data["messages"]
        ]

    def get_full_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session data including metadata

        Args:
            session_id: Session ID

        Returns:
            Full session data
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            raise ValueError(f"Session {session_id} does not exist")

        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all chat sessions

        Returns:
            List of session metadata (id, created_at, message_count, preview)
        """
        sessions = []

        for session_file in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                preview = ""
                if session_data["messages"]:
                    first_msg = session_data["messages"][0]
                    preview = first_msg["content"][:50]

                sessions.append({
                    "session_id": session_data["session_id"],
                    "created_at": session_data["created_at"],
                    "message_count": len(session_data["messages"]),
                    "preview": preview
                })
            except Exception:
                continue

        return sessions

    def delete_session(self, session_id: str):
        """
        Delete a chat session

        Args:
            session_id: Session ID to delete
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if session_file.exists():
            session_file.unlink()

    def clear_all_sessions(self):
        """
        Delete all chat sessions
        """
        for session_file in self.storage_dir.glob("*.json"):
            session_file.unlink()
