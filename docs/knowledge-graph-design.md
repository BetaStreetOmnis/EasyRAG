# 知识图谱阶段 B 设计文档

## 目标与范围

知识图谱是 EasyRAG 的检索增强层，用于从既有 chunk 中抽取实体与关系，并在向量检索之外提供结构化上下文。阶段 B 的首个增量只交付图谱数据模型、内存存储与单元测试，不改变现有解析、切分、向量入库或检索流程。

本阶段完成后，系统应具备以下能力：

- 以类型化对象表示实体、关系与完整知识图谱。
- 支持实体去重与合并、关系端点校验、图谱字典序列化与反序列化。
- 通过 `GraphStore` 抽象隔离后续持久化实现，降低 API 与存储后端的耦合。
- 为后续图谱检索、子图导出与前端可视化提供稳定的数据基础。

## 数据模型

### Entity

`Entity` 使用 dataclass 表示图谱节点：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 实体唯一标识 |
| `name` | `str` | 实体名称 |
| `type` | `str` | 实体类型，例如人物、组织、概念 |
| `properties` | `dict` | 实体扩展属性 |
| `source_chunk_ids` | `list` | 实体来源 chunk 标识列表 |

同名同类型且使用相同 `id` 的实体重复加入时，`KnowledgeGraph.add_entity` 会合并扩展属性，并按插入顺序合并来源 chunk，不产生重复节点。若相同 `id` 对应不同名称或类型，则拒绝写入，避免破坏实体身份。

### Relation

`Relation` 使用 dataclass 表示有向边：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 关系唯一标识 |
| `source_entity_id` | `str` | 起点实体标识 |
| `target_entity_id` | `str` | 终点实体标识 |
| `type` | `str` | 关系类型，例如属于、位于、引用 |
| `properties` | `dict` | 关系扩展属性 |
| `weight` | `float` | 关系权重 |

关系加入图谱前会校验起点与终点实体均已存在。缺失任一端点时抛出 `ValueError`，保证图数据始终闭合。

### KnowledgeGraph

`KnowledgeGraph` 是实体与关系的内存容器：

- `add_entity`：加入实体；相同 `id` 且同名同类型时合并属性与来源。
- `add_relation`：加入关系；两端实体必须存在。
- `get_entity`：按实体 `id` 查询实体。
- `get_relations`：按实体 `id` 过滤该实体作为起点或终点的所有关系。
- `entities` / `relations`：只读属性，返回内部集合的浅拷贝。
- `to_dict` / `from_dict`：输出和恢复 JSON 友好的字典结构。

字典结构如下：

```json
{
  "entities": [
    {
      "id": "entity-openai",
      "name": "OpenAI",
      "type": "organization",
      "properties": {"country": "America"},
      "source_chunk_ids": ["chunk-1"]
    }
  ],
  "relations": [
    {
      "id": "relation-1",
      "source_entity_id": "entity-openai",
      "target_entity_id": "entity-gpt",
      "type": "develops",
      "properties": {},
      "weight": 1.0
    }
  ]
}
```

### GraphStore

`GraphStore` 定义存储后端的最小接口：

- `save(graph, kb_id)`：保存知识库对应的图谱，覆盖旧版本。
- `load(kb_id)`：读取图谱；不存在时返回 `None`。
- `delete(kb_id)`：删除图谱并返回是否删除成功。

`InMemoryGraphStore` 基于进程内 `dict` 实现该接口，适用于单元测试、临时任务和后续持久化后端的接口验证。它通过序列化快照保存数据，避免保存后原对象继续变更影响已保存版本。

## 与现有流水线的关系

现有流水线保持不变：

```text
文件解析 → chunker → 向量化 → FAISS 入库/检索 → rerank → 生成回答
```

知识图谱作为旁路增强层接入：

```text
chunker 产生的 chunk
    ├── 原有 FAISS 检索流程
    └── 实体关系抽取 → KnowledgeGraph → 图谱检索 → 上下文融合
```

后续融合原则：

- 图谱抽取消费 chunk 及其元数据，不反向修改 chunk。
- 向量检索仍是默认召回路径，图谱检索提供补充实体、关系与邻域上下文。
- 图谱服务不可用时，RAG 主流程应可降级为现有行为。
- 图谱构建、检索与可视化均按知识库 `kb_id` 隔离。

## REST API 契约草案

以下端点仅为阶段 B 设计草案，本阶段不实现。后续实现必须与现有知识库 API 的错误格式、鉴权方式与路径规范保持一致。

### 获取完整图谱

```http
GET /kb/{kb_id}/graph
```

成功返回 `KnowledgeGraph.to_dict()` 对应结构；图谱不存在返回 `404`。生产环境中应支持 `nodes` / `edges` 分页或按查询深度裁剪，避免大图一次性返回。

### 查询实体列表

```http
GET /kb/{kb_id}/graph/entities?type=&name=&limit=&offset=
```

返回实体数组与分页信息。`name` 建议使用精确匹配，模糊搜索可由后续搜索参数扩展。

### 查询实体详情与邻域

```http
GET /kb/{kb_id}/graph/entities/{entity_id}
GET /kb/{kb_id}/graph/entities/{entity_id}/relations
```

详情接口返回实体及其一度关系摘要；关系接口支持 `direction=in|out|both` 与 `limit` 参数。

### 查询关系列表

```http
GET /kb/{kb_id}/graph/relations?entity_id=&type=&limit=&offset=
```

`entity_id` 存在时返回该实体关联的关系；不传时返回分页关系列表。

### 触发图谱构建

```http
POST /kb/{kb_id}/graph/extract
```

请求体可指定 chunk 范围、抽取模型与实体类型白名单。构建可能是长任务，建议返回任务标识并提供任务状态查询接口；实现细节在 step2 设计中确定。

### 删除图谱

```http
DELETE /kb/{kb_id}/graph
```

删除该知识库的图谱数据，不影响已入库 chunk 与向量索引。图谱不存在时返回 `404` 或幂等 `204`，需与现有删除语义保持一致。

## 分阶段增量计划

| 阶段 | 内容 | 交付边界 |
| --- | --- | --- |
| step1 | 数据模型骨架 | `Entity`、`Relation`、`KnowledgeGraph`、`GraphStore`、`InMemoryGraphStore` 与单元测试 |
| step2 | LLM 实体关系抽取器 | 从 chunk 抽取实体和关系，输出可校验的 `KnowledgeGraph`，处理重试与模型输出约束 |
| step3 | 持久化存储后端 | 实现生产可用的 `GraphStore`，支持版本、事务、迁移与按知识库隔离 |
| step4 | API 端点 | 实现图谱查询、构建任务与删除接口，完成鉴权、分页和错误处理 |
| step5 | 前端可视化 | 提供图谱浏览、搜索、节点详情和邻域展开，支持大数据量渐进加载 |

每个阶段保持独立可回滚：新增能力通过显式配置启用，不改变默认 RAG 检索结果；跨阶段接口变更必须通过单元测试与 API 兼容性评审。
