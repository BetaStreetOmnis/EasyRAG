"""知识图谱查询服务离线单元测试。"""

import pytest

from core.graph import (
    Entity,
    GraphQueryService,
    GraphStore,
    InMemoryGraphStore,
    KnowledgeGraph,
    Relation,
    SqliteGraphStore,
)


def make_store(backend: str, tmp_path) -> GraphStore:
    """创建待测试的图谱存储后端。"""
    if backend == "memory":
        return InMemoryGraphStore()
    return SqliteGraphStore(str(tmp_path / "graph.db"))


def make_graph() -> KnowledgeGraph:
    """构造顺序刻意乱序，用于验证确定性排序。"""
    graph = KnowledgeGraph()
    graph.add_entity(
        Entity(
            id="entity-c",
            name="Python",
            type="language",
            properties={"birth_year": 1991},
            source_chunk_ids=["chunk-1"],
        )
    )
    graph.add_entity(Entity(id="entity-a", name="OpenAI", type="company"))
    graph.add_entity(Entity(id="entity-b", name="GPT", type="model"))
    graph.add_entity(Entity(id="entity-d", name="Python SDK", type="model"))
    graph.add_relation(
        Relation(
            id="relation-c",
            source_entity_id="entity-b",
            target_entity_id="entity-a",
            type="owned_by",
            weight=0.8,
        )
    )
    graph.add_relation(
        Relation(
            id="relation-a",
            source_entity_id="entity-a",
            target_entity_id="entity-b",
            type="develops",
            properties={"since": 2018},
            weight=0.9,
        )
    )
    graph.add_relation(
        Relation(
            id="relation-b",
            source_entity_id="entity-c",
            target_entity_id="entity-b",
            type="develops",
            weight=0.7,
        )
    )
    graph.add_relation(
        Relation(
            id="relation-d",
            source_entity_id="entity-d",
            target_entity_id="entity-a",
            type="owned_by",
            weight=0.6,
        )
    )
    return graph


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_get_graph_hit_and_missing(backend: str, tmp_path) -> None:
    """完整图谱命中时返回序列化结果，缺失时返回 None。"""
    graph = make_graph()
    store = make_store(backend, tmp_path)
    store.save(graph, "kb-1")
    service = GraphQueryService(store)

    assert service.get_graph("kb-1") == graph.to_dict()
    assert service.get_graph("missing-kb") is None


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_list_entities_filters_pagination_and_clamps(
    backend: str, tmp_path
) -> None:
    """实体列表支持精确过滤、稳定分页与参数钳制。"""
    graph = make_graph()
    store = make_store(backend, tmp_path)
    store.save(graph, "kb-1")
    service = GraphQueryService(store)

    result = service.list_entities("kb-1")
    assert [item["id"] for item in result["items"]] == [
        "entity-a",
        "entity-b",
        "entity-c",
        "entity-d",
    ]
    assert result["total"] == 4

    result = service.list_entities("kb-1", entity_type="model")
    assert [item["id"] for item in result["items"]] == ["entity-b", "entity-d"]
    assert result["total"] == 2

    result = service.list_entities("kb-1", name="OpenAI")
    assert [item["id"] for item in result["items"]] == ["entity-a"]
    assert result["items"][0]["properties"] == {}
    assert result["items"][0]["source_chunk_ids"] == []

    result = service.list_entities("kb-1", limit=2, offset=1)
    assert [item["id"] for item in result["items"]] == ["entity-b", "entity-c"]
    assert result["total"] == 4
    clamped = service.list_entities("kb-1", limit=0, offset=-10)
    assert [item["id"] for item in clamped["items"]] == ["entity-a"]
    assert service.list_entities("kb-1", limit=0, offset=-10)["total"] == 4
    assert service.list_entities("kb-1", limit=1000)["total"] == 4


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_get_entity_hit_and_missing(backend: str, tmp_path) -> None:
    """实体详情返回完整实体结构。"""
    graph = make_graph()
    store = make_store(backend, tmp_path)
    store.save(graph, "kb-1")
    service = GraphQueryService(store)

    entity = service.get_entity("kb-1", "entity-c")
    assert entity == graph.get_entity("entity-c").__dict__
    assert service.get_entity("kb-1", "missing-entity") is None
    assert service.get_entity("missing-kb", "entity-c") is None


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_entity_neighborhood_directions_and_missing(
    backend: str, tmp_path
) -> None:
    """邻域查询按方向过滤并保持关系 ID 升序。"""
    graph = make_graph()
    store = make_store(backend, tmp_path)
    store.save(graph, "kb-1")
    service = GraphQueryService(store)

    both = service.get_entity_neighborhood("kb-1", "entity-a")
    assert both is not None
    assert both["entity"]["id"] == "entity-a"
    assert [item["id"] for item in both["relations"]] == [
        "relation-a",
        "relation-c",
        "relation-d",
    ]
    assert both["total"] == 3

    outgoing = service.get_entity_neighborhood("kb-1", "entity-a", direction="out")
    assert outgoing is not None
    assert [item["id"] for item in outgoing["relations"]] == ["relation-a"]
    assert outgoing["total"] == 1

    incoming = service.get_entity_neighborhood("kb-1", "entity-a", direction="in")
    assert incoming is not None
    assert [item["id"] for item in incoming["relations"]] == [
        "relation-c",
        "relation-d",
    ]
    assert incoming["total"] == 2
    assert incoming["relations"][0]["properties"] == {}

    assert service.get_entity_neighborhood("kb-1", "missing-entity") is None
    assert service.get_entity_neighborhood("missing-kb", "entity-a") is None


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_list_relations_filters_pagination_and_clamps(
    backend: str, tmp_path
) -> None:
    """关系列表支持实体、类型过滤和稳定分页。"""
    graph = make_graph()
    store = make_store(backend, tmp_path)
    store.save(graph, "kb-1")
    service = GraphQueryService(store)

    result = service.list_relations("kb-1")
    assert [item["id"] for item in result["items"]] == [
        "relation-a",
        "relation-b",
        "relation-c",
        "relation-d",
    ]
    assert result["total"] == 4

    result = service.list_relations("kb-1", entity_id="entity-a")
    assert [item["id"] for item in result["items"]] == [
        "relation-a",
        "relation-c",
        "relation-d",
    ]
    assert result["total"] == 3

    result = service.list_relations("kb-1", relation_type="develops")
    assert [item["id"] for item in result["items"]] == [
        "relation-a",
        "relation-b",
    ]
    assert result["total"] == 2

    result = service.list_relations(
        "kb-1", relation_type="develops", limit=1, offset=1
    )
    assert [item["id"] for item in result["items"]] == ["relation-b"]
    assert result["total"] == 2

    result = service.list_relations("kb-1", limit=0, offset=-10)
    assert [item["id"] for item in result["items"]] == ["relation-a"]
    assert result["total"] == 4
    assert service.list_relations("kb-1", limit=1000)["total"] == 4


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_missing_graph_lists_are_empty(backend: str, tmp_path) -> None:
    """知识库图谱不存在时列表返回空结果。"""
    service = GraphQueryService(make_store(backend, tmp_path))

    assert service.list_entities("missing-kb") == {"items": [], "total": 0}
    assert service.list_relations("missing-kb") == {"items": [], "total": 0}
