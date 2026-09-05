"""知识图谱查询服务。"""

from typing import Any, Dict, Optional

from .models import Entity, GraphStore, Relation


class GraphQueryService:
    """提供面向知识图谱的纯内存查询能力。"""

    def __init__(self, store: GraphStore) -> None:
        """初始化图谱存储后端。

        Args:
            store: 任意实现了 ``GraphStore`` 接口的存储实例。
        """
        self._store = store

    def get_graph(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取指定知识库的完整图谱。"""
        graph = self._store.load(kb_id)
        if graph is None:
            return None
        return graph.to_dict()

    def list_entities(
        self,
        kb_id: str,
        entity_type: Optional[str] = None,
        name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """分页查询实体，并支持类型与名称精确过滤。"""
        graph = self._store.load(kb_id)
        if graph is None:
            return {"items": [], "total": 0}

        entities = sorted(graph.entities.values(), key=lambda entity: entity.id)
        entities = [
            entity
            for entity in entities
            if (entity_type is None or entity.type == entity_type)
            and (name is None or entity.name == name)
        ]
        actual_limit = self._clamp_limit(limit)
        actual_offset = self._clamp_offset(offset)
        return {
            "items": [
                self._entity_to_dict(entity)
                for entity in entities[actual_offset : actual_offset + actual_limit]
            ],
            "total": len(entities),
        }

    def get_entity(self, kb_id: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """按 ID 查询实体详情。"""
        graph = self._store.load(kb_id)
        if graph is None:
            return None
        entity = graph.get_entity(entity_id)
        if entity is None:
            return None
        return self._entity_to_dict(entity)

    def get_entity_neighborhood(
        self,
        kb_id: str,
        entity_id: str,
        direction: str = "both",
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """查询实体详情及其一度关系。"""
        graph = self._store.load(kb_id)
        if graph is None:
            return None
        entity = graph.get_entity(entity_id)
        if entity is None:
            return None

        relations = sorted(
            graph.get_relations(entity_id),
            key=lambda relation: relation.id,
        )
        relations = [
            relation
            for relation in relations
            if self._relation_matches_direction(relation, entity_id, direction)
        ]
        actual_limit = self._clamp_limit(limit)
        actual_offset = self._clamp_offset(offset)
        return {
            "entity": self._entity_to_dict(entity),
            "relations": [
                self._relation_to_dict(relation)
                for relation in relations[
                    actual_offset : actual_offset + actual_limit
                ]
            ],
            "total": len(relations),
        }

    def list_relations(
        self,
        kb_id: str,
        entity_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """分页查询关系，并支持实体与类型精确过滤。"""
        graph = self._store.load(kb_id)
        if graph is None:
            return {"items": [], "total": 0}

        relations = sorted(
            graph.get_relations(entity_id),
            key=lambda relation: relation.id,
        )
        relations = [
            relation
            for relation in relations
            if relation_type is None or relation.type == relation_type
        ]
        actual_limit = self._clamp_limit(limit)
        actual_offset = self._clamp_offset(offset)
        return {
            "items": [
                self._relation_to_dict(relation)
                for relation in relations[
                    actual_offset : actual_offset + actual_limit
                ]
            ],
            "total": len(relations),
        }

    @staticmethod
    def _entity_to_dict(entity: Entity) -> Dict[str, Any]:
        """转换实体为 JSON 友好结构。"""
        return {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "properties": dict(entity.properties),
            "source_chunk_ids": list(entity.source_chunk_ids),
        }

    @staticmethod
    def _relation_to_dict(relation: Relation) -> Dict[str, Any]:
        """转换关系为 JSON 友好结构。"""
        return {
            "id": relation.id,
            "source_entity_id": relation.source_entity_id,
            "target_entity_id": relation.target_entity_id,
            "type": relation.type,
            "properties": dict(relation.properties),
            "weight": relation.weight,
        }

    @staticmethod
    def _relation_matches_direction(
        relation: Relation, entity_id: str, direction: str
    ) -> bool:
        """判断关系是否匹配指定方向。"""
        if direction == "out":
            return relation.source_entity_id == entity_id
        if direction == "in":
            return relation.target_entity_id == entity_id
        if direction == "both":
            return (
                relation.source_entity_id == entity_id
                or relation.target_entity_id == entity_id
            )
        return False

    @staticmethod
    def _clamp_limit(limit: int) -> int:
        """将分页大小钳制到有效区间。"""
        return min(max(limit, 1), 500)

    @staticmethod
    def _clamp_offset(offset: int) -> int:
        """将分页偏移钳制为非负整数。"""
        return max(offset, 0)
