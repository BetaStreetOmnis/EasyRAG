import sys
import unittest
from types import ModuleType

from fastapi.testclient import TestClient

from core.memory.session_store import (
    InMemorySessionStore,
    session_history_messages,
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


import app as app_module  # noqa: E402
from app import SESSION_STORE  # noqa: E402


class TestSessionHistoryMessages(unittest.TestCase):
    def setUp(self):
        self.store = InMemorySessionStore()

    def test_empty_store_returns_empty_history(self):
        self.assertEqual(session_history_messages(self.store, "kb", "session"), [])

    def test_turn_limit_trims_session_history(self):
        history = []
        for index in range(3):
            history.extend([
                {"role": "user", "content": f"问题{index}"},
                {"role": "assistant", "content": f"回答{index}"},
            ])
            self.store.append("kb", "session", "user", f"问题{index}")
            self.store.append("kb", "session", "assistant", f"回答{index}")

        self.assertEqual(
            session_history_messages(self.store, "kb", "session", history_max_turns=1),
            history[-2:],
        )

    def test_char_limit_trims_session_history(self):
        self.store.append("kb", "session", "user", "u" * 8)
        self.store.append("kb", "session", "assistant", "a" * 8)
        self.assertEqual(
            session_history_messages(
                self.store, "kb", "session", history_max_chars=100
            ),
            [
                {"role": "user", "content": "u" * 8},
                {"role": "assistant", "content": "a" * 8},
            ],
        )

    def test_none_store_raises_value_error(self):
        with self.assertRaises(ValueError):
            session_history_messages(None, "kb", "session")


class FakeRAGService:
    calls = None
    kb_names = None
    results = None

    def kb_exists(self, kb_name):
        return kb_name in (self.kb_names or {"kb"})

    def chat_with_kb(self, **kwargs):
        self.calls.append(kwargs)
        if not self.results:
            return "回答"
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class TestSessionChatEndpoints(unittest.TestCase):
    def setUp(self):
        self.original_rag_service = app_module.RAGService
        app_module.RAGService = FakeRAGService
        FakeRAGService.calls = []
        FakeRAGService.results = []
        SESSION_STORE.clear_all()
        self.client = TestClient(app_module.app)

    def tearDown(self):
        app_module.RAGService = self.original_rag_service
        SESSION_STORE.clear_all()

    def test_without_session_uses_request_history(self):
        history = [
            {"role": "user", "content": "旧问题"},
            {"role": "assistant", "content": "旧回答"},
        ]
        response = self.client.post(
            "/kb/chat", json={"kb_name": "kb", "query": "问题", "history": history}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "answer": "回答"})
        self.assertEqual(FakeRAGService.calls[0]["history"], history)

    def test_session_first_round_uses_empty_history_and_saves_turn(self):
        response = self.client.post(
            "/kb/chat", json={"kb_name": "kb", "query": "问题", "session_id": "session"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FakeRAGService.calls[0]["history"], [])
        self.assertEqual(
            SESSION_STORE.get_history("kb", "session"),
            [
                {"role": "user", "content": "问题"},
                {"role": "assistant", "content": "回答"},
            ],
        )

    def test_session_second_round_uses_previous_turn(self):
        for query in ("第一问", "第二问"):
            response = self.client.post(
                "/kb/chat",
                json={"kb_name": "kb", "query": query, "session_id": "session"},
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(FakeRAGService.calls[1]["history"], [
            {"role": "user", "content": "第一问"},
            {"role": "assistant", "content": "回答"},
        ])

    def test_session_ignores_request_history(self):
        SESSION_STORE.append("kb", "session", "user", "服务端问题")
        SESSION_STORE.append("kb", "session", "assistant", "服务端回答")
        response = self.client.post(
            "/kb/chat",
            json={
                "kb_name": "kb",
                "query": "问题",
                "history": [{"role": "user", "content": "客户端问题"}],
                "session_id": "session",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FakeRAGService.calls[0]["history"], [
            {"role": "user", "content": "服务端问题"},
            {"role": "assistant", "content": "服务端回答"},
        ])

    def test_missing_kb_with_session_does_not_write(self):
        response = self.client.post(
            "/kb/chat",
            json={"kb_name": "missing", "query": "问题", "session_id": "session"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(SESSION_STORE.get_history("missing", "session"), [])

    def test_chat_exception_with_session_does_not_write(self):
        FakeRAGService.results = [RuntimeError("生成失败")]
        response = self.client.post(
            "/kb/chat", json={"kb_name": "kb", "query": "问题", "session_id": "session"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(SESSION_STORE.get_history("kb", "session"), [])

    def test_chat_empty_answer_with_session_does_not_write(self):
        FakeRAGService.results = [""]
        response = self.client.post(
            "/kb/chat", json={"kb_name": "kb", "query": "问题", "session_id": "session"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "answer": ""})
        self.assertEqual(SESSION_STORE.get_history("kb", "session"), [])

    def test_stream_sessions_receive_concatenated_answer_history(self):
        FakeRAGService.results = [["第一", "段"], ["第二", "回答"]]
        first = self.client.post(
            "/kb/chat_stream",
            json={"kb_name": "kb", "query": "第一问", "session_id": "session"},
        )
        second = self.client.post(
            "/kb/chat_stream",
            json={"kb_name": "kb", "query": "第二问", "session_id": "session"},
        )
        self.assertEqual(first.text, "第一段")
        self.assertEqual(second.text, "第二回答")
        self.assertEqual(FakeRAGService.calls[1]["history"], [
            {"role": "user", "content": "第一问"},
            {"role": "assistant", "content": "第一段"},
        ])
        self.assertEqual(SESSION_STORE.get_history("kb", "session"), [
            {"role": "user", "content": "第一问"},
            {"role": "assistant", "content": "第一段"},
            {"role": "user", "content": "第二问"},
            {"role": "assistant", "content": "第二回答"},
        ])

    def test_stream_empty_answer_with_session_does_not_write(self):
        FakeRAGService.results = [[]]
        response = self.client.post(
            "/kb/chat_stream",
            json={"kb_name": "kb", "query": "问题", "session_id": "session"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")
        self.assertEqual(SESSION_STORE.get_history("kb", "session"), [])

    def test_invalid_session_id_returns_422(self):
        payloads = [
            {"kb_name": "kb", "query": "问题", "session_id": ""},
            {"kb_name": "kb", "query": "问题", "session_id": "s" * 129},
        ]
        for payload in payloads:
            response = self.client.post("/kb/chat", json=payload)
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
