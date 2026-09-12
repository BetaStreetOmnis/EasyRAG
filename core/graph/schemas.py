"""知识图谱接口响应模型。"""

from typing import Any, Dict, List

from pydantic import BaseModel


class GraphEntityResponse(BaseModel):
    """表示图谱实体接口响应。"""

    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    source_chunk_ids: List[str]


class GraphRelationResponse(BaseModel):
    """表示图谱关系接口响应。"""

    id: str
    source_entity_id: str
    target_entity_id: str
    type: str
    properties: Dict[str, Any]
    weight: float


class GraphDataResponse(BaseModel):
    """表示完整图谱接口响应。"""

    entities: List[GraphEntityResponse]
    relations: List[GraphRelationResponse]


class GraphDeleteResponse(BaseModel):
    """表示删除图谱接口响应。"""

    status: str
    message: str


class GraphEntityListResponse(BaseModel):
    """表示实体列表接口响应。"""

    items: List[GraphEntityResponse]
    total: int


class GraphEntityDetailResponse(BaseModel):
    """表示实体详情接口响应。"""

    entity: GraphEntityResponse
    relations: List[GraphRelationResponse]
    total: int


class GraphRelationListResponse(BaseModel):
    """表示关系列表接口响应。"""

    items: List[GraphRelationResponse]
    total: int


class GraphBuildStats(BaseModel):
    """表示图谱构建统计信息。"""

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

    status: str
    data: GraphBuildStats
