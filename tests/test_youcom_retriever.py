"""YouComWebRetriever 单元测试（纯离线，不触网、不需要真实 Key）。

用标准库 unittest + mock 打桩 requests.get，覆盖：来源映射、鉴权头与
User-Agent、top_k 夹取与总数截断、未配置 Key、各类错误（非 2xx / 网络异常 /
解析失败）优雅降级、异常响应结构不崩溃、Key 不泄露。

运行：`python -m unittest discover -s tests`（无需额外依赖）。
"""
import unittest
from unittest import mock

import requests

from core.web_search.youcom_retriever import YouComWebRetriever, YOUCOM_USER_AGENT


class FakeResp:
    def __init__(self, status_code=200, payload=None, raise_json=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("no json")
        return self._payload


SAMPLE = {
    "results": {
        "web": [
            {"url": "https://e.com/a", "title": "标题A", "description": "描述A",
             "snippets": ["片段A1", "片段A2"]},
            {"url": "https://e.com/b", "title": "标题B", "snippets": ["片段B1"]},
        ],
        "news": [
            {"url": "https://e.com/n", "title": "新闻N", "description": "新闻描述"},
        ],
    },
    "metadata": {"query": "t"},
}


class YouComWebRetrieverTest(unittest.TestCase):

    def test_unavailable_without_key(self):
        r = YouComWebRetriever(api_key="")
        self.assertFalse(r.available)
        with mock.patch.object(requests, "get") as g:
            self.assertEqual(r.search("q"), [])
            g.assert_not_called()

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_maps_web_and_news(self, g):
        g.return_value = FakeResp(200, SAMPLE)
        r = YouComWebRetriever(api_key="secret-key")
        out = r.search("测试", top_k=5)

        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]["index"], 0)
        self.assertEqual(out[0]["metadata"], {
            "url": "https://e.com/a", "title": "标题A", "source": "you.com"})
        self.assertIn("描述A", out[0]["text"])
        self.assertIn("来源: https://e.com/a", out[0]["text"])
        self.assertIn("片段B1", out[1]["text"])   # description 缺失回退 snippet
        self.assertEqual(out[2]["metadata"]["title"], "新闻N")   # news 也纳入
        # 分数按名次递减
        self.assertGreater(out[0]["score"], out[2]["score"])

        # 请求头带 X-API-Key 与团队约定 User-Agent；count 为夹取后的值
        _, kwargs = g.call_args
        self.assertEqual(kwargs["headers"]["X-API-Key"], "secret-key")
        self.assertEqual(kwargs["headers"]["User-Agent"], YOUCOM_USER_AGENT)
        self.assertEqual(kwargs["params"]["query"], "测试")
        self.assertEqual(kwargs["params"]["count"], 5)

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_top_k_clamped_and_total_truncated(self, g):
        body = {"results": {
            "web": [{"url": f"u{i}", "title": f"T{i}"} for i in range(4)],
            "news": [{"url": "un", "title": "N"}],
        }}
        g.return_value = FakeResp(200, body)
        r = YouComWebRetriever(api_key="k")

        out = r.search("q", top_k=99)                 # 99 → 夹取为 MAX_TOP_K(20)
        _, kwargs = g.call_args
        self.assertEqual(kwargs["params"]["count"], 20)

        out = r.search("q", top_k=3)                  # web+news=5 → 截断为 3
        self.assertEqual(len(out), 3)

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_invalid_top_k_falls_back_to_default(self, g):
        g.return_value = FakeResp(200, {"results": {"web": []}})
        r = YouComWebRetriever(api_key="k")
        r.search("q", top_k="not-an-int")
        _, kwargs = g.call_args
        self.assertEqual(kwargs["params"]["count"], 5)

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_non_200_returns_empty_and_no_key_leak(self, g):
        g.return_value = FakeResp(500, payload={"echo": "secret-key"})
        r = YouComWebRetriever(api_key="secret-key")
        out = r.search("q")
        self.assertEqual(out, [])
        self.assertNotIn("secret-key", str(out))

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_network_error_returns_empty(self, g):
        g.side_effect = requests.RequestException("boom")
        r = YouComWebRetriever(api_key="k")
        self.assertEqual(r.search("q"), [])

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_bad_json_returns_empty(self, g):
        g.return_value = FakeResp(200, raise_json=True)
        r = YouComWebRetriever(api_key="k")
        self.assertEqual(r.search("q"), [])

    def test_whitespace_key_is_not_available(self):
        r = YouComWebRetriever(api_key="   ")
        self.assertFalse(r.available)          # 空白 Key 视为未配置
        with mock.patch.object(requests, "get") as g:
            self.assertEqual(r.search("q"), [])
            g.assert_not_called()

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_non_dict_payloads_return_empty(self, g):
        # 顶层为 list/str，或 results 为非 dict：不得抛出，统一返回 []
        for payload in ([1, 2, 3], "oops", {"results": "oops"}, {"results": [1]}):
            g.return_value = FakeResp(200, payload)
            r = YouComWebRetriever(api_key="k")
            self.assertEqual(r.search("q"), [], payload)

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_hostile_shapes_no_crash(self, g):
        body = {"results": {
            "web": ["str", 42, None, {"title": None, "url": None,
                                      "snippets": [None, "有效片段"]}],
            "news": "not-a-list",
        }}
        g.return_value = FakeResp(200, body)
        r = YouComWebRetriever(api_key="k")
        out = r.search("q")
        self.assertEqual(len(out), 1)                 # 非 dict / 非法项被跳过
        self.assertIn("有效片段", out[0]["text"])

    @mock.patch("core.web_search.youcom_retriever.requests.get")
    def test_missing_results_node(self, g):
        g.return_value = FakeResp(200, {"metadata": {}})
        r = YouComWebRetriever(api_key="k")
        self.assertEqual(r.search("q"), [])


if __name__ == "__main__":
    unittest.main()
