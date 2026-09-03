"""知识图谱 LLM 抽取器离线单元测试。"""

import hashlib
import json
import sys

import pytest

from core.graph import GraphExtractionError, LLMEntityRelationExtractor


class FakeLLM:
    """按调用顺序返回预设响应的离线 LLM。"""

    def __init__(self, responses):
        """保存预设响应并初始化调用记录。"""
        self.responses = list(responses)
        self.calls = []

    def generate_response(self, query, temperature=None, max_length=None):
        """记录请求参数并返回下一条预设响应。"""
        self.calls.append(
            {
                "query": query,
                "temperature": temperature,
                "max_length": max_length,
            }
        )
        if not self.responses:
            raise AssertionError("FakeLLM 响应已耗尽")
        return self.responses.pop(0)


def make_extractor(responses, **kwargs):
    """构造使用 FakeLLM 的抽取器。"""
    llm = FakeLLM(responses)
    return LLMEntityRelationExtractor(llm_client=llm, **kwargs), llm


def entity_id(name, entity_type):
    """计算测试期望的实体 ID。"""
    digest = hashlib.sha1("{}|{}".format(name, entity_type).encode("utf-8")).hexdigest()[:12]
    return "entity-" + digest


def relation_id(source, relation_type, target):
    """计算测试期望的关系 ID。"""
    digest = hashlib.sha1("{}|{}|{}".format(source, relation_type, target).encode("utf-8")).hexdigest()[:12]
    return "relation-" + digest


def test_normal_json_builds_deterministic_graph():
    """正常 JSON 输出可转换为确定性图谱。"""
    payload = {
        "entities": [
            {"name": "OpenAI", "type": "组织", "properties": {"country": "America"}},
            {"name": "OpenAI", "type": "组织", "properties": {"model": "GPT"}},
            {"name": "GPT", "type": "技术"},
        ],
        "relations": [
            {"source": "OpenAI", "target": "GPT", "type": "研发", "weight": 0.9}
        ],
    }
    extractor, llm = make_extractor([json.dumps(payload)])
    graph = extractor.extract_from_chunk("OpenAI 研发 GPT", "chunk-1")

    openai_id = entity_id("OpenAI", "组织")
    gpt_id = entity_id("GPT", "技术")
    assert set(graph.entities) == {openai_id, gpt_id}
    assert graph.entities[openai_id].properties == {"country": "America", "model": "GPT"}
    assert graph.entities[openai_id].source_chunk_ids == ["chunk-1"]
    relation = graph.relations[0]
    assert relation.id == relation_id("OpenAI", "研发", "GPT")
    assert relation.source_entity_id == openai_id
    assert relation.target_entity_id == gpt_id
    assert relation.weight == pytest.approx(0.9)
    assert llm.calls[0]["temperature"] == 0.0


def test_json_with_markdown_fence_and_noise_is_extracted():
    """围栏和前后噪声不影响平衡 JSON 对象截取。"""
    response = '前置噪声 ```json\n{"entities": [{"name": "张三", "type": "人物"}], "relations": []}\n``` 后置噪声'
    extractor, _ = make_extractor([response])
    graph = extractor.extract_from_chunk("张三是一名工程师。", "chunk-1")
    assert list(graph.entities) == [entity_id("张三", "人物")]


def test_invalid_json_then_valid_retries_successfully():
    """顶层 JSON 解析失败会携带错误原因重试。"""
    valid = json.dumps({"entities": [], "relations": []})
    extractor, llm = make_extractor(["不是 JSON", valid], max_retries=2)
    graph = extractor.extract_from_chunk("文本", "chunk-1")

    assert graph.to_dict() == {"entities": [], "relations": []}
    assert len(llm.calls) == 2
    assert "JSON 解析失败" in llm.calls[1]["query"]
    assert "上一轮输出无效" in llm.calls[1]["query"]


def test_invalid_json_exhausts_retries():
    """连续结构错误按 1 加重试次数调用后失败。"""
    extractor, llm = make_extractor(["bad", "bad", "bad"], max_retries=2)
    with pytest.raises(GraphExtractionError, match="JSON 解析失败"):
        extractor.extract_from_chunk("文本", "chunk-1")
    assert len(llm.calls) == 3


def test_unknown_relation_endpoint_is_dropped_without_retry():
    """关系端点不匹配属于语义修正，不触发重试。"""
    payload = {
        "entities": [{"name": "OpenAI", "type": "组织"}],
        "relations": [
            {"source": "OpenAI", "target": "不存在", "type": "研发"},
            {"source": "OpenAI", "target": "OpenAI", "type": "自指"},
        ],
    }
    extractor, llm = make_extractor([json.dumps(payload)], max_retries=2)
    graph = extractor.extract_from_chunk("文本", "chunk-1")
    assert len(graph.relations) == 1
    assert graph.relations[0].type == "自指"
    assert len(llm.calls) == 1


def test_entity_type_whitelist_cascades_relations():
    """白名单过滤实体，并级联删除端点关系。"""
    payload = {
        "entities": [
            {"name": "OpenAI", "type": "组织"},
            {"name": "GPT", "type": "技术"},
            {"name": "New York", "type": "地点"},
        ],
        "relations": [
            {"source": "OpenAI", "target": "GPT", "type": "研发"},
            {"source": "OpenAI", "target": "New York", "type": "位于"},
        ],
    }
    extractor, _ = make_extractor([json.dumps(payload)], entity_types={"人物", "组织", "概念", "技术"})
    graph = extractor.extract_from_chunk("文本", "chunk-1")
    assert set(graph.entities) == {
        entity_id("OpenAI", "组织"),
        entity_id("GPT", "技术"),
    }
    assert [relation.type for relation in graph.relations] == ["研发"]


@pytest.mark.parametrize(
    "weight,expected",
    [("bad", 1.0), (-0.5, 0.0), (1.5, 1.0)],
)
def test_relation_weight_is_normalized(weight, expected):
    """非法 weight 回退，越界 weight 钳制到合法区间。"""
    payload = {
        "entities": [{"name": "A", "type": "概念"}, {"name": "B", "type": "概念"}],
        "relations": [{"source": "A", "target": "B", "type": "相关", "weight": weight}],
    }
    extractor, _ = make_extractor([json.dumps(payload, ensure_ascii=False)])
    graph = extractor.extract_from_chunk("A 与 B 相关", "chunk-1")
    assert graph.relations[0].weight == pytest.approx(expected)


def test_empty_chunk_and_empty_schema_return_empty_graph():
    """空输入和空抽取 schema 都返回空图谱。"""
    empty_schema = json.dumps({"entities": [], "relations": []})
    extractor, llm = make_extractor([empty_schema, empty_schema])
    assert extractor.extract_from_chunk("", "empty-chunk").to_dict() == {
        "entities": [],
        "relations": [],
    }
    assert extractor.extract_from_chunks([("empty-schema", "文本")]).to_dict() == {
        "entities": [],
        "relations": [],
    }
    assert len(llm.calls) == 2


def test_extract_from_chunks_merges_and_records_failures():
    """批量抽取合并同名同类型实体，并默认跳过失败 chunk。"""
    first = {
        "entities": [
            {"name": "OpenAI", "type": "组织", "properties": {"a": 1}},
            {"name": "GPT", "type": "技术"},
        ],
        "relations": [{"source": "OpenAI", "target": "GPT", "type": "研发"}],
    }
    third = {
        "entities": [
            {"name": "OpenAI", "type": "组织", "properties": {"b": 2}},
            {"name": "Claude", "type": "技术"},
        ],
        "relations": [{"source": "OpenAI", "target": "Claude", "type": "对比"}],
    }
    extractor, llm = make_extractor(
        [json.dumps(first), "bad", "bad", json.dumps(third)], max_retries=1
    )
    graph = extractor.extract_from_chunks(
        [("chunk-1", "文本一"), ("chunk-2", "文本二"), ("chunk-3", "文本三")]
    )
    openai_id = entity_id("OpenAI", "组织")
    assert graph.entities[openai_id].source_chunk_ids == ["chunk-1", "chunk-3"]
    assert graph.entities[openai_id].properties == {"a": 1, "b": 2}
    assert {relation.type for relation in graph.relations} == {"研发", "对比"}
    assert extractor.last_run_stats == {
        "total_chunks": 3,
        "succeeded_chunks": 2,
        "failed_chunks": ["chunk-2"],
        "chunk_errors": extractor.last_run_stats["chunk_errors"],
        "total_entities": 4,
        "total_relations": 2,
    }
    assert len(llm.calls) == 4


def test_extract_from_chunks_strict_raises_on_failure():
    """strict 模式下失败 chunk 立即中断批量抽取。"""
    extractor, llm = make_extractor(["bad", "bad", "bad"], max_retries=2)
    with pytest.raises(GraphExtractionError):
        extractor.extract_from_chunks([("chunk-1", "文本")], strict=True)
    assert len(llm.calls) == 3
    assert extractor.last_run_stats["failed_chunks"] == ["chunk-1"]


def test_long_chunk_is_truncated_before_llm_call():
    """超长输入先截断，不会传给 LLM 超限部分。"""
    extractor, llm = make_extractor([json.dumps({"entities": [], "relations": []})], max_chunk_chars=20)
    extractor.extract_from_chunk("A" * 21, "chunk-1")
    assert "A" * 20 in llm.calls[0]["query"]
    assert "A" * 21 not in llm.calls[0]["query"]


def test_default_llm_client_is_created_lazily(monkeypatch):
    """默认模型客户端只在首次抽取时创建。"""
    default_llm = FakeLLM([json.dumps({"entities": [], "relations": []})])

    class FakeModule:
        """模拟惰性导入的模型模块。"""

        @staticmethod
        def get_openai_model():
            """返回离线模型客户端。"""
            return default_llm

    monkeypatch.setitem(sys.modules, "core.llm.openai_llm_model", FakeModule)
    extractor = LLMEntityRelationExtractor()

    extractor.extract_from_chunk("文本", "chunk-1")

    assert len(default_llm.calls) == 1
