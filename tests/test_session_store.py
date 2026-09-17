import threading
import unittest

from core.memory.session_store import InMemorySessionStore


class TestInMemorySessionStore(unittest.TestCase):
    def test_invalid_constructor_limits(self):
        invalid_values = (
            ("max_sessions", True),
            ("max_sessions", 0),
            ("max_sessions", -1),
            ("max_messages_per_session", False),
            ("max_messages_per_session", 0),
            ("max_messages_per_session", -10),
        )
        for argument_name, invalid_value in invalid_values:
            with self.subTest(name=argument_name, value=invalid_value):
                with self.assertRaises(ValueError):
                    InMemorySessionStore(**{argument_name: invalid_value})

    def test_append_and_get_history(self):
        store = InMemorySessionStore()
        store.append("kb", "session", "user", "问题")
        store.append("kb", "session", "assistant", "回答")

        self.assertEqual(store.get_history("kb", "session"), [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "回答"},
        ])

    def test_invalid_append_arguments(self):
        store = InMemorySessionStore()
        invalid_cases = [
            {"role": "system", "content": "内容"},
            {"role": None, "content": "内容"},
            {"role": "user", "content": ""},
            {"role": "user", "content": None},
            {"role": "user", "content": 123},
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    store.append("kb", "session", **case)

    def test_invalid_session_keys(self):
        store = InMemorySessionStore()
        invalid_keys = [
            (None, "session"),
            ("", "session"),
            (123, "session"),
            ("kb", None),
            ("kb", ""),
            ("kb", 123),
        ]
        for kb_name, session_id in invalid_keys:
            for method_name in ("append", "get_history", "clear"):
                with self.subTest(key=(kb_name, session_id), method=method_name):
                    with self.assertRaises(ValueError):
                        if method_name == "append":
                            store.append(kb_name, session_id, "user", "内容")
                        else:
                            getattr(store, method_name)(kb_name, session_id)

    def test_unknown_session_history(self):
        store = InMemorySessionStore()

        self.assertEqual(store.get_history("kb", "missing"), [])

    def test_clear_is_idempotent(self):
        store = InMemorySessionStore()
        store.append("kb", "session", "user", "问题")
        store.clear("kb", "session")
        store.clear("kb", "session")

        self.assertEqual(store.get_history("kb", "session"), [])
        self.assertEqual(store.stats(), {"sessions": 0, "messages": 0})

    def test_clear_all(self):
        store = InMemorySessionStore()
        store.append("kb1", "session1", "user", "问题1")
        store.append("kb2", "session2", "user", "问题2")
        store.clear_all()

        self.assertEqual(store.get_history("kb1", "session1"), [])
        self.assertEqual(store.get_history("kb2", "session2"), [])
        self.assertEqual(store.stats(), {"sessions": 0, "messages": 0})

    def test_lru_eviction_uses_get_history_touch(self):
        store = InMemorySessionStore(max_sessions=2)
        store.append("kb", "session1", "user", "问题1")
        store.append("kb", "session2", "user", "问题2")
        store.get_history("kb", "session1")
        store.append("kb", "session3", "user", "问题3")

        self.assertEqual(store.get_history("kb", "session1"), [
            {"role": "user", "content": "问题1"}
        ])
        self.assertEqual(store.get_history("kb", "session2"), [])
        self.assertEqual(store.stats(), {"sessions": 2, "messages": 2})

    def test_message_limit_keeps_latest_messages(self):
        store = InMemorySessionStore(max_messages_per_session=3)
        for index in range(5):
            store.append("kb", "session", "user", f"问题{index}")

        self.assertEqual(store.get_history("kb", "session"), [
            {"role": "user", "content": f"问题{index}"}
            for index in range(2, 5)
        ])

    def test_history_returns_copy(self):
        store = InMemorySessionStore()
        store.append("kb", "session", "user", "问题")
        history = store.get_history("kb", "session")
        history.clear()

        self.assertEqual(store.get_history("kb", "session"), [
            {"role": "user", "content": "问题"}
        ])

    def test_stats_counts_all_sessions_and_messages(self):
        store = InMemorySessionStore()
        store.append("kb1", "session1", "user", "问题1")
        store.append("kb1", "session1", "assistant", "回答1")
        store.append("kb2", "session2", "user", "问题2")

        self.assertEqual(store.stats(), {"sessions": 2, "messages": 3})

    def test_concurrent_append(self):
        store = InMemorySessionStore(max_messages_per_session=1000)
        results = []

        def append_messages():
            for index in range(25):
                try:
                    store.append("kb", "session", "user", f"消息{index}")
                    results.append(True)
                except ValueError:
                    results.append(False)

        threads = [threading.Thread(target=append_messages) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertTrue(all(results))
        self.assertEqual(len(store.get_history("kb", "session")), 200)
        self.assertEqual(store.stats(), {"sessions": 1, "messages": 200})


if __name__ == "__main__":
    unittest.main()
