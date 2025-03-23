import re
from typing import List, Dict, Any, Optional, Tuple

class RecursiveCharacterTextSplitter:
    """递归字符文本分割器"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200, separators=None):
        """
        初始化递归字符文本分割器
        
        参数:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
            separators: 分隔符列表，按优先级排序，如果为None则使用默认设置
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 默认分隔符，按优先级排序
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 换行
            ". ",    # 句子
            "! ",    # 感叹句
            "? ",    # 问句
            ";",     # 分号
            ",",     # 逗号
            " ",     # 空格（单词）
            ""       # 字符
        ]
    
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        递归地将文本分割成块
        
        参数:
            text: 要分割的文本
            
        返回:
            包含分割后文本块的列表，每个块包含内容和元数据
        """
        chunks = self._split_text_recursive(text, self.separators)
        
        # 将纯文本块转换为带元数据的字典格式
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "content": chunk,
                "metadata": {
                    "chunk_index": i,
                    "chunk_size": len(chunk)
                }
            })
        
        return result
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """
        递归分割文本
        
        参数:
            text: 要分割的文本
            separators: 当前可用的分隔符列表
            
        返回:
            分割后的文本块列表
        """
        # 如果文本长度小于块大小，直接返回
        if len(text) <= self.chunk_size:
            return [text]
        
        # 如果没有更多分隔符，则按块大小强制分割
        if not separators:
            return self._split_by_character(text)
        
        # 获取当前分隔符和剩余分隔符
        separator = separators[0]
        next_separators = separators[1:]
        
        # 使用当前分隔符分割文本
        splits = text.split(separator)
        
        # 如果分割后只有一个元素，使用下一个分隔符
        if len(splits) == 1:
            return self._split_text_recursive(text, next_separators)
        
        # 处理分割后的文本
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            # 如果不是第一个分割，添加分隔符
            if current_chunk:
                split_with_separator = separator + split
            else:
                split_with_separator = split
            
            split_length = len(split_with_separator)
            
            # 如果添加当前分割会超过块大小
            if current_length + split_length > self.chunk_size:
                # 如果当前块不为空，添加到结果
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    chunks.append(chunk_text)
                
                # 如果当前分割本身超过块大小，递归处理
                if split_length > self.chunk_size:
                    sub_chunks = self._split_text_recursive(split_with_separator, next_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_length = 0
                else:
                    # 开始新的块
                    current_chunk = [split_with_separator]
                    current_length = split_length
            else:
                # 添加到当前块
                current_chunk.append(split_with_separator)
                current_length += split_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_text = "".join(current_chunk)
            chunks.append(chunk_text)
        
        # 处理块重叠
        if self.chunk_overlap > 0:
            return self._merge_chunks_with_overlap(chunks)
        
        return chunks
    
    def _split_by_character(self, text: str) -> List[str]:
        """
        按字符强制分割文本
        
        参数:
            text: 要分割的文本
            
        返回:
            分割后的文本块列表
        """
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks
    
    def _merge_chunks_with_overlap(self, chunks: List[str]) -> List[str]:
        """
        处理块之间的重叠
        
        参数:
            chunks: 原始文本块列表
            
        返回:
            处理重叠后的文本块列表
        """
        if not chunks or len(chunks) == 1:
            return chunks
        
        result = []
        for i in range(len(chunks)):
            if i == 0:
                # 第一个块不需要前向重叠
                result.append(chunks[i])
            else:
                # 获取前一个块的末尾部分作为重叠
                prev_chunk = chunks[i-1]
                overlap_size = min(self.chunk_overlap, len(prev_chunk))
                overlap_text = prev_chunk[-overlap_size:]
                
                # 将重叠部分添加到当前块的开头
                result.append(overlap_text + chunks[i])
        
        return result
