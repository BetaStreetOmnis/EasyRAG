"""基于 LLM 的知识图谱实体关系抽取器。"""

import json
import logging
import re
from hashlib import sha1
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from core.graph.models import Entity, KnowledgeGraph, Relation

logger = logging.getLogger(__name__)


class GraphExtractionError(Exception):
    """表示图谱抽取失败，或模型输出重试后仍不可用。"""


class LLMEntityRelationExtractor:
    """调用 LLM 从文本 chunk 中抽取实体与关系。"""

    def __init__(
        self,
        llm_client: Any = None,
        max_retries: int = 2,
        temperature: float = 0.0,
        max_entities_per_chunk: int = 50,
        max_relations_per_chunk: int = 80,
        entity_types: Optional[Iterable[str]] = None,
        max_chunk_chars: int = 6000,
    ) -> None:
        """初始化抽取配置，默认模型客户端在首次调用时惰性创建。

        Args:
            llm_client: 兼容 ``generate_response`` 的模型客户端。
            max_retries: JSON 结构无效时的最大额外调用次数。
            temperature: 抽取温度。
            max_entities_per_chunk: 单个 chunk 允许保存的最大实体数。
            max_relations_per_chunk: 单个 chunk 允许保存的最大关系数。
            entity_types: 实体类型白名单；为 ``None`` 时不过滤。
            max_chunk_chars: 输入文本最大字符数，超出部分先截断。
        """
        self._llm_client = llm_client
        self._max_retries = max_retries
        self._temperature = temperature
        self._max_entities_per_chunk = max_entities_per_chunk
        self._max_relations_per_chunk = max_relations_per_chunk
        self._entity_types = set(entity_types) if entity_types is not None else None
        self._max_chunk_chars = max_chunk_chars
        self.last_run_stats: Dict[str, Any] = {}

    @staticmethod
    def _entity_id(name: str, entity_type: str) -> str:
        """生成确定性实体 ID。"""
        digest = sha1("{}|{}".format(name, entity_type).encode("utf-8")).hexdigest()[:12]
        return "entity-" + digest

    @staticmethod
    def _relation_id(source: str, relation_type: str, target: str) -> str:
        """生成确定性关系 ID。"""
        key = "{}|{}|{}".format(source, relation_type, target)
        return "relation-" + sha1(key.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """递归合并属性字典，保持目标字典可变。"""
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                LLMEntityRelationExtractor._deep_merge(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def _extract_balanced_json(text: str) -> Optional[str]:
        """截取文本中首个语法上平衡的 JSON 对象片段。"""
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                escaped, in_string = LLMEntityRelationExtractor._scan_json_string(
                    char, escaped, in_string
                )
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        return None

    @staticmethod
    def _scan_json_string(char: str, escaped: bool, in_string: bool) -> Tuple[bool, bool]:
        """更新 JSON 字符串扫描状态。"""
        if escaped:
            return False, in_string
        if char == "\\":
            return True, in_string
        if char == '"':
            return escaped, False
        return escaped, in_string

    @classmethod
    def _load_json_object(cls, response: str) -> Optional[Dict[str, Any]]:
        """容错解析模型输出中的 JSON 对象。"""
        cleaned = response.strip()
        fence_pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
        fence_match = fence_pattern.match(cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        try:
            candidate = cleaned if cleaned.startswith("{") else cls._extract_balanced_json(cleaned)
            if candidate is None:
                return None
            data = json.loads(candidate)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _build_prompt(self, text: str, truncated: bool, previous_error: Optional[str]) -> str:
        """构造中文实体关系抽取提示词。"""
        prompt = """你是一个严谨的知识图谱信息抽取器。请从给定文本中抽取实体和关系。

要求：
1. 只输出一个 JSON 对象，不加任何解释，不使用 Markdown 代码块。
2. 实体名和实体类型可使用中文或英文；关系的 source 和 target 必须严格使用实体列表中的实体名。
3. properties 与 weight 可省略；weight 必须是数字。
4. 若无法抽取实体或关系，输出 {"entities": [], "relations": []}。

输出 JSON schema：
{"entities": [{"name": "...", "type": "...", "properties": {}}],
 "relations": [{"source": "...", "target": "...", "type": "...", "weight": 0.9, "properties": {}}]}
"""
        if truncated:
            prompt += "\n注意：以下文本超过输入上限，已截断。\n"
        prompt += "\n待抽取文本：\n" + text
        if previous_error:
            prompt += "\n\n上一轮输出无效，错误原因：{}\n请修正后只输出一个合法 JSON 对象。".format(previous_error)
        return prompt

    def _get_llm_client(self) -> Any:
        """返回注入客户端，或惰性初始化 OpenAI 兼容客户端。"""
        if self._llm_client is not None:
            return self._llm_client
        try:
            from core.llm.openai_llm_model import get_openai_model

            self._llm_client = get_openai_model()
            return self._llm_client
        except Exception as error:
            raise GraphExtractionError("初始化 OpenAI 兼容模型失败: {}".format(error)) from error

    @staticmethod
    def _normalize_weight(raw_weight: Any, relation_id: str, chunk_id: str) -> float:
        """校验关系权重，非法值回退并越界值钳制。"""
        if isinstance(raw_weight, bool):
            logger.warning("chunk=%s 关系 %s weight 非法，回退为 1.0", chunk_id, relation_id)
            return 1.0
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            logger.warning("chunk=%s 关系 %s weight 非法，回退为 1.0", chunk_id, relation_id)
            return 1.0
        if weight < 0.0:
            logger.warning("chunk=%s 关系 %s weight 低于下限，钳制为 0.0", chunk_id, relation_id)
            return 0.0
        if weight > 1.0:
            logger.warning("chunk=%s 关系 %s weight 高于上限，钳制为 1.0", chunk_id, relation_id)
            return 1.0
        return weight

    def _parse_and_validate(
        self, output: str, chunk_id: str
    ) -> Tuple[Optional[KnowledgeGraph], Optional[str]]:
        """解析并校验模型输出，返回图谱与结构错误原因。"""
        data = self._load_json_object(output)
        if data is None:
            return None, "JSON 解析失败或不存在平衡 JSON 对象"
        if "entities" not in data or "relations" not in data:
            return None, "顶层结构不是包含 entities 和 relations 的 JSON 对象"
        if not isinstance(data["entities"], list) or not isinstance(data["relations"], list):
            return None, "entities 或 relations 不是数组"

        entities = self._parse_entities(data["entities"], chunk_id)
        if len(entities) > self._max_entities_per_chunk:
            logger.warning(
                "chunk=%s 去重后实体数 %s 超过上限 %s，已截断",
                chunk_id,
                len(entities),
                self._max_entities_per_chunk,
            )
            entities = entities[: self._max_entities_per_chunk]

        graph = KnowledgeGraph()
        name_to_id: Dict[str, str] = {}
        for entity in entities:
            graph.add_entity(
                Entity(
                    id=entity.id,
                    name=entity.name,
                    type=entity.type,
                    properties=dict(entity.properties),
                    source_chunk_ids=[chunk_id],
                )
            )
            name_to_id[entity.name] = entity.id

        self._parse_relations(data["relations"], graph, name_to_id, chunk_id)
        return graph, None

    def _parse_entities(self, raw_entities: List[Any], chunk_id: str) -> List[Entity]:
        """解析、过滤并合并实体输出。"""
        entity_map: Dict[Tuple[str, str], Entity] = {}
        for raw_entity in raw_entities:
            entity_fields = self._parse_entity_fields(raw_entity, chunk_id)
            if entity_fields is None:
                continue
            name, entity_type, properties = entity_fields
            key = (name, entity_type)
            entity = entity_map.get(key)
            if entity is None:
                entity_map[key] = Entity(
                    id=self._entity_id(name, entity_type),
                    name=name,
                    type=entity_type,
                    properties=properties,
                )
            else:
                self._deep_merge(entity.properties, properties)
        return list(entity_map.values())

    def _parse_entity_fields(
        self, raw_entity: Any, chunk_id: str
    ) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """提取并校验单个实体字段。"""
        if not isinstance(raw_entity, dict):
            logger.warning("chunk=%s 忽略非对象实体输出", chunk_id)
            return None
        name = raw_entity.get("name")
        entity_type = raw_entity.get("type")
        if not isinstance(name, str) or not name.strip():
            logger.warning("chunk=%s 忽略缺少有效 name 的实体", chunk_id)
            return None
        if not isinstance(entity_type, str) or not entity_type.strip():
            logger.warning("chunk=%s 忽略缺少有效 type 的实体", chunk_id)
            return None

        name = name.strip()
        entity_type = entity_type.strip()
        if self._entity_types is not None and entity_type not in self._entity_types:
            logger.warning("chunk=%s 过滤白名单外实体类型: %s", chunk_id, entity_type)
            return None
        properties = raw_entity.get("properties", {})
        if not isinstance(properties, dict):
            logger.warning("chunk=%s 忽略实体 %s 的非对象 properties", chunk_id, name)
            properties = {}
        return name, entity_type, dict(properties)

    def _parse_relations(
        self,
        raw_relations: List[Any],
        graph: KnowledgeGraph,
        name_to_id: Dict[str, str],
        chunk_id: str,
    ) -> None:
        """解析关系输出并写入图谱。"""
        relation_ids: Set[str] = set()
        saved_relations = 0
        raw_relations = list(raw_relations)
        if len(raw_relations) > self._max_relations_per_chunk:
            logger.warning(
                "chunk=%s 关系数 %s 超过上限 %s，将截断",
                chunk_id,
                len(raw_relations),
                self._max_relations_per_chunk,
            )
        for raw_relation in raw_relations:
            if saved_relations >= self._max_relations_per_chunk:
                logger.warning(
                    "chunk=%s 关系数超过上限 %s，已截断",
                    chunk_id,
                    self._max_relations_per_chunk,
                )
                break
            if not isinstance(raw_relation, dict):
                logger.warning("chunk=%s 忽略非对象关系输出", chunk_id)
                continue
            source = raw_relation.get("source")
            target = raw_relation.get("target")
            relation_type = raw_relation.get("type")
            if not all(isinstance(value, str) for value in (source, target, relation_type)):
                logger.warning("chunk=%s 忽略端点或类型不是字符串的关系", chunk_id)
                continue

            source = source.strip()
            target = target.strip()
            relation_type = relation_type.strip()
            if not relation_type:
                logger.warning("chunk=%s 忽略类型为空的关系", chunk_id)
                continue
            if source not in name_to_id or target not in name_to_id:
                logger.warning(
                    "chunk=%s 丢弃端点不存在的关系: %s -> %s",
                    chunk_id,
                    source,
                    target,
                )
                continue

            relation_id = self._relation_id(source, relation_type, target)
            if relation_id in relation_ids:
                logger.warning("chunk=%s 忽略重复关系: %s", chunk_id, relation_id)
                continue
            relation_ids.add(relation_id)

            properties = raw_relation.get("properties", {})
            if not isinstance(properties, dict):
                logger.warning("chunk=%s 忽略关系 %s 的非对象 properties", chunk_id, relation_id)
                properties = {}
            graph.add_relation(
                Relation(
                    id=relation_id,
                    source_entity_id=name_to_id[source],
                    target_entity_id=name_to_id[target],
                    type=relation_type,
                    properties=dict(properties),
                    weight=self._normalize_weight(
                        raw_relation.get("weight", 1.0), relation_id, chunk_id
                    ),
                )
            )
            saved_relations += 1

    def extract_from_chunk(self, text: str, chunk_id: str) -> KnowledgeGraph:
        """从单个文本 chunk 抽取知识图谱。

        Args:
            text: chunk 文本，超出上限时先截断。
            chunk_id: chunk 标识，写入实体来源。

        Returns:
            抽取得到的独立知识图谱。

        Raises:
            GraphExtractionError: 模型客户端不可用、调用失败或结构错误重试耗尽。
        """
        if not isinstance(text, str) or not isinstance(chunk_id, str):
            raise GraphExtractionError("text 与 chunk_id 必须是字符串")

        truncated = len(text) > self._max_chunk_chars
        source_text = text[: self._max_chunk_chars] if truncated else text
        previous_error: Optional[str] = None
        last_error = "未知错误"

        try:
            llm_client = self._get_llm_client()
            for attempt in range(self._max_retries + 1):
                prompt = self._build_prompt(source_text, truncated, previous_error)
                output = llm_client.generate_response(
                    prompt, temperature=self._temperature, max_length=4096
                )
                graph, current_error = self._parse_and_validate(output, chunk_id)
                if current_error is None:
                    return graph

                previous_error = current_error
                last_error = current_error
                logger.warning(
                    "chunk=%s 第 %s 次抽取输出无效: %s", chunk_id, attempt + 1, current_error
                )
        except GraphExtractionError:
            raise
        except Exception as error:
            raise GraphExtractionError("图谱抽取调用失败: {}".format(error)) from error

        raise GraphExtractionError("chunk={} 抽取失败: {}".format(chunk_id, last_error))

    def extract_from_chunks(
        self, chunks: List[Tuple[str, str]], strict: bool = False
    ) -> KnowledgeGraph:
        """逐个抽取 chunk，并把结果合并进同一个知识图谱。

        Args:
            chunks: ``(chunk_id, text)`` 元组列表。
            strict: 为 ``True`` 时任一 chunk 失败立即抛出异常。

        Returns:
            合并后的知识图谱；批量统计记录在 ``last_run_stats``。

        Raises:
            GraphExtractionError: ``strict=True`` 且任一 chunk 抽取失败。
        """
        graph = KnowledgeGraph()
        successful_chunks = 0
        failed_chunks: List[str] = []
        chunk_errors: Dict[str, str] = {}
        total_entities = 0
        total_relations = 0

        for chunk_id, text in chunks:
            try:
                chunk_graph = self.extract_from_chunk(text, chunk_id)
            except GraphExtractionError as error:
                logger.warning("chunk=%s 抽取失败，strict=%s: %s", chunk_id, strict, error)
                failed_chunks.append(chunk_id)
                chunk_errors[chunk_id] = str(error)
                if strict:
                    self._record_batch_stats(
                        len(chunks),
                        successful_chunks,
                        failed_chunks,
                        chunk_errors,
                        total_entities,
                        total_relations,
                    )
                    raise
                continue

            for entity in chunk_graph.entities.values():
                graph.add_entity(entity)
            for relation in chunk_graph.relations:
                graph.add_relation(relation)
            successful_chunks += 1
            total_entities += len(chunk_graph.entities)
            total_relations += len(chunk_graph.relations)

        self._record_batch_stats(
            len(chunks),
            successful_chunks,
            failed_chunks,
            chunk_errors,
            total_entities,
            total_relations,
        )
        return graph

    def _record_batch_stats(
        self,
        total_chunks: int,
        successful_chunks: int,
        failed_chunks: List[str],
        chunk_errors: Dict[str, str],
        total_entities: int,
        total_relations: int,
    ) -> None:
        """记录批量抽取统计。"""
        self.last_run_stats = {
            "total_chunks": total_chunks,
            "succeeded_chunks": successful_chunks,
            "failed_chunks": failed_chunks,
            "chunk_errors": chunk_errors,
            "total_entities": total_entities,
            "total_relations": total_relations,
        }
