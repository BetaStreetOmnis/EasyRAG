"""知识图谱核心数据模型。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Entity:
    """表示知识图谱中的一个节点。"""

    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_chunk_ids: List[str] = field(default_factory=list)


@dataclass
class Relation:
    """表示知识图谱中从起点实体指向终点实体的有向边。"""

    id: str
    source_entity_id: str
    target_entity_id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


class KnowledgeGraph:
    """维护实体和关系的内存容器。"""

    def __init__(self) -> None:
        """初始化内部实体表与关系表。"""
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}

    @property
    def entities(self) -> Dict[str, Entity]:
        """返回实体表的浅拷贝，避免外部替换内部容器。"""
        return dict(self._entities)

    @property
    def relations(self) -> List[Relation]:
        """按加入顺序返回关系列表。"""
        return list(self._relations.values())

    def add_entity(self, entity: Entity) -> str:
        """加入实体，并合并同名同类型的既有实体。

        Args:
            entity: 待加入的实体。

        Returns:
            图谱中实际保存的实体 ID。

        Raises:
            ValueError: 实体 ID 已存在但名称或类型不一致。
        """
        existing_entity = self._entities.get(entity.id)
        if existing_entity is None:
            copied_entity = Entity(
                id=entity.id,
                name=entity.name,
                type=entity.type,
                properties=dict(entity.properties),
                source_chunk_ids=list(entity.source_chunk_ids),
            )
            self._entities[copied_entity.id] = copied_entity
            return copied_entity.id

        if existing_entity.name != entity.name or existing_entity.type != entity.type:
            raise ValueError(
                "实体 ID 已存在，且名称或类型与既有实体不一致: {}".format(entity.id)
            )

        existing_entity.properties.update(entity.properties)
        for chunk_id in entity.source_chunk_ids:
            if chunk_id not in existing_entity.source_chunk_ids:
                existing_entity.source_chunk_ids.append(chunk_id)
        return existing_entity.id

    def add_relation(self, relation: Relation) -> str:
        """加入关系，并确保两个端点实体均存在。

        Args:
            relation: 待加入的有向关系。

        Returns:
            图谱中实际保存的关系 ID。

        Raises:
            ValueError: 起点或终点实体不存在。
        """
        missing_entity_ids = [
            entity_id
            for entity_id in (relation.source_entity_id, relation.target_entity_id)
            if entity_id not in self._entities
        ]
        if missing_entity_ids:
            raise ValueError(
                "关系端点实体不存在: {}".format(", ".join(missing_entity_ids))
            )

        copied_relation = Relation(
            id=relation.id,
            source_entity_id=relation.source_entity_id,
            target_entity_id=relation.target_entity_id,
            type=relation.type,
            properties=dict(relation.properties),
            weight=relation.weight,
        )
        self._relations[copied_relation.id] = copied_relation
        return copied_relation.id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """按 ID 查询实体。"""
        return self._entities.get(entity_id)

    def get_relations(self, entity_id: Optional[str] = None) -> List[Relation]:
        """查询关系，并可按任一端点实体过滤。"""
        if entity_id is None:
            return list(self._relations.values())

        return [
            relation
            for relation in self._relations.values()
            if relation.source_entity_id == entity_id
            or relation.target_entity_id == entity_id
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为 JSON 友好的字典结构。"""
        return {
            "entities": [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type,
                    "properties": dict(entity.properties),
                    "source_chunk_ids": list(entity.source_chunk_ids),
                }
                for entity in self._entities.values()
            ],
            "relations": [
                {
                    "id": relation.id,
                    "source_entity_id": relation.source_entity_id,
                    "target_entity_id": relation.target_entity_id,
                    "type": relation.type,
                    "properties": dict(relation.properties),
                    "weight": relation.weight,
                }
                for relation in self._relations.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        """从字典结构恢复知识图谱。

        Args:
            data: `to_dict` 输出的数据。

        Returns:
            反序列化后的知识图谱。
        """
        graph = cls()
        for entity_data in data.get("entities", []):
            graph.add_entity(
                Entity(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    type=entity_data["type"],
                    properties=dict(entity_data.get("properties", {})),
                    source_chunk_ids=list(entity_data.get("source_chunk_ids", [])),
                )
            )

        for relation_data in data.get("relations", []):
            graph.add_relation(
                Relation(
                    id=relation_data["id"],
                    source_entity_id=relation_data["source_entity_id"],
                    target_entity_id=relation_data["target_entity_id"],
                    type=relation_data["type"],
                    properties=dict(relation_data.get("properties", {})),
                    weight=float(relation_data.get("weight", 1.0)),
                )
            )
        return graph


class GraphStore(ABC):
    """定义知识图谱存储后端接口。"""

    @abstractmethod
    def save(self, graph: KnowledgeGraph, kb_id: str) -> None:
        """保存指定知识库的图谱。"""

    @abstractmethod
    def load(self, kb_id: str) -> Optional[KnowledgeGraph]:
        """读取指定知识库的图谱，不存在时返回 None。"""

    @abstractmethod
    def delete(self, kb_id: str) -> bool:
        """删除指定知识库的图谱，并返回是否删除成功。"""


class InMemoryGraphStore(GraphStore):
    """基于进程内字典的最小图谱存储实现。"""

    def __init__(self) -> None:
        """初始化内部存储表。"""
        self._graphs: Dict[str, Dict[str, Any]] = {}

    def save(self, graph: KnowledgeGraph, kb_id: str) -> None:
        """以序列化快照保存图谱并覆盖旧版本。"""
        self._graphs[kb_id] = graph.to_dict()

    def load(self, kb_id: str) -> Optional[KnowledgeGraph]:
        """读取指定图谱的独立快照。"""
        graph_data = self._graphs.get(kb_id)
        if graph_data is None:
            return None
        return KnowledgeGraph.from_dict(graph_data)

    def delete(self, kb_id: str) -> bool:
        """删除指定图谱并返回是否删除成功。"""
        return self._graphs.pop(kb_id, None) is not None
