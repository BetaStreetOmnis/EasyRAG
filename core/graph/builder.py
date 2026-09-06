"""知识图谱构建服务。"""

from typing import Any, Dict, List, Tuple

from .extractor import LLMEntityRelationExtractor
from .models import GraphStore


class GraphBuildService:
    """串联文本抽取与存储，构建指定知识库的图谱。"""

    def __init__(
        self,
        extractor: LLMEntityRelationExtractor,
        store: GraphStore,
    ) -> None:
        """初始化图谱构建依赖。

        Args:
            extractor: 负责从文本 chunk 抽取实体与关系的抽取器。
            store: 任意实现 ``GraphStore`` 接口的图谱存储实例。
        """
        self._extractor = extractor
        self._store = store

    def build(
        self, kb_name: str, chunks: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """抽取文本 chunk 并原子替换指定知识库的图谱。

        Args:
            kb_name: 知识库名称。
            chunks: ``(chunk_id, text)`` 列表。

        Returns:
            构建统计信息。除基础统计外，还会并入抽取器最近一次
            ``total_chunks``、``succeeded_chunks``、``failed_chunks``、
            ``chunk_errors`` 等运行字段。

        Raises:
            ValueError: 知识库没有可用的文本块。
        """
        if not chunks:
            raise ValueError("知识库中没有可用的文本块")

        graph = self._extractor.extract_from_chunks(chunks, strict=False)
        self._store.save(graph, kb_name)

        stats: Dict[str, Any] = {
            # 知识库名称
            "kb_name": kb_name,
            # 参与构建的文本块总数
            "chunks_total": len(chunks),
            # 最终保存的去重后实体数
            "entities": len(graph.entities),
            # 最终保存的关系数
            "relations": len(graph.relations),
        }
        stats.update(self._extractor.last_run_stats)
        return stats

    @staticmethod
    def limit_chunks(
        chunks: List[Tuple[str, str]], max_chunks: int
    ) -> List[Tuple[str, str]]:
        """按上限截断待构建 chunk，正数生效，0 表示不限制。"""
        if max_chunks < 0:
            raise ValueError("max_chunks 不能小于 0")
        return chunks if max_chunks == 0 else chunks[:max_chunks]

    def build_from_documents(
        self, kb_name: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """将本仓库存储的 chunk 字典转换后构建图谱。

        Args:
            kb_name: 知识库名称。
            documents: ``add_documents`` 保存的 chunk 字典列表。

        Returns:
            构建统计信息，字段与 :meth:`build` 一致。

        Raises:
            ValueError: 知识库没有可用的文本块。
        """
        chunks = [
            (str(document.get("id", "doc-{}".format(index))), str(document["text"]))
            for index, document in enumerate(documents)
        ]
        return self.build(kb_name, chunks)
