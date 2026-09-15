import unittest

from core.memory.history_window import trim_history


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


if __name__ == "__main__":
    unittest.main()
