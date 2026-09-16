import sys
import unittest
from types import ModuleType

from pydantic import ValidationError

from core.memory.history_window import (
    DEFAULT_MAX_MESSAGE_CHARS,
    DEFAULT_MAX_TURNS,
    resolve_limits,
    trim_history,
)


for module_name, attributes in {
    "main": {"RAGService": object, "DocumentProcessor": object},
    "core.llm.local_llm_model": {"get_llm_model": lambda *args, **kwargs: None},
    "core.chunker.chunker_main": {"ChunkMethod": object},
}.items():
    module = ModuleType(module_name)
    for attribute_name, attribute_value in attributes.items():
        setattr(module, attribute_name, attribute_value)
    sys.modules.setdefault(module_name, module)

from app import ChatQuery  # noqa: E402


class TestTrimHistory(unittest.TestCase):
    def test_none_and_empty_history(self):
        # 空输入应直接返回空列表，不进入后续处理。
        self.assertEqual(trim_history(None), [])
        self.assertEqual(trim_history([]), [])

    def test_invalid_messages_are_filtered(self):
        # 仅保留合法的用户和助手消息，其他结构直接过滤。
        history = [
            "invalid",
            {"role": "user"},
            {"content": "缺少角色"},
            {"role": "system", "content": "非法角色"},
            {"role": "user", "content": 123},
            {"role": "user", "content": "用户"},
            {"role": "assistant", "content": "助手"},
        ]
        self.assertEqual(trim_history(history), [
            {"role": "user", "content": "用户"},
            {"role": "assistant", "content": "助手"},
        ])

    def test_orphan_user_is_dropped(self):
        # 没有相邻助手回复的用户消息不能组成完整轮次。
        history = [
            {"role": "user", "content": "孤立问题"},
        ]
        self.assertEqual(trim_history(history), [])

    def test_long_content_is_truncated(self):
        # 超过单条长度上限的消息应截断到指定字符数。
        history = [
            {"role": "user", "content": "a" * 8},
            {"role": "assistant", "content": "b" * 10},
        ]
        result = trim_history(history, max_message_chars=5)
        self.assertEqual(result, [
            {"role": "user", "content": "aaaaa"},
            {"role": "assistant", "content": "bbbbb"},
        ])

    def test_keeps_latest_turns_in_order(self):
        # 只保留最近 N 轮完整对话，并维持原有顺序。
        history = []
        for index in range(4):
            history.extend([
                {"role": "user", "content": f"问题{index}"},
                {"role": "assistant", "content": f"回答{index}"},
            ])
        result = trim_history(history, max_turns=2)
        self.assertEqual(result, [
            {"role": "user", "content": "问题2"},
            {"role": "assistant", "content": "回答2"},
            {"role": "user", "content": "问题3"},
            {"role": "assistant", "content": "回答3"},
        ])

    def test_normal_history_passes_through(self):
        # 正常输入应与旧校验逻辑等价，返回三轮完整对话。
        history = [
            {"role": "user", "content": "问题一"},
            {"role": "assistant", "content": "回答一"},
            {"role": "user", "content": "问题二"},
            {"role": "assistant", "content": "回答二"},
            {"role": "user", "content": "问题三"},
            {"role": "assistant", "content": "回答三"},
        ]
        self.assertEqual(trim_history(history), history)

    def test_trim_history_is_idempotent(self):
        # 再次窗口化不会改变首次结果，也不依赖外部状态。
        history = [
            {"role": "user", "content": "u" * 9},
            {"role": "assistant", "content": "a" * 9},
        ]
        first_result = trim_history(history, max_message_chars=4)
        self.assertEqual(trim_history(first_result, max_message_chars=4), first_result)

    def test_zero_max_turns_returns_empty(self):
        # 轮数窗口为零时应返回空列表。
        history = [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "回答"},
        ]
        self.assertEqual(trim_history(history, max_turns=0), [])

    def test_resolve_limits_defaults(self):
        # 未提供有效覆盖值时保持既有默认行为。
        expected_defaults = {
            "max_turns": DEFAULT_MAX_TURNS,
            "max_message_chars": DEFAULT_MAX_MESSAGE_CHARS,
        }
        self.assertEqual(resolve_limits(), expected_defaults)
        self.assertEqual(resolve_limits(None, None), {
            "max_turns": 10,
            "max_message_chars": 8000,
        })

    def test_resolve_limits_overrides(self):
        # 轮数与字符上限均可独立或同时覆盖。
        self.assertEqual(resolve_limits(max_turns=3), {
            "max_turns": 3,
            "max_message_chars": 8000,
        })
        self.assertEqual(resolve_limits(max_message_chars=123), {
            "max_turns": 10,
            "max_message_chars": 123,
        })
        self.assertEqual(resolve_limits(5, 456), {
            "max_turns": 5,
            "max_message_chars": 456,
        })

    def test_resolve_limits_falls_back_for_invalid_values(self):
        # 非整数、越界值均回退默认值，供无校验调用方兜底。
        defaults = {
            "max_turns": 10,
            "max_message_chars": 8000,
        }
        for invalid_turns in (0, -1, 101, "10", True):
            self.assertEqual(resolve_limits(max_turns=invalid_turns), defaults)
        for invalid_chars in (99, -100, 100001, "8000", False):
            self.assertEqual(resolve_limits(max_message_chars=invalid_chars), defaults)

    def test_chat_query_history_limit_defaults(self):
        # 兼容旧请求：未传新增字段时保持 None。
        query = ChatQuery(kb_name="test", query="问题")
        self.assertIsNone(query.history_max_turns)
        self.assertIsNone(query.history_max_chars)

    def test_chat_query_history_limit_validation(self):
        # 新增字段必须在请求层校验取值范围。
        with self.assertRaises(ValidationError):
            ChatQuery(kb_name="test", query="问题", history_max_turns=0)
        with self.assertRaises(ValidationError):
            ChatQuery(kb_name="test", query="问题", history_max_turns=101)
        with self.assertRaises(ValidationError):
            ChatQuery(kb_name="test", query="问题", history_max_chars=99)
        with self.assertRaises(ValidationError):
            ChatQuery(kb_name="test", query="问题", history_max_chars=100001)

    def test_resolve_limits_with_trim_history(self):
        # 端点可安全将解析结果作为 kwargs 传给窗口化函数。
        history = [
            {"role": "user", "content": "u" * 4},
            {"role": "assistant", "content": "a" * 4},
            {"role": "user", "content": "latest"},
            {"role": "assistant", "content": "answer"},
        ]
        self.assertEqual(
            trim_history(history, **resolve_limits(1, 100)),
            history[-2:],
        )


if __name__ == "__main__":
    unittest.main()
