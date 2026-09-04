"""基于 SQLite 的知识图谱持久化存储。"""

import dataclasses
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Optional

from .models import Entity, GraphStore, KnowledgeGraph, Relation


SCHEMA_VERSION = 1


def _to_json_value(value: Any) -> Any:
    """递归转换为 JSON 可序列化数据，并将时间转为 ISO8601。"""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_value(item) for item in value]
    return value


def _entity_to_dict(entity: Entity) -> Dict[str, Any]:
    """将实体转换为 JSON 友好字典。"""
    return _to_json_value(dataclasses.asdict(entity))


def _entity_from_dict(data: Dict[str, Any]) -> Entity:
    """从 JSON 字典恢复实体。"""
    return Entity(
        id=data["id"],
        name=data["name"],
        type=data["type"],
        properties=dict(data.get("properties", {})),
        source_chunk_ids=list(data.get("source_chunk_ids", [])),
    )


def _relation_to_dict(relation: Relation) -> Dict[str, Any]:
    """将有向关系转换为 JSON 友好字典。"""
    return _to_json_value(dataclasses.asdict(relation))


def _relation_from_dict(data: Dict[str, Any]) -> Relation:
    """从 JSON 字典恢复有向关系。"""
    return Relation(
        id=data["id"],
        source_entity_id=data["source_entity_id"],
        target_entity_id=data["target_entity_id"],
        type=data["type"],
        properties=dict(data.get("properties", {})),
        weight=float(data.get("weight", 1.0)),
    )


def _knowledge_graph_to_dict(graph: KnowledgeGraph) -> Dict[str, Any]:
    """将完整图谱转换为稳定 JSON 字典。"""
    return {
        "entities": [_entity_to_dict(entity) for entity in graph.entities.values()],
        "relations": [_relation_to_dict(relation) for relation in graph.relations],
    }


def _knowledge_graph_from_dict(data: Dict[str, Any]) -> KnowledgeGraph:
    """从 JSON 字典恢复完整图谱。"""
    graph = KnowledgeGraph()
    for entity_data in data.get("entities", []):
        graph.add_entity(_entity_from_dict(entity_data))
    for relation_data in data.get("relations", []):
        graph.add_relation(_relation_from_dict(relation_data))
    return graph


class SqliteGraphStore(GraphStore):
    """使用 SQLite 文件保存知识图谱的存储后端。

    每次操作都会创建独立连接并立即关闭，因此同一个 store 实例可以在多个
    线程中串行或并发使用；SQLite 自身的锁与 busy timeout 负责文件级并发。
    """

    def __init__(self, path: str = "easyrag_graph.db") -> None:
        """初始化数据库文件和当前版本的表结构。

        Args:
            path: SQLite 数据库文件路径。

        Raises:
            RuntimeError: 已存在数据库使用不支持的 schema 版本。
        """
        self._path = path
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        """创建带基础超时配置的 SQLite 连接。"""
        connection = sqlite3.connect(
            self._path, timeout=30.0, check_same_thread=False
        )
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def _initialize_schema(self) -> None:
        """创建 schema 表和图谱快照表，并写入当前版本。"""
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, ?)",
                (SCHEMA_VERSION,),
            )
            version = connection.execute(
                "SELECT version FROM schema_version WHERE id = 1"
            ).fetchone()[0]
            if version != SCHEMA_VERSION:
                raise RuntimeError(
                    "不支持的图谱数据库 schema 版本: {}".format(version)
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_graphs (
                    kb_id TEXT PRIMARY KEY,
                    graph_data TEXT NOT NULL
                )
                """
            )

    def save(self, graph: KnowledgeGraph, kb_id: str) -> None:
        """以单事务整体替换指定知识库的图谱。

        Args:
            graph: 待保存的知识图谱。
            kb_id: 知识库 ID。

        Raises:
            sqlite3.Error: 事务失败时已回滚，旧图谱保持不变。
        """
        graph_data = json.dumps(
            _knowledge_graph_to_dict(graph),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "DELETE FROM knowledge_graphs WHERE kb_id = ?", (kb_id,)
            )
            connection.execute(
                "INSERT INTO knowledge_graphs (kb_id, graph_data) VALUES (?, ?)",
                (kb_id, graph_data),
            )

    def load(self, kb_id: str) -> Optional[KnowledgeGraph]:
        """读取指定知识库的图谱，不存在时返回 None。"""
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT graph_data FROM knowledge_graphs WHERE kb_id = ?", (kb_id,)
            ).fetchone()
        if row is None:
            return None
        return _knowledge_graph_from_dict(json.loads(row[0]))

    def delete(self, kb_id: str) -> bool:
        """删除指定知识库的图谱，并返回是否删除成功。"""
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "DELETE FROM knowledge_graphs WHERE kb_id = ?", (kb_id,)
            )
            return cursor.rowcount > 0

    def __enter__(self) -> "SqliteGraphStore":
        """进入上下文管理器。"""
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """退出上下文管理器。

        连接在每次操作后均已关闭，这里无需额外释放资源。
        """
