"""You.com Web Search 外部检索器。

作为本地知识库之外的补充检索源：调用 You.com Search API
（GET https://ydc-index.io/v1/search，X-API-Key 鉴权），把网页与新闻结果
整理成与本地库检索一致的结构（index / score / text / metadata），
供 /web/search 端点使用。

配置：环境变量 YDC_API_KEY（团队约定名，勿改）。未配置时检索器不可用，
上层端点会返回明确提示而非报错。任何网络 / 状态码 / 解析异常都会被捕获并
返回空结果，绝不向上抛出，保证不影响主服务。
"""
import logging
import os

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv 可选：缺失时退化为仅读真实环境变量，不影响启动
    pass

logger = logging.getLogger(__name__)

# You.com Search API 端点（团队约定）
YOUCOM_ENDPOINT = "https://ydc-index.io/v1/search"
# 团队约定：对 You.com 主机的请求需带此 User-Agent（lowercased owner-repo slug）
YOUCOM_USER_AGENT = "youdotcom-integration/betastreetomnis-easyrag"

DEFAULT_TOP_K = 5
MAX_TOP_K = 20
REQUEST_TIMEOUT = 15


class YouComWebRetriever:
    """You.com 联网检索器，返回与本地库检索一致的结果结构。"""

    def __init__(self, api_key=None, endpoint=YOUCOM_ENDPOINT):
        # 显式传入优先，否则回退环境变量 YDC_API_KEY；strip 掉空白避免误判为已配置
        raw_key = api_key if api_key is not None else os.getenv("YDC_API_KEY", "")
        self.api_key = (raw_key or "").strip()
        self.endpoint = endpoint

    @property
    def available(self):
        """是否已配置可用的 API Key。"""
        return bool(self.api_key)

    def search(self, query, top_k=DEFAULT_TOP_K):
        """检索网页结果。

        参数:
            query: 查询文本
            top_k: 返回的最大结果数（1-20，越界自动夹取）

        返回:
            List[Dict]，每项含 index / score / text / metadata；未配置 Key、
            网络异常、非 2xx、解析失败时统一返回 []（记录日志，绝不抛出）。
        """
        if not self.available:
            logger.warning("YouComWebRetriever 未配置 YDC_API_KEY，跳过联网检索")
            return []

        try:
            n = int(top_k)
        except (TypeError, ValueError):
            n = DEFAULT_TOP_K
        n = max(1, min(n, MAX_TOP_K))

        try:
            resp = requests.get(
                self.endpoint,
                params={"query": query, "count": n},
                headers={"X-API-Key": self.api_key, "User-Agent": YOUCOM_USER_AGENT},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error("You.com 联网检索请求失败: %s", exc)
            return []

        if resp.status_code != 200:
            # 不回显响应体，避免泄露账号信息；401 鉴权 / 429 限流 / 5xx 服务端
            logger.error("You.com 联网检索返回状态码 %s", resp.status_code)
            return []

        try:
            payload = resp.json()
        except ValueError as exc:
            logger.error("You.com 响应解析失败: %s", exc)
            return []

        return self._to_results(payload, n)

    @staticmethod
    def _to_results(payload, n):
        """把 You.com 响应归一化为本地库一致的结果结构。

        响应结构 {"results": {"web": [...], "news": [...]}}；news 可能缺失，
        每条结果除 url/title/description/snippets 外字段均视为可选，防御式读取。
        """
        if not isinstance(payload, dict):
            return []
        results_node = payload.get("results")
        if not isinstance(results_node, dict):
            return []
        entries = []
        for bucket in ("web", "news"):
            bucket_items = results_node.get(bucket)
            if not isinstance(bucket_items, list):
                continue
            for entry in bucket_items:
                if isinstance(entry, dict):
                    entries.append(entry)

        # web 与 news 各返回最多 n 条，按合并总数截断，与 top_k 语义对齐
        entries = entries[:n]

        formatted = []
        for rank, entry in enumerate(entries):
            url = entry.get("url") or ""
            title = entry.get("title") or ""
            description = entry.get("description") or ""
            snippets = entry.get("snippets")
            snippet_text = ""
            if isinstance(snippets, list):
                snippet_text = "\n".join(s for s in snippets if isinstance(s, str))

            text_parts = [part for part in (title, description, snippet_text) if part]
            if url:
                text_parts.append("来源: %s" % url)

            formatted.append({
                "index": rank,
                # You.com 已按相关性排序、无分数，这里用名次递减的中性分数
                "score": round(1.0 - rank * 0.01, 4),
                "text": "\n".join(text_parts),
                "metadata": {"url": url, "title": title, "source": "you.com"},
            })
        return formatted
