"""知识图谱数据模型单元测试。"""

import json

import pytest

from core.graph import Entity, InMemoryGraphStore, KnowledgeGraph, Relation


def make_graph() -> KnowledgeGraph:
    """构造包含两个实体和一条关系的测试图谱。"""
    graph = KnowledgeGraph()
    graph.add_entity(
        Entity(
            id="entity-openai",
            name="OpenAI",
            type="organization",
            properties={"country": "America"},
            source_chunk_ids=["chunk-1"],
        )
    )
    graph.add_entity(
        Entity(
            id="entity-gpt",
            name="GPT",
            type="model",
            properties={"version": 4},
            source_chunk_ids=["chunk-1"],
        )
    )
    graph.add_relation(
        Relation(
            id="relation-develops",
            source_entity_id="entity-openai",
            target_entity_id="entity-gpt",
            type="develops",
            properties={"since": 2018},
            weight=0.8,
        )
    )
    return graph


def test_add_and_get_entity() -> None:
    """实体加入图谱后可按 ID 查询，并保持传入数据一致。"""
    graph = KnowledgeGraph()
    entity = Entity(
        id="entity-easyrag",
        name="EasyRAG",
        type="project",
        properties={"language": "Python"},
        source_chunk_ids=["chunk-1", "chunk-2"],
    )

    assert graph.add_entity(entity) == "entity-easyrag"
    assert graph.get_entity("entity-easyrag") == entity
    assert graph.entities == {"entity-easyrag": entity}
    assert graph.get_entity("missing") is None


def test_merge_entities_with_same_id_name_and_type() -> None:
    """重复实体按 ID 去重，并合并属性与来源 chunk。"""
    graph = KnowledgeGraph()
    first = Entity(
        id="entity-openai",
        name="OpenAI",
        type="organization",
        properties={"country": "America", "city": "San Francisco"},
        source_chunk_ids=["chunk-1", "chunk-2"],
    )
    second = Entity(
        id="entity-openai",
        name="OpenAI",
        type="organization",
        properties={"city": "San Francisco", "founded": 2015},
        source_chunk_ids=["chunk-2", "chunk-3"],
    )

    graph.add_entity(first)
    graph.add_entity(second)

    merged_entity = graph.get_entity("entity-openai")
    assert merged_entity is not None
    assert merged_entity.properties == {
        "country": "America",
        "city": "San Francisco",
        "founded": 2015,
    }
    assert merged_entity.source_chunk_ids == ["chunk-1", "chunk-2", "chunk-3"]
    assert len(graph.entities) == 1


def test_add_relation_requires_existing_entities() -> None:
    """关系任一端点不存在时必须拒绝写入。"""
    graph = KnowledgeGraph()
    graph.add_entity(
        Entity(id="entity-openai", name="OpenAI", type="organization")
    )
    relation = Relation(
        id="relation-invalid",
        source_entity_id="entity-openai",
        target_entity_id="entity-missing",
        type="develops",
    )

    with pytest.raises(ValueError) as error:
        graph.add_relation(relation)

    assert "entity-missing" in str(error.value)
    assert graph.relations == []


def test_get_relations_filtered_by_entity() -> None:
    """实体过滤应同时覆盖作为起点和终点的关系。"""
    graph = make_graph()
    graph.add_entity(
        Entity(id="entity-user", name="User", type="role")
    )
    graph.add_relation(
        Relation(
            id="relation-uses",
            source_entity_id="entity-user",
            target_entity_id="entity-gpt",
            type="uses",
        )
    )

    assert [relation.id for relation in graph.get_relations("entity-gpt")] == [
        "relation-develops",
        "relation-uses",
    ]
    assert [relation.id for relation in graph.get_relations("entity-user")] == [
        "relation-uses",
    ]
    assert len(graph.get_relations()) == 2


def test_json_round_trip() -> None:
    """图谱字典经 JSON 文本往返后保持数据一致。"""
    graph = make_graph()
    graph_data = json.loads(json.dumps(graph.to_dict(), ensure_ascii=False))

    restored_graph = KnowledgeGraph.from_dict(graph_data)

    assert restored_graph.to_dict() == graph.to_dict()
    assert restored_graph.entities == graph.entities
    assert restored_graph.relations == graph.relations


def test_in_memory_graph_store_save_load_and_delete() -> None:
    """内存存储支持保存、读取、覆盖与删除。"""
    store = InMemoryGraphStore()
    graph = make_graph()

    assert store.load("kb-1") is None
    store.save(graph, "kb-1")
    loaded_graph = store.load("kb-1")

    assert loaded_graph is not None
    assert loaded_graph.to_dict() == graph.to_dict()

    graph.add_entity(
        Entity(id="entity-user", name="User", type="role")
    )
    assert "entity-user" not in store.load("kb-1").entities

    assert store.delete("kb-1") is True
    assert store.load("kb-1") is None
    assert store.delete("kb-1") is False
