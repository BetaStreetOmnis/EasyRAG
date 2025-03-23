import re
import numpy as np
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from core.embbeding_model import get_embedding


class SemanticChunker:
    """基于语义边界的智能分块工具"""
    
    def __init__(self, embedding_model=None, similarity_threshold=0.7, min_chunk_size=100, max_chunk_size=1000):
        """
        初始化语义分块器
        
        参数:
            embedding_model: 嵌入模型，用于将文本转换为向量
            similarity_threshold: 相似度阈值，用于确定语义边界
            min_chunk_size: 最小块大小（字符数）
            max_chunk_size: 最大块大小（字符数）
        """
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_text(self, text: str) -> List[str]:
        """
        基于语义边界对文本进行分块
        
        参数:
            text: 要分块的文本
            
        返回:
            分块后的文本列表
        """
        # 首先按段落分割W
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 如果段落太少，直接返回
        if len(paragraphs) <= 1:
            return paragraphs
        
        # 计算每个段落的嵌入向量
        embeddings = []
        for para in paragraphs:
            if self.embedding_model:
                embedding = self.embedding_model.encode(para)
            else:
                # 如果没有提供嵌入模型，使用简单的TF-IDF作为替代
                embedding = self._simple_embedding(para)
            embeddings.append(embedding)
        
        # 计算相邻段落之间的相似度
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._compute_similarity(embeddings[i], embeddings[i+1])
            similarities.append(sim)
        
        # 根据相似度确定语义边界
        chunks = []
        current_chunk = paragraphs[0]
        
        for i in range(len(similarities)):
            # 如果相似度低于阈值，认为是语义边界
            if similarities[i] < self.similarity_threshold:
                # 检查当前块大小
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = paragraphs[i+1]
                else:
                    current_chunk += "\n\n" + paragraphs[i+1]
            else:
                # 检查添加下一段后是否超过最大块大小
                if len(current_chunk) + len(paragraphs[i+1]) > self.max_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = paragraphs[i+1]
                else:
                    current_chunk += "\n\n" + paragraphs[i+1]
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


    def _simple_embedding(self, text: str) -> np.ndarray:
        """简单的文本表示方法，当没有嵌入模型时使用"""
        # 这里使用字符频率作为简单的文本表示
        chars = {}
        for char in text:
            chars[char] = chars.get(char, 0) + 1
        
        # 转换为向量
        vec = np.zeros(256)  # 假设使用ASCII字符
        for char, count in chars.items():
            try:
                vec[ord(char) % 256] = count / len(text)
            except:
                pass
        return vec
    
    def _compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量之间的余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return dot_product / (norm1 * norm2)