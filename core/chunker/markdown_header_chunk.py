import re
from typing import List, Dict, Any, Optional, Tuple

class MarkdownHeaderTextSplitter:
    """基于Markdown标题的文本分割器"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200, headers_to_split_on=None):
        """
        初始化Markdown标题文本分割器
        
        参数:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
            headers_to_split_on: 用于分割的标题级别和分隔符，如果为None则使用默认设置
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 默认的标题分割配置
        self.headers_to_split_on = headers_to_split_on or [
            ("#", "标题1"),
            ("##", "标题2"),
            ("###", "标题3"),
            ("####", "标题4"),
            ("#####", "标题5"),
            ("######", "标题6"),
        ]
    
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        根据Markdown标题将文本分割成块
        
        参数:
            text: 要分割的Markdown文本
            
        返回:
            包含分割后文本块的列表，每个块包含内容和元数据
        """
        # 分割文本为行
        lines = text.split('\n')
        
        # 初始化结果列表和当前块
        chunks = []
        current_headers = {}
        current_content = []
        
        for line in lines:
            # 检查是否是标题行
            header_match = None
            header_level = None
            
            for header_prefix, header_name in self.headers_to_split_on:
                if line.strip().startswith(header_prefix + " "):
                    header_match = line.strip()[len(header_prefix) + 1:]
                    header_level = len(header_prefix)
                    break
            
            # 如果是标题行，处理当前内容块
            if header_match is not None:
                # 如果有累积的内容，创建一个新块
                if current_content:
                    chunk_text = "\n".join(current_content).strip()
                    if chunk_text:
                        chunks.append({
                            "content": chunk_text,
                            "metadata": {**current_headers}
                        })
                    current_content = []
                
                # 更新当前标题信息
                # 移除所有等级大于等于当前标题的标题
                for level in list(current_headers.keys()):
                    if int(level) >= header_level:
                        current_headers.pop(level)
                
                # 添加当前标题
                current_headers[str(header_level)] = header_match
                
                # 将标题行添加到当前内容
                current_content.append(line)
            else:
                # 非标题行，直接添加到当前内容
                current_content.append(line)
        
        # 处理最后一个块
        if current_content:
            chunk_text = "\n".join(current_content).strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "metadata": {**current_headers}
                })
        
        # 处理过大的块
        result_chunks = []
        for chunk in chunks:
            if len(chunk["content"]) > self.chunk_size:
                # 如果块太大，进一步分割
                sub_chunks = self._split_large_chunk(chunk["content"])
                for sub_chunk in sub_chunks:
                    result_chunks.append({
                        "content": sub_chunk,
                        "metadata": {**chunk["metadata"]}
                    })
            else:
                result_chunks.append(chunk)
        
        return result_chunks
    
    def _split_large_chunk(self, text: str) -> List[str]:
        """
        将大块文本分割成更小的块
        
        参数:
            text: 要分割的文本
            
        返回:
            分割后的文本列表
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # 如果当前段落本身就超过了块大小，需要进一步分割
            if para_size > self.chunk_size:
                # 先处理当前累积的块
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 分割大段落
                words = para.split(' ')
                temp_chunk = []
                temp_size = 0
                
                for word in words:
                    word_size = len(word) + 1  # +1 for space
                    if temp_size + word_size > self.chunk_size:
                        chunks.append(" ".join(temp_chunk))
                        temp_chunk = [word]
                        temp_size = word_size
                    else:
                        temp_chunk.append(word)
                        temp_size += word_size
                
                if temp_chunk:
                    chunks.append(" ".join(temp_chunk))
            
            # 如果添加当前段落会超过块大小，创建新块
            elif current_size + para_size > self.chunk_size:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 添加最后一个块
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
