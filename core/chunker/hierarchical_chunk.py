import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.embbeding_model import get_embedding


class HierarchicalTextSplitter:
    """构建文档的层次结构"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        """
        初始化层次文本分割器
        
        参数:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分割成层次结构
        
        参数:
            text: 要分割的文本
            
        返回:
            包含层次结构的文本块列表
        """
        # 识别标题和段落
        lines = text.split('\n')
        
        # 构建层次结构
        hierarchy = []
        current_section = None
        current_level = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测标题级别
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2)
                
                # 创建新的章节
                new_section = {
                    "level": level,
                    "title": title,
                    "content": "",
                    "children": []
                }
                
                # 处理层级关系
                if current_section is None:
                    hierarchy.append(new_section)
                elif level > current_level:
                    current_section["children"].append(new_section)
                else:
                    # 回溯到适当的父级
                    parent = self._find_parent(hierarchy, level)
                    if parent:
                        parent["children"].append(new_section)
                    else:
                        hierarchy.append(new_section)
                
                current_section = new_section
                current_level = level
            else:
                # 普通内容
                if current_section:
                    current_section["content"] += line + "\n"
                else:
                    # 没有标题的内容
                    default_section = {
                        "level": 1,
                        "title": "文档内容",
                        "content": line + "\n",
                        "children": []
                    }
                    hierarchy.append(default_section)
                    current_section = default_section
                    current_level = 1
        
        # 将层次结构转换为块
        chunks = self._create_chunks_from_hierarchy(hierarchy)
        return chunks
    
    def _find_parent(self, hierarchy: List[Dict[str, Any]], level: int, current_path: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查找给定级别的父节点"""
        if current_path is None:
            current_path = []
        
        for section in hierarchy:
            if section["level"] < level:
                return section
            
            # 递归检查子节点
            parent = self._find_parent(section.get("children", []), level, current_path + [section])
            if parent:
                return parent
        
        return None
    
    def _create_chunks_from_hierarchy(self, hierarchy: List[Dict[str, Any]], parent_path: str = "") -> List[Dict[str, Any]]:
        """从层次结构创建文本块"""
        chunks = []
        
        for section in hierarchy:
            # 构建路径
            current_path = parent_path
            if current_path:
                current_path += " > "
            current_path += section["title"]
            
            # 处理当前节点的内容
            content = section["content"].strip()
            if content:
                # 分割大内容
                if len(content) > self.chunk_size:
                    sub_chunks = self._split_content(content)
                    for i, sub_chunk in enumerate(sub_chunks):
                        chunks.append({
                            "text": sub_chunk,
                            "path": current_path,
                            "level": section["level"],
                            "title": section["title"],
                            "is_partial": True,
                            "part_number": i + 1,
                            "total_parts": len(sub_chunks)
                        })
                else:
                    chunks.append({
                        "text": content,
                        "path": current_path,
                        "level": section["level"],
                        "title": section["title"],
                        "is_partial": False
                    })
            
            # 递归处理子节点
            child_chunks = self._create_chunks_from_hierarchy(section.get("children", []), current_path)
            chunks.extend(child_chunks)
        
        return chunks
    
    def _split_content(self, content: str) -> List[str]:
        """将大内容分割成更小的块"""
        chunks = []
        current_chunk = ""
        
        # 按句子分割
        sentences = re.split(r'(?<=[。！？.!?])', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
