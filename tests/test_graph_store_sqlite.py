"""SqliteGraphStore 单元测试。"""

import sqlite3
from datetime import datetime
from threading import Thread

import pytest

from core.graph import Entity, KnowledgeGraph, Relation, SqliteGraphStore


def make_graph(prefix: str = "entity") -> KnowledgeGraph:
    """构造包含嵌套元数据和 ISO8601 时间的测试图谱。"""
    graph = KnowledgeGraph()
    graph.add_entity(
        Entity(
            id="{}-openai".format(prefix),
            name="OpenAI",
            type="organization",
            properties={
                "country": "America",
                "tags": ["AI", "research"],
                "updated_at": datetime(2026, 9, 4, 12, 30, 5),
            },
            source_chunk_ids=["chunk-1", "chunk-2"],
        )
    )
    graph.add_entity(
        Entity(id="{}-gpt".format(prefix), name="GPT", type="model")
    )
    graph.add_relation(
        Relation(
            id="{}-develops".format(prefix),
            source_entity_id="{}-openai".format(prefix),
            target_entity_id="{}-gpt".format(prefix),
            type="develops",
            properties={"since": 2018, "verified_at": datetime(2026, 1, 2, 3, 4, 5)},
            weight=0.75,
        )
    )
    return graph


def with_iso_datetimes(
    graph: KnowledgeGraph, prefix: str = "entity"
) -> KnowledgeGraph:
    """返回 datetime 已归一化为 ISO8601 字符串的期望图谱。"""
    graph.get_entity("{}-openai".format(prefix)).properties["updated_at"] = (
        "2026-09-04T12:30:05"
    )
    graph.relations[0].properties["verified_at"] = "2026-01-02T03:04:05"
    return graph


def test_save_load_round_trip(tmp_path) -> None:
    """保存后读取的数据一致，datetime 按 ISO8601 字符串归一化。"""
    graph = make_graph()
    with SqliteGraphStore(str(tmp_path / "graph.db")) as store:
        store.save(graph, "kb-1")
        loaded = store.load("kb-1")

    expected = with_iso_datetimes(make_graph())

    assert loaded is not None
    assert loaded.to_dict() == expected.to_dict()
    assert loaded.entities == expected.entities
    assert loaded.relations == expected.relations


def test_multiple_knowledge_bases_are_isolated(tmp_path) -> None:
    """写入一个知识库不会覆盖或影响另一个知识库。"""
    first = make_graph("entity-a")
    second = make_graph("entity-b")
    first = with_iso_datetimes(first, "entity-a")
    second = with_iso_datetimes(second, "entity-b")
    store = SqliteGraphStore(str(tmp_path / "graph.db"))

    store.save(first, "kb-a")
    store.save(second, "kb-b")

    assert store.load("kb-a").to_dict() == first.to_dict()
    assert store.load("kb-b").to_dict() == second.to_dict()
    store.delete("kb-a")
    assert store.load("kb-a") is None
    assert store.load("kb-b").to_dict() == second.to_dict()


def test_delete_returns_false_when_missing(tmp_path) -> None:
    """删除不存在和已删除的知识库都返回 False。"""
    store = SqliteGraphStore(str(tmp_path / "graph.db"))
    store.save(make_graph(), "kb-1")

    assert store.delete("kb-1") is True
    assert store.load("kb-1") is None
    assert store.delete("kb-1") is False
    assert store.delete("missing") is False


def test_load_missing_returns_none(tmp_path) -> None:
    """读取不存在的知识库返回 None。"""
    store = SqliteGraphStore(str(tmp_path / "graph.db"))

    assert store.load("missing") is None


def test_schema_version_is_one(tmp_path) -> None:
    """schema_version 表存在且记录当前版本 1。"""
    database_path = str(tmp_path / "graph.db")
    SqliteGraphStore(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        version = connection.execute("SELECT version FROM schema_version").fetchone()[0]

    assert "schema_version" in tables
    assert "knowledge_graphs" in tables
    assert version == 1


def test_save_replaces_old_graph_atomically(tmp_path) -> None:
    """重复保存整体替换旧图，失败时旧图不被半写破坏。"""
    old_graph = make_graph()
    new_graph = make_graph()
    database_path = str(tmp_path / "graph.db")
    store = SqliteGraphStore(database_path)
    store.save(old_graph, "kb-1")

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TRIGGER fail_graph_insert
            BEFORE INSERT ON knowledge_graphs
            BEGIN
                SELECT RAISE(ABORT, 'mock insert failure');
            END
            """
        )

    with pytest.raises(sqlite3.IntegrityError, match="mock insert failure"):
        store.save(new_graph, "kb-1")

    expected = with_iso_datetimes(make_graph())
    loaded = store.load("kb-1")
    assert loaded is not None
    assert loaded.to_dict() == expected.to_dict()
    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP TRIGGER fail_graph_insert")
    store.save(KnowledgeGraph(), "kb-1")
    assert store.load("kb-1").to_dict() == {"entities": [], "relations": []}


def test_store_instance_can_be_used_across_threads(tmp_path) -> None:
    """check_same_thread=False 支持同一 store 实例跨线程访问。"""
    store = SqliteGraphStore(str(tmp_path / "graph.db"))
    errors = []

    def load_graph() -> None:
        try:
            store.load("missing")
        except Exception as error:
            errors.append(error)

    thread = Thread(target=load_graph)
    thread.start()
    thread.join()

    assert errors == []
