"""知识图谱删除能力离线单元测试。"""

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
    """构造包含实体和关系的最小图谱。"""
    graph = KnowledgeGraph()
    graph.add_entity(
        Entity(
            id="entity-1",
            name="OpenAI",
            type="company",
            source_chunk_ids=["chunk-1"],
        )
    )
    graph.add_entity(Entity(id="entity-2", name="GPT", type="model"))
    graph.add_relation(
        Relation(
            id="relation-1",
            source_entity_id="entity-1",
            target_entity_id="entity-2",
            type="develops",
            weight=0.9,
        )
    )
    return graph


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_delete_graph_hit_and_missing(backend: str, tmp_path) -> None:
    """删除已存在图谱生效，删除缺失图谱返回 False。"""
    store = make_store(backend, tmp_path)
    store.save(make_graph(), "kb-1")
    service = GraphQueryService(store)

    assert service.delete_graph("kb-1") is True
    assert service.get_graph("kb-1") is None
    assert service.list_entities("kb-1") == {"items": [], "total": 0}
    assert service.delete_graph("kb-1") is False


def test_sqlite_delete_persists_across_store_instances(tmp_path) -> None:
    """SQLite 图谱删除后，新实例读取仍为空。"""
    db_path = str(tmp_path / "graph.db")
    store_a = SqliteGraphStore(db_path)
    store_a.save(make_graph(), "kb-1")
    service_a = GraphQueryService(store_a)

    assert service_a.delete_graph("kb-1") is True

    store_b = SqliteGraphStore(db_path)
    service_b = GraphQueryService(store_b)
    assert service_b.get_graph("kb-1") is None
