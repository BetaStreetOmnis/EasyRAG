import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import csr_matrix


class BM25Chunker:
    """基于BM25算法的文本分割器"""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200, k1=1.5, b=0.75):
        """
        初始化BM25文本分割器
        
        参数:
            chunk_size: 块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
            k1: BM25算法的k1参数，控制词频缩放
            b: BM25算法的b参数，控制文档长度归一化
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k1 = k1
        self.b = b
        
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        使用BM25算法将文本分割成语义相关的块
        
        参数:
            text: 要分割的文本
            
        返回:
            包含分割后文本块的列表，每个块包含内容和元数据
        """
        # 首先进行初步分割，获取候选段落
        paragraphs = self._split_into_paragraphs(text)
        
        # 如果段落太少，直接返回
        if len(paragraphs) <= 1:
            return [{"content": text, "metadata": {"chunk_index": 0, "chunk_size": len(text)}}]
        
        # 计算BM25相似度矩阵
        similarity_matrix = self._calculate_bm25_similarity(paragraphs)
        
        # 基于相似度进行聚类分块
        chunks = self._cluster_paragraphs(paragraphs, similarity_matrix)
        
        # 处理块重叠
        if self.chunk_overlap > 0:
            chunks = self._merge_chunks_with_overlap(chunks)
        
        # 构建结果
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
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        将文本分割成段落
        
        参数:
            text: 要分割的文本
            
        返回:
            段落列表
        """
        # 使用空行分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # 处理过长的段落
        result = []
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                # 过长段落按句子再分割
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= self.chunk_size:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            result.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    result.append(current_chunk)
            else:
                result.append(paragraph)
        
        return result
    
    def _calculate_bm25_similarity(self, paragraphs: List[str]) -> np.ndarray:
        """
        计算段落间的BM25相似度
        
        参数:
            paragraphs: 段落列表
            
        返回:
            相似度矩阵
        """
        # 使用CountVectorizer获取词频矩阵
        vectorizer = CountVectorizer(token_pattern=r"(?u)\b\w+\b")
        tf = vectorizer.fit_transform(paragraphs)
        
        # 计算文档频率
        df = np.bincount(tf.indices, minlength=tf.shape[1])
        
        # 计算IDF
        n_docs = len(paragraphs)
        idf = np.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
        
        # 计算文档长度和平均文档长度
        doc_lengths = tf.sum(axis=1).A1
        avg_doc_length = np.mean(doc_lengths)
        
        # 计算BM25相似度矩阵
        similarity_matrix = np.zeros((n_docs, n_docs))
        
        for i in range(n_docs):
            for j in range(n_docs):
                if i == j:
                    similarity_matrix[i, j] = 1.0  # 自身相似度为1
                    continue
                
                # 获取文档i和j的词频
                doc_i = tf[i].toarray().flatten()
                doc_j = tf[j].toarray().flatten()
                
                # 计算BM25分数
                score = 0.0
                for term_idx in range(len(doc_i)):
                    if doc_i[term_idx] > 0 and doc_j[term_idx] > 0:
                        # BM25公式计算
                        numerator = doc_j[term_idx] * (self.k1 + 1)
                        denominator = doc_j[term_idx] + self.k1 * (1 - self.b + self.b * doc_lengths[j] / avg_doc_length)
                        term_score = idf[term_idx] * numerator / denominator
                        score += term_score
                
                similarity_matrix[i, j] = score
        
        # 归一化相似度矩阵
        row_max = np.max(similarity_matrix, axis=1).reshape(-1, 1)
        row_max[row_max == 0] = 1.0  # 避免除以零
        similarity_matrix = similarity_matrix / row_max
        
        return similarity_matrix
    
    def _cluster_paragraphs(self, paragraphs: List[str], similarity_matrix: np.ndarray) -> List[str]:
        """
        基于相似度矩阵聚类段落
        
        参数:
            paragraphs: 段落列表
            similarity_matrix: 相似度矩阵
            
        返回:
            聚类后的文本块列表
        """
        n_paragraphs = len(paragraphs)
        visited = [False] * n_paragraphs
        chunks = []
        
        for i in range(n_paragraphs):
            if visited[i]:
                continue
                
            # 开始一个新的聚类
            current_chunk = paragraphs[i]
            visited[i] = True
            
            # 贪婪地添加相似段落
            while len(current_chunk) < self.chunk_size:
                # 找到最相似且未访问的段落
                best_sim = -1
                best_idx = -1
                
                for j in range(n_paragraphs):
                    if not visited[j] and similarity_matrix[i, j] > best_sim:
                        best_sim = similarity_matrix[i, j]
                        best_idx = j
                
                # 如果没有找到合适的段落或添加后会超过chunk_size，则结束
                if best_idx == -1 or len(current_chunk) + len(paragraphs[best_idx]) > self.chunk_size:
                    break
                    
                # 添加段落到当前块
                current_chunk += "\n\n" + paragraphs[best_idx]
                visited[best_idx] = True
            
            chunks.append(current_chunk)
        
        # 处理剩余未访问的段落
        for i in range(n_paragraphs):
            if not visited[i]:
                chunks.append(paragraphs[i])
        
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
