"""知识图谱接口响应模型。"""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class GraphEntityResponse(BaseModel):
    """表示图谱实体接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ent-001",
                "name": "张三",
                "type": "人物",
                "properties": {"职位": "算法工程师"},
                "source_chunk_ids": ["chunk-001", "chunk-002"],
            }
        }
    )

    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    source_chunk_ids: List[str]


class GraphRelationResponse(BaseModel):
    """表示图谱关系接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rel-001",
                "source_entity_id": "ent-001",
                "target_entity_id": "ent-002",
                "type": "任职于",
                "properties": {"职位": "首席科学家"},
                "weight": 1.5,
            }
        }
    )

    id: str
    source_entity_id: str
    target_entity_id: str
    type: str
    properties: Dict[str, Any]
    weight: float


class GraphDataResponse(BaseModel):
    """表示完整图谱接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entities": [
                    {
                        "id": "ent-001",
                        "name": "张三",
                        "type": "人物",
                        "properties": {"职位": "算法工程师"},
                        "source_chunk_ids": ["chunk-001", "chunk-002"],
                    },
                    {
                        "id": "ent-002",
                        "name": "贝塔科技",
                        "type": "公司",
                        "properties": {"成立年份": 2015},
                        "source_chunk_ids": ["chunk-003"],
                    },
                ],
                "relations": [
                    {
                        "id": "rel-001",
                        "source_entity_id": "ent-001",
                        "target_entity_id": "ent-002",
                        "type": "任职于",
                        "properties": {"职位": "首席科学家"},
                        "weight": 1.5,
                    }
                ],
            }
        }
    )

    entities: List[GraphEntityResponse]
    relations: List[GraphRelationResponse]


class GraphDeleteResponse(BaseModel):
    """表示删除图谱接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "图谱删除成功",
            }
        }
    )

    status: str
    message: str


class GraphEntityListResponse(BaseModel):
    """表示实体列表接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "ent-001",
                        "name": "张三",
                        "type": "人物",
                        "properties": {"职位": "算法工程师"},
                        "source_chunk_ids": ["chunk-001", "chunk-002"],
                    },
                    {
                        "id": "ent-002",
                        "name": "贝塔科技",
                        "type": "公司",
                        "properties": {"成立年份": 2015},
                        "source_chunk_ids": ["chunk-003"],
                    },
                ],
                "total": 2,
            }
        }
    )

    items: List[GraphEntityResponse]
    total: int


class GraphEntityDetailResponse(BaseModel):
    """表示实体详情接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entity": {
                    "id": "ent-001",
                    "name": "张三",
                    "type": "人物",
                    "properties": {"职位": "算法工程师"},
                    "source_chunk_ids": ["chunk-001", "chunk-002"],
                },
                "relations": [
                    {
                        "id": "rel-001",
                        "source_entity_id": "ent-001",
                        "target_entity_id": "ent-002",
                        "type": "任职于",
                        "properties": {"职位": "首席科学家"},
                        "weight": 1.5,
                    }
                ],
                "total": 1,
            }
        }
    )

    entity: GraphEntityResponse
    relations: List[GraphRelationResponse]
    total: int


class GraphRelationListResponse(BaseModel):
    """表示关系列表接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "rel-001",
                        "source_entity_id": "ent-001",
                        "target_entity_id": "ent-002",
                        "type": "任职于",
                        "properties": {"职位": "首席科学家"},
                        "weight": 1.5,
                    }
                ],
                "total": 1,
            }
        }
    )

    items: List[GraphRelationResponse]
    total: int


class GraphBuildStats(BaseModel):
    """表示图谱构建统计信息。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kb_name": "产品知识库",
                "chunks_total": 10,
                "entities": 12,
                "relations": 18,
                "total_chunks": 10,
                "succeeded_chunks": 9,
                "failed_chunks": ["chunk-010"],
                "chunk_errors": {"chunk-010": "文档解析失败"},
                "total_entities": 12,
                "total_relations": 18,
            }
        }
    )

    kb_name: str
    chunks_total: int
    entities: int
    relations: int
    total_chunks: int
    succeeded_chunks: int
    failed_chunks: List[str]
    chunk_errors: Dict[str, str]
    total_entities: int
    total_relations: int


class GraphBuildResponse(BaseModel):
    """表示图谱构建接口响应。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {
                    "kb_name": "产品知识库",
                    "chunks_total": 10,
                    "entities": 12,
                    "relations": 18,
                    "total_chunks": 10,
                    "succeeded_chunks": 9,
                    "failed_chunks": ["chunk-010"],
                    "chunk_errors": {"chunk-010": "文档解析失败"},
                    "total_entities": 12,
                    "total_relations": 18,
                },
            }
        }
    )

    status: str
    data: GraphBuildStats
