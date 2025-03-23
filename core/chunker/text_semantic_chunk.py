import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.embbeding_model import get_embedding





class TextSemanticChunker:
    """使用嵌入模型进行基于语义的分块"""
    
    def __init__(self, embedding_model=None, chunk_size=1000, chunk_overlap=200):
        """
        初始化语义分块器
        
        参数:
            embedding_model: 嵌入模型
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
        """
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """
        创建语义分块
        
        参数:
            text: 要分块的文本
            
        返回:
            包含文本块和元数据的字典列表
        """
        # 首先按句子分割
        sentences = re.split(r'(?<=[。！？.!?])', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 创建块
        chunks = []
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            # 如果添加当前句子会超过块大小，保存当前块并开始新块
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # 创建块对象
                chunk_obj = {
                    "text": current_chunk,
                    "sentences": current_sentences,
                    "metadata": {
                        "char_count": len(current_chunk),
                        "sentence_count": len(current_sentences)
                    }
                }
                
                # 如果有嵌入模型，添加嵌入向量
                if self.embedding_model:
                    chunk_obj["embedding"] = self.embedding_model.encode(current_chunk)
                else:
                    chunk_obj["embedding"] = get_embedding(current_chunk)
                
                chunks.append(chunk_obj)
                
                # 开始新块，保留重叠部分
                overlap_text = ""
                overlap_sentences = []
                
                # 从后向前计算重叠部分
                char_count = 0
                for s in reversed(current_sentences):
                    if char_count + len(s) <= self.chunk_overlap:
                        overlap_text = s + overlap_text
                        overlap_sentences.insert(0, s)
                        char_count += len(s)
                    else:
                        break
                
                current_chunk = overlap_text + sentence
                current_sentences = overlap_sentences + [sentence]
            else:
                current_chunk += sentence
                current_sentences.append(sentence)
        
        # 添加最后一个块
        if current_chunk:
            chunk_obj = {
                "text": current_chunk,
                "sentences": current_sentences,
                "metadata": {
                    "char_count": len(current_chunk),
                    "sentence_count": len(current_sentences)
                }
            }
            
            if self.embedding_model:
                chunk_obj["embedding"] = self.embedding_model.encode(current_chunk)
            else:
                chunk_obj["embedding"] = get_embedding(current_chunk)
            
            chunks.append(chunk_obj)
        
        return chunks
