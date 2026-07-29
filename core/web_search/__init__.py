"""联网检索模块：把 You.com 等外部搜索源作为本地知识库之外的补充检索器。"""
from core.web_search.youcom_retriever import YouComWebRetriever

__all__ = ["YouComWebRetriever"]
