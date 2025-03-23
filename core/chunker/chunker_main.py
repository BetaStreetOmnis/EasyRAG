import re
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum

from core.chunker.text_semantic_chunk import TextSemanticChunker
from core.chunker.semantic_chunk import SemanticChunker
from core.chunker.hierarchical_chunk import HierarchicalTextSplitter
from core.chunker.markdown_header_chunk import MarkdownHeaderTextSplitter
from core.chunker.recursive_character_chunk import RecursiveCharacterTextSplitter
from core.chunker.bm25_chunk import BM25Chunker

# 配置日志
logger = logging.getLogger(__name__)

class ChunkMethod(Enum):
    """分块方法枚举"""
    TEXT_SEMANTIC = "text_semantic"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    MARKDOWN_HEADER = "markdown_header"
    RECURSIVE_CHARACTER = "recursive_character"
    BM25 = "bm25"

class DocumentChunker:
    """
    文档分块器主类，可以选择不同的分块策略
    """
    
    def __init__(self, 
                 method: Union[str, ChunkMethod] = ChunkMethod.TEXT_SEMANTIC,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 embedding_model = None,
                 **kwargs):
        """
        初始化文档分块器
        
        参数:
            method: 分块方法，可以是ChunkMethod枚举或字符串
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
            embedding_model: 嵌入模型
            **kwargs: 传递给具体分块器的其他参数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        
        # 将字符串转换为枚举
        if isinstance(method, str):
            try:
                self.method = ChunkMethod(method.lower())
            except ValueError:
                logger.warning(f"未知的分块方法: {method}，使用默认方法: text_semantic")
                self.method = ChunkMethod.TEXT_SEMANTIC
        else:
            self.method = method
            
        # 初始化选择的分块器
        self._init_chunker(**kwargs)
    
    def _init_chunker(self, **kwargs):
        """初始化具体的分块器"""
        if self.method == ChunkMethod.TEXT_SEMANTIC:
            self.chunker = TextSemanticChunker(
                embedding_model=self.embedding_model,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.method == ChunkMethod.SEMANTIC:
            similarity_threshold = kwargs.get('similarity_threshold', 0.7)
            min_chunk_size = kwargs.get('min_chunk_size', 100)
            self.chunker = SemanticChunker(
                embedding_model=self.embedding_model,
                similarity_threshold=similarity_threshold,
                min_chunk_size=min_chunk_size,
                max_chunk_size=self.chunk_size
            )
        elif self.method == ChunkMethod.HIERARCHICAL:
            self.chunker = HierarchicalTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.method == ChunkMethod.MARKDOWN_HEADER:
            headers_to_split_on = kwargs.get('headers_to_split_on', None)
            self.chunker = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
        elif self.method == ChunkMethod.RECURSIVE_CHARACTER:
            separators = kwargs.get('separators', None)
            self.chunker = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=separators
            )
        elif self.method == ChunkMethod.BM25:
            min_chunk_size = kwargs.get('min_chunk_size', 200)
            self.chunker = BM25Chunker(
                min_chunk_size=min_chunk_size,
                max_chunk_size=self.chunk_size
            )
        else:
            # 默认使用TextSemanticChunker
            logger.warning(f"未实现的分块方法: {self.method}，使用默认方法: text_semantic")
            self.chunker = TextSemanticChunker(
                embedding_model=self.embedding_model,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def chunk_document(self, document: str, progress_callback=None) -> List[Dict[str, Any]]:
        """
        对文档进行分块
        
        参数:
            document: 要分块的文档
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            
        返回:
            分块后的文档列表
        """
        try:
            if progress_callback:
                progress_callback(0, f"开始使用 {self.method.value} 方法进行文档分块")
            
            result = []
            if self.method == ChunkMethod.TEXT_SEMANTIC:
                # 这里假设分块过程无法中断，我们在开始和结束时报告进度
                if progress_callback:
                    progress_callback(10, "正在进行文本语义分块...")
                result = self.chunker.create_chunks(document)
                if progress_callback:
                    progress_callback(95, f"文本语义分块完成，共生成 {len(result)} 个分块")
                
            elif self.method == ChunkMethod.SEMANTIC:
                if progress_callback:
                    progress_callback(10, "正在进行语义分块...")
                chunks = self.chunker.chunk_text(document)
                result = [{"text": chunk, "metadata": {"method": "semantic"}} for chunk in chunks]
                if progress_callback:
                    progress_callback(95, f"语义分块完成，共生成 {len(result)} 个分块")
                
            elif self.method == ChunkMethod.HIERARCHICAL:
                if progress_callback:
                    progress_callback(10, "正在进行层次分块...")
                result = self.chunker.split_text(document)
                if progress_callback:
                    progress_callback(95, f"层次分块完成，共生成 {len(result)} 个分块")
                
            elif self.method == ChunkMethod.MARKDOWN_HEADER:
                if progress_callback:
                    progress_callback(10, "正在进行Markdown标题分块...")
                result = self.chunker.split_text(document)
                if progress_callback:
                    progress_callback(95, f"Markdown标题分块完成，共生成 {len(result)} 个分块")
                
            elif self.method == ChunkMethod.RECURSIVE_CHARACTER:
                if progress_callback:
                    progress_callback(10, "正在进行递归字符分块...")
                chunks = self.chunker.split_text(document)
                result = [{"text": chunk, "metadata": {"method": "recursive"}} for chunk in chunks]
                if progress_callback:
                    progress_callback(95, f"递归字符分块完成，共生成 {len(result)} 个分块")
                
            elif self.method == ChunkMethod.BM25:
                if progress_callback:
                    progress_callback(10, "正在进行BM25分块...")
                result = self.chunker.chunk_document(document)
                if progress_callback:
                    progress_callback(95, f"BM25分块完成，共生成 {len(result)} 个分块")
                
            else:
                # 默认使用TextSemanticChunker
                if progress_callback:
                    progress_callback(10, "使用默认方法进行分块...")
                result = self.chunker.create_chunks(document)
                if progress_callback:
                    progress_callback(95, f"默认分块完成，共生成 {len(result)} 个分块")
            
            # 为每个分块添加唯一ID
            for i, chunk in enumerate(result):
                if isinstance(chunk, dict) and "metadata" in chunk:
                    chunk["metadata"]["chunk_id"] = f"chunk_{i+1}"
                elif isinstance(chunk, dict):
                    chunk["metadata"] = {"chunk_id": f"chunk_{i+1}"}
                else:
                    # 如果chunk不是字典，转换为字典格式
                    result[i] = {"text": chunk, "metadata": {"chunk_id": f"chunk_{i+1}"}}
            
            if progress_callback:
                progress_callback(100, f"分块处理完成，共生成 {len(result)} 个分块")
                
            return result
            
        except Exception as e:
            logger.error(f"文档分块失败: {str(e)}")
            # 出错时使用简单的分块方法
            if progress_callback:
                progress_callback(50, "主要分块方法失败，使用备用简单分块...")
                
            simple_chunks = self._simple_chunk(document)
            result = [{"text": chunk, "metadata": {"method": "simple_fallback", "chunk_id": f"chunk_{i+1}"}} 
                     for i, chunk in enumerate(simple_chunks)]
            
            if progress_callback:
                progress_callback(100, f"备用分块完成，共生成 {len(result)} 个分块")
                
            return result
    
    def _simple_chunk(self, text: str) -> List[str]:
        """简单的分块方法，作为出错时的后备方案"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            end = min(i + self.chunk_size, len(text))
            chunks.append(text[i:end])
            if end == len(text):
                break
        return chunks
    
    def change_method(self, method: Union[str, ChunkMethod], **kwargs):
        """
        更改分块方法
        
        参数:
            method: 新的分块方法
            **kwargs: 传递给具体分块器的其他参数
        """
        if isinstance(method, str):
            try:
                self.method = ChunkMethod(method.lower())
            except ValueError:
                logger.warning(f"未知的分块方法: {method}，保持当前方法: {self.method.value}")
                return False
        else:
            self.method = method
            
        # 重新初始化分块器
        self._init_chunker(**kwargs)
        return True
