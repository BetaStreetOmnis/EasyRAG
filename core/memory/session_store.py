import threading
from collections import OrderedDict
from typing import Dict, List, Tuple


DEFAULT_MAX_SESSIONS = 1000
DEFAULT_MAX_MESSAGES_PER_SESSION = 200


class InMemorySessionStore:
    """提供线程安全的进程内会话历史存储。"""

    def __init__(
        self,
        max_sessions=DEFAULT_MAX_SESSIONS,
        max_messages_per_session=DEFAULT_MAX_MESSAGES_PER_SESSION,
    ):
        """初始化 LRU 会话存储并校验容量限制。"""
        self._validate_limit("max_sessions", max_sessions)
        self._validate_limit(
            "max_messages_per_session", max_messages_per_session
        )
        self.max_sessions = max_sessions
        self.max_messages_per_session = max_messages_per_session
        self._sessions: Dict[Tuple[str, str], List[Dict[str, str]]] = (
            OrderedDict()
        )
        self._lock = threading.Lock()

    @staticmethod
    def _validate_limit(name, value):
        """校验容量限制必须是正整数。"""
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(f"{name} 必须是大于 0 的整数")

    @staticmethod
    def _validate_session_key(kb_name, session_id):
        """校验会话键的组成部分必须是非空字符串。"""
        if not isinstance(kb_name, str) or not kb_name:
            raise ValueError("kb_name 必须是非空字符串")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id 必须是非空字符串")

    def append(self, kb_name, session_id, role, content):
        """追加消息并执行单会话与全量会话上限控制。"""
        self._validate_session_key(kb_name, session_id)
        if role not in ("user", "assistant"):
            raise ValueError("role 必须是 user 或 assistant")
        if not isinstance(content, str) or not content:
            raise ValueError("content 必须是非空字符串")

        message = {"role": role, "content": content}
        key = (kb_name, session_id)
        with self._lock:
            if key in self._sessions:
                self._sessions.move_to_end(key)
            else:
                self._sessions[key] = []
            self._sessions[key].append(message)
            if len(self._sessions[key]) > self.max_messages_per_session:
                del self._sessions[key][:-self.max_messages_per_session]
            while len(self._sessions) > self.max_sessions:
                self._sessions.popitem(last=False)

    def get_history(self, kb_name, session_id):
        """返回指定会话历史的新列表，并触发 LRU 访问。"""
        self._validate_session_key(kb_name, session_id)
        key = (kb_name, session_id)
        with self._lock:
            if key not in self._sessions:
                return []
            self._sessions.move_to_end(key)
            return list(self._sessions[key])

    def clear(self, kb_name, session_id):
        """删除指定会话；会话不存在时静默成功。"""
        self._validate_session_key(kb_name, session_id)
        key = (kb_name, session_id)
        with self._lock:
            self._sessions.pop(key, None)

    def clear_all(self):
        """清空全部会话。"""
        with self._lock:
            self._sessions.clear()

    def stats(self):
        """返回当前会话数与消息总数。"""
        with self._lock:
            return {
                "sessions": len(self._sessions),
                "messages": sum(
                    len(messages) for messages in self._sessions.values()
                ),
            }
