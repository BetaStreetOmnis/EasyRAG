"""GraphBuildService 离线单元测试。"""

import json
import hashlib

import pytest

from core.graph import LLMEntityRelationExtractor, SqliteGraphStore
from core.graph.builder import GraphBuildService


class FakeLLM:
    """按调用顺序返回预设响应的离线 LLM。"""

    def __init__(self, responses):
        """保存预设响应并初始化调用记录。"""
        self.responses = list(responses)
        self.calls = []

    def generate_response(self, query, temperature=None, max_length=None):
        """记录请求并返回下一条预设响应。"""
        self.calls.append({"query": query, "temperature": temperature})
        if not self.responses:
            raise AssertionError("FakeLLM 响应已耗尽")
        return self.responses.pop(0)


def make_service(tmp_path, responses, **kwargs):
    """构造使用临时 SQLite 存储的构建服务。"""
    llm = FakeLLM(responses)
    service = GraphBuildService(
        LLMEntityRelationExtractor(llm_client=llm, **kwargs),
        SqliteGraphStore(str(tmp_path / "graph.db")),
    )
    return service, llm, service._store


@pytest.mark.parametrize(
    ("payloads", "expected"),
    [
        (
            [
                {
                    "entities": [
                        {"name": "OpenAI", "type": "组织"},
                        {"name": "GPT", "type": "技术"},
                    ],
                    "relations": [
                        {"source": "OpenAI", "target": "GPT", "type": "研发"}
                    ],
                }
            ],
            (2, 1),
        ),
        ([{"entities": [], "relations": []}], (0, 0)),
    ],
)
def test_build_saves_graph_and_returns_stats(tmp_path, payloads, expected):
    """正常构建会保存去重图谱，并返回抽取运行统计。"""
    responses = [json.dumps(payload) for payload in payloads]
    service, llm, _ = make_service(tmp_path, responses)

    stats = service.build("kb-1", [("chunk-1", "OpenAI 研发 GPT")])

    assert (stats["entities"], stats["relations"]) == expected
    assert stats["kb_name"] == "kb-1"
    assert stats["chunks_total"] == 1
    assert stats["total_chunks"] == 1
    assert stats["succeeded_chunks"] == 1
    assert stats["failed_chunks"] == []
    assert len(llm.calls) == 1


def test_build_from_documents_uses_document_id_and_fallback(tmp_path):
    """文档自带 id 时优先使用，缺失时按索引兜底。"""
    payload = {
        "entities": [{"name": "OpenAI", "type": "组织"}],
        "relations": [],
    }
    service, _, store = make_service(tmp_path, [json.dumps(payload)] * 2)
    documents = [
        {"id": "custom-id", "text": "OpenAI"},
        {"text": "OpenAI"},
    ]

    stats = service.build_from_documents("kb-1", documents)

    assert stats["succeeded_chunks"] == 2
    entity_id = "entity-" + hashlib.sha1("OpenAI|组织".encode()).hexdigest()[:12]
    assert store.load("kb-1").entities[entity_id].source_chunk_ids == [
        "custom-id",
        "doc-1",
    ]


def test_build_without_chunks_raises_value_error(tmp_path):
    """空 chunk 列表在调用 LLM 前直接失败。"""
    service, llm, _ = make_service(tmp_path, [])

    with pytest.raises(ValueError, match="知识库中没有可用的文本块"):
        service.build("kb-1", [])

    assert llm.calls == []


def test_build_tolerates_single_chunk_failure(tmp_path):
    """strict=False 时单 chunk 失败不阻断其他文本抽取和落库。"""
    valid = {
        "entities": [{"name": "OpenAI", "type": "组织"}],
        "relations": [],
    }
    service, llm, store = make_service(
        tmp_path,
        [json.dumps(valid), "bad", "bad", json.dumps(valid)],
        max_retries=1,
    )

    stats = service.build(
        "kb-1",
        [("chunk-1", "有效"), ("chunk-2", "无效"), ("chunk-3", "有效")],
    )

    assert stats["succeeded_chunks"] == 2
    assert stats["failed_chunks"] == ["chunk-2"]
    assert len(stats["chunk_errors"]) == 1
    assert len(llm.calls) == 4
    assert len(store.load("kb-1").entities) == 1


@pytest.mark.parametrize(
    ("max_chunks", "expected"),
    [
        (0, ["doc-0", "doc-1", "doc-2"]),
        (2, ["doc-0", "doc-1"]),
    ],
)
def test_extract_endpoint_applies_max_chunks(monkeypatch, max_chunks, expected):
    """max_chunks 为 0 时不截断，正数时只保留前 N 个 chunk。"""
    chunks = [
        ("doc-0", "文本一"),
        ("doc-1", "文本二"),
        ("doc-2", "文本三"),
    ]

    assert GraphBuildService.limit_chunks(chunks, max_chunks) == chunks[: len(expected)]
