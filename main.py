import os
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
import json

# 导入自定义模块
from core.faiss_connect import FaissManager, DataLineageTracker
from core.embbeding_model import get_embedding
from core.rerank_model import reranker, load_rerank_model
from core.chunker.chunker_main import DocumentChunker, ChunkMethod
# from core.file_read.file_handle import FileHandler
from core.file_read.file_to_markdown import FileToMarkdown
# 配置日志
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    文档处理类，负责文件读取和分块处理
    """
    
    def __init__(self, chunk_method: str = "text_semantic", chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档处理器
        
        Args:
            chunk_method: 分块方法
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
        """
        # self.file_handler = FileHandler() # 文件处理类 目前暂时更换为markdown解析器，效果更好
        self.file_handler = FileToMarkdown()
        self.chunker = DocumentChunker(
            method=chunk_method,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理文件，读取内容并返回文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件信息，包含内容和结构
        """
        return self.file_handler.process_file(file_path)
    
    def chunk_document(self, document: str, progress_callback=None) -> List[Dict[str, Any]]:
        """
        对文档内容进行分块
        
        Args:
            document: 文档内容
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            
        Returns:
            List[Dict]: 分块后的文档列表
        """
        return self.chunker.chunk_document(document, progress_callback=progress_callback)
    
    def process_and_chunk_file(self, file_path: str, progress_callback=None) -> List[Dict[str, Any]]:
        """
        处理文件并进行分块，一站式服务
        
        Args:
            file_path: 文件路径
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            
        Returns:
            List[Dict]: 分块后的文档列表
        """
        if progress_callback:
            progress_callback(10, f"开始处理文件: {os.path.basename(file_path)}")
            
        file_info = self.process_file(file_path)
        if not file_info.get("content"):
            logger.error(f"文件 {file_path} 内容为空或处理失败")
            if progress_callback:
                progress_callback(100, f"文件处理失败: {os.path.basename(file_path)}")
            return []
        
        if progress_callback:
            progress_callback(30, "文件读取完成，开始分块处理")
        
        # 定义一个包装函数来处理进度回调的比例调整
        def chunk_progress_wrapper(progress, message):
            if progress_callback:
                # 将分块进度(0-100)映射到总进度的30%-90%区间
                adjusted_progress = 30 + (progress * 0.6)
                progress_callback(adjusted_progress, message)
        
        chunks = self.chunk_document(file_info["content"], progress_callback=chunk_progress_wrapper)
        
        if progress_callback:
            progress_callback(90, "分块处理完成，正在添加元数据")
        
        # 为每个块添加文件元数据
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["file_name"] = file_info.get("file_name", "")
            chunk["metadata"]["file_path"] = file_info.get("file_path", "")
            chunk["metadata"]["file_type"] = file_info.get("file_type", "")
        
        if progress_callback:
            progress_callback(100, f"文件处理完成: {os.path.basename(file_path)}, 共生成 {len(chunks)} 个分块")
        
        return chunks
    
    def change_chunk_method(self, method: str, **kwargs) -> bool:
        """
        更改分块方法
        
        Args:
            method: 新的分块方法
            **kwargs: 其他参数
            
        Returns:
            bool: 是否成功更改
        """
        return self.chunker.change_method(method, **kwargs)

    def process_document(self, file_path: str, chunk_method: str = None, chunk_size: int = None, 
                         chunk_overlap: int = None, progress_callback=None):
        """
        处理文档并进行分块，一站式处理文件到分块的过程
        
        Args:
            file_path: 文件路径
            chunk_method: 分块方法，如果提供则会临时切换分块方法
            chunk_size: 块大小，如果提供则会临时调整
            chunk_overlap: 块重叠大小，如果提供则会临时调整
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            
        Returns:
            List[Dict]: 分块后的文档列表
        """
        try:
            # 保存原始分块设置
            original_method = None
            original_size = None
            original_overlap = None
            
            # 如果提供了新的分块参数，临时更改分块器配置
            if chunk_method or chunk_size or chunk_overlap:
                if progress_callback:
                    progress_callback(5, "配置分块参数...")
                
                # 保存原始配置
                original_method = self.chunker.method
                original_size = self.chunker.chunk_size
                original_overlap = self.chunker.chunk_overlap
                
                # 应用新配置
                params = {}
                if chunk_size:
                    params['chunk_size'] = chunk_size
                if chunk_overlap:
                    params['chunk_overlap'] = chunk_overlap
                
                if chunk_method:
                    self.chunker.change_method(chunk_method, **params)
                elif params:
                    # 如果只改变了大小或重叠，不改变方法
                    if 'chunk_size' in params:
                        self.chunker.chunk_size = params['chunk_size']
                    if 'chunk_overlap' in params:
                        self.chunker.chunk_overlap = params['chunk_overlap']
                
                if progress_callback:
                    progress_callback(8, f"分块参数已配置 - 方法:{chunk_method or self.chunker.method.value}, 大小:{self.chunker.chunk_size}, 重叠:{self.chunker.chunk_overlap}")
            
            # 处理文件并分块
            try:
                chunks = self.process_and_chunk_file(file_path, progress_callback=progress_callback)
                
                # 添加额外的元数据
                if chunks:
                    unique_id = os.path.basename(file_path)
                    for i, chunk in enumerate(chunks):
                        if "metadata" not in chunk:
                            chunk["metadata"] = {}
                        # 添加唯一ID和位置信息
                        chunk["metadata"]["document_id"] = unique_id
                        chunk["metadata"]["chunk_index"] = i
                        chunk["metadata"]["total_chunks"] = len(chunks)
                
                return chunks
            finally:
                # 恢复原始分块设置
                if original_method or original_size or original_overlap:
                    restore_params = {}
                    if original_size:
                        restore_params['chunk_size'] = original_size
                    if original_overlap:
                        restore_params['chunk_overlap'] = original_overlap
                    
                    if original_method:
                        self.chunker.change_method(original_method, **restore_params)
                    else:
                        # 只恢复大小和重叠
                        if 'chunk_size' in restore_params:
                            self.chunker.chunk_size = restore_params['chunk_size']
                        if 'chunk_overlap' in restore_params:
                            self.chunker.chunk_overlap = restore_params['chunk_overlap']
        
        except Exception as e:
            logger.error(f"处理文档失败: {str(e)}")
            if progress_callback:
                progress_callback(100, f"处理文档失败: {str(e)}")
            return []


class RAGService:
    """
    检索增强生成(RAG)服务类，提供向量知识库的基础功能
    """
    
    def __init__(self, db_path: str = os.path.join(os.path.dirname(__file__), "db")):
        """
        初始化RAG服务
        
        Args:
            db_path: 向量数据库存储路径
        """
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.vector_db = FaissManager(os.path.join(db_path, "faiss_indexes"))
        self.lineage_tracker = DataLineageTracker()
        self.doc_processor = DocumentProcessor()

    def kb_exists(self, kb_name: str) -> bool:
        """
        检查知识库是否存在
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            bool: 知识库是否存在
        """
        return self.vector_db.collection_exists(kb_name)
        
        
    def create_knowledge_base(self, kb_name: str, dimension: int = 512, index_type: str = "Flat") -> bool:
        """
        创建新的知识库
        
        Args:
            kb_name: 知识库名称
            dimension: 向量维度，默认为512（与embedding模型匹配）
            index_type: 索引类型，支持"Flat"、"IVF"、"HNSW"
            
        Returns:
            bool: 创建是否成功
        """
        return self.vector_db.create_collection(kb_name, dimension, index_type)
    
    def list_knowledge_bases(self) -> List[str]:
        """
        获取所有知识库列表
        
        Returns:
            List[str]: 知识库名称列表
        """
        return self.vector_db.list_collections()
    
    def get_knowledge_base_info(self, kb_name: str) -> Dict[str, Any]:
        """
        获取知识库信息
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            Dict: 知识库信息
        """
        return self.vector_db.get_collection_info(kb_name)
    
    def delete_knowledge_base(self, kb_name: str) -> bool:
        """
        删除知识库
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            bool: 删除是否成功
        """
        return self.vector_db.delete_collection(kb_name)
    
    def add_documents(self, kb_name: str, documents: List[Dict[str, Any]], file_path: str = None, 
                    progress_callback=None, check_duplicates: bool = True) -> bool:
        """
        向知识库添加文档
        
        Args:
            kb_name: 知识库名称
            documents: 文档列表，每个文档为包含text字段的字典
            file_path: 文档来源的文件路径，用于文件级管理
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            check_duplicates: 是否检查重复文档
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 检查知识库是否存在
            if not self.vector_db.collection_exists(kb_name):
                error_msg = f"知识库 {kb_name} 不存在"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                if progress_callback:
                    progress_callback(100, f"添加失败：{error_msg}")
                return False
            
            # 检查文档列表是否为空
            if not documents:
                error_msg = f"文档列表为空，无法添加到知识库 {kb_name}"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                if progress_callback:
                    progress_callback(100, f"添加失败：{error_msg}")
                return False
            
            if progress_callback:
                progress_callback(0, f"开始向知识库 {kb_name} 添加 {len(documents)} 个文档")
            
            print(f"开始处理 {len(documents)} 个文档，准备添加到知识库 {kb_name}")
            
            # 提取文本并生成向量
            texts = [doc.get("text", "") for doc in documents]
            
            # 检查是否有空文本
            empty_texts = [i for i, text in enumerate(texts) if not text.strip()]
            if empty_texts:
                print(f"WARNING: 发现 {len(empty_texts)} 个空文本分块: {empty_texts}")
            
            vectors = []
            total_texts = len(texts)
            
            if progress_callback:
                progress_callback(10, f"开始生成 {total_texts} 个文档的向量表示")
                
            print(f"开始生成向量，共 {total_texts} 个文本")
            
            for i, text in enumerate(texts):
                try:
                    if not text.strip():
                        print(f"WARNING: 跳过空文本 (索引 {i})")
                        # 为空文本创建零向量或跳过
                        continue
                        
                    vector = get_embedding(text)
                    if vector is None or len(vector) == 0:
                        print(f"ERROR: 文本 {i} 生成向量失败")
                        continue
                        
                    vectors.append(vector)
                    
                    # 每处理10%的文档报告一次进度
                    if progress_callback and i % max(1, total_texts // 10) == 0:
                        progress_percent = 10 + int((i / total_texts) * 40)  # 10%-50%的进度区间
                        progress_callback(progress_percent, f"已生成 {i+1}/{total_texts} 个向量")
                        
                except Exception as e:
                    error_msg = f"生成第 {i} 个文档的向量时出错: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    logger.error(error_msg)
                    continue
            
            if not vectors:
                error_msg = f"没有成功生成任何向量，无法添加到知识库"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                if progress_callback:
                    progress_callback(100, f"添加失败：{error_msg}")
                return False
            
            print(f"成功生成 {len(vectors)} 个向量")
            
            if progress_callback:
                progress_callback(50, f"向量生成完成，开始添加到知识库")
                
            # 添加向量到知识库，启用去重功能
            print(f"开始调用 vector_db.add_vectors，知识库: {kb_name}")
            result = self.vector_db.add_vectors(kb_name, np.array(vectors), documents, file_path)
            
            print(f"vector_db.add_vectors 返回结果: {result}")
            
            if result.get("status") == "success":
                success_msg = f"成功添加文档到知识库 {kb_name}: {result.get('message', '')}"
                print(f"SUCCESS: {success_msg}")
                if progress_callback:
                    progress_callback(100, success_msg)
                return True
            elif result.get("status") == "error":
                error_msg = f"添加文档到知识库 {kb_name} 失败: {result.get('message', '')}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                if progress_callback:
                    progress_callback(100, f"添加失败：{result.get('message', '')}")
                return False
            else:
                error_msg = f"未知的返回状态: {result}"
                print(f"ERROR: {error_msg}")
                logger.error(error_msg)
                if progress_callback:
                    progress_callback(100, f"添加失败：{error_msg}")
                return False
            
        except Exception as e:
            error_msg = f"向知识库 {kb_name} 添加文档失败: {str(e)}"
            print(f"EXCEPTION: {error_msg}")
            logger.error(error_msg)
            logger.exception(e)
            if progress_callback:
                progress_callback(100, f"添加失败：{str(e)}")
            return False
    
    def add_file(self, kb_name: str, file_path: str, progress_callback=None, check_duplicates: bool = True) -> bool:
        """
        处理文件并添加到知识库
        
        Args:
            kb_name: 知识库名称
            file_path: 文件路径
            progress_callback: 进度回调函数，接收一个0-100的进度值和一个描述字符串
            check_duplicates: 是否检查重复文档
            
        Returns:
            bool: 添加是否成功
        """
        try:
            if progress_callback:
                progress_callback(0, f"开始处理文件：{os.path.basename(file_path)}")
            
            # 定义一个包装函数来处理进度回调的比例调整（文件处理部分占50%的进度）
            def process_progress_wrapper(progress, message):
                if progress_callback:
                    adjusted_progress = int(progress * 0.5)  # 0-50%的进度区间
                    progress_callback(adjusted_progress, message)
            
            # 使用文档处理器处理文件
            chunks = self.doc_processor.process_and_chunk_file(file_path, progress_callback=process_progress_wrapper)
            if not chunks:
                logger.error(f"文件 {file_path} 处理失败或无内容")
                if progress_callback:
                    progress_callback(100, f"添加失败：文件 {file_path} 处理失败或无内容")
                return False
            
            if progress_callback:
                progress_callback(50, f"文件处理完成，生成了 {len(chunks)} 个分块，开始添加到知识库")
            
            # 定义一个包装函数来处理进度回调的比例调整（知识库添加部分占50%-100%的进度区间）
            def add_progress_wrapper(progress, message):
                if progress_callback:
                    adjusted_progress = 50 + int(progress * 0.5)  # 50%-100%的进度区间
                    progress_callback(adjusted_progress, message)
            
            # 添加到知识库
            return self.add_documents(kb_name, chunks, file_path, 
                                     progress_callback=add_progress_wrapper,
                                     check_duplicates=check_duplicates)
            
        except Exception as e:
            logger.error(f"添加文件 {file_path} 到知识库 {kb_name} 失败: {str(e)}")
            if progress_callback:
                progress_callback(100, f"添加失败：{str(e)}")
            return False
    
    def list_files(self, kb_name: str) -> List[Dict[str, Any]]:
        """获取知识库中的所有文件信息"""
        return self.vector_db.list_files(kb_name)
        
    def update_file_importance(self, kb_name: str, file_name: str, importance_factor: float) -> bool:
        """更新文件的重要性系数
        
        参数:
            kb_name: 知识库名称
            file_name: 文件名
            importance_factor: 重要性系数 (0.1-5.0)
            
        返回:
            更新是否成功
        """
        try:
            # 确保系数在有效范围内
            if importance_factor < 0.1:
                importance_factor = 0.1
            elif importance_factor > 5.0:
                importance_factor = 5.0
                
            # 更新文件元数据
            return self.vector_db.update_file_metadata(
                kb_name, 
                file_name, 
                {"importance_coefficient": importance_factor}
            )
        except Exception as e:
            logger.error(f"更新文件重要性系数失败: {str(e)}")
            logger.exception(e)
            return False
            
    def search(self, kb_name: str, query: str, top_k: int = 5, 
               use_rerank: bool = True, remove_duplicates: bool = True,
               filter_criteria: str = "") -> List[Dict[str, Any]]:
        """搜索知识库
        
        参数:
            kb_name: 知识库名称
            query: 查询文本
            top_k: 返回的最大结果数
            use_rerank: 是否使用重排序
            remove_duplicates: 是否去除重复内容
            filter_criteria: 过滤条件
            
        返回:
            检索结果列表
        """
        logger.info(f"搜索知识库 {kb_name}, 查询: {query}, top_k: {top_k}, 使用重排序: {use_rerank}")
        
        # if not self.vector_db or not self.embedding_model:
        #     raise Exception("向量数据库或嵌入模型未初始化")
            
        if not self.vector_db.kb_exists(kb_name):
            logger.warning(f"知识库 {kb_name} 不存在")
            return []
            
        # 将查询转换为向量
        try:
            query_vector = get_embedding(query)
        except Exception as e:
            logger.error(f"查询向量化失败: {str(e)}")
            logger.exception(e)
            return []
            
        # 向量搜索，获取更多结果用于重排序
        search_top_k = top_k * 3 if use_rerank else top_k

        # 调用vector_db的search方法，获取索引、相似度和元数据
        indices, similarities, metadata_list = self.vector_db.search(kb_name, query_vector, search_top_k)
        
        if not indices or not similarities or not metadata_list:
            logger.info(f"未找到匹配结果")
            return []
            
        # 将原始搜索结果组织成统一格式
        search_results = []
        for idx, sim, meta in zip(indices, similarities, metadata_list):
            # 提取重要性系数，默认为1.0
            importance_coef = meta.get("metadata", {}).get("importance_coefficient", 1.0)
            
            # 确保系数在有效范围内
            if not isinstance(importance_coef, (int, float)) or importance_coef <= 0:
                importance_coef = 1.0
                
            # 调整分数
            adjusted_score = sim * float(importance_coef)
            
            result_item = {
                "index": idx,
                "score": adjusted_score,
                "text": meta.get("text", ""),
                "metadata": meta.get("metadata", {})
            }
            search_results.append(result_item)
            
        # 如果使用重排序，则应用重排序模型
        if use_rerank and len(search_results) > 0:
            try:
                documents = [item["text"] for item in search_results]
                logger.info(f"向量搜索返回了 {len(documents)} 条结果")
                
                # 使用重排序模型
                if load_rerank_model():
                    logger.info(f"使用重排序模型对 {len(documents)} 条结果进行重排序")
                    # 获取重排序结果
                    ranked_results = reranker(query, documents)
                    
                    # 重新组织结果
                    reranked_results = []
                    for doc, score in ranked_results:
                        # 找到原始文档的索引
                        original_index = documents.index(doc)
                        orig_result = search_results[original_index]
                        
                        # 提取重要性系数
                        importance_coef = orig_result["metadata"].get("importance_coefficient", 1.0)
                        if not isinstance(importance_coef, (int, float)) or importance_coef <= 0:
                            importance_coef = 1.0
                            
                        # 应用重要性系数到重排序分数
                        adjusted_score = score * float(importance_coef)
                        
                        # 创建新的结果项
                        result_item = orig_result.copy()
                        result_item["score"] = adjusted_score
                        reranked_results.append(result_item)
                    
                    # 按分数降序排序
                    reranked_results.sort(key=lambda x: x["score"], reverse=True)
                    
                    # 只保留top_k个结果
                    search_results = reranked_results[:top_k]
                else:
                    logger.warning("重排序模型未加载，使用原始向量搜索结果")
                    # 按分数降序排序
                    search_results.sort(key=lambda x: x["score"], reverse=True)
                    search_results = search_results[:top_k]
            except Exception as e:
                logger.error(f"重排序失败: {str(e)}")
                logger.exception(e)
                # 按分数降序排序
                search_results.sort(key=lambda x: x["score"], reverse=True)
                search_results = search_results[:top_k]
        else:
            # 不使用重排序，直接按分数排序并截取top_k个结果
            search_results.sort(key=lambda x: x["score"], reverse=True)
            search_results = search_results[:top_k]
            
        # 如果需要去重，则移除内容相似的结果
        if remove_duplicates:
            try:
                unique_results = []
                unique_contents = set()
                
                for item in search_results:
                    content = item["text"].strip()
                    # 创建一个简单的签名用于去重 (前100个字符)
                    content_signature = content[:100]
                    
                    if content_signature not in unique_contents:
                        unique_contents.add(content_signature)
                        unique_results.append(item)
                        
                search_results = unique_results
            except Exception as e:
                logger.error(f"去除重复内容失败: {str(e)}")
                logger.exception(e)
                
        # 格式化最终结果
        formatted_results = []
        for item in search_results:
            result = {
                "content": item["text"],
                "score": round(item["score"], 3),
                "metadata": item["metadata"]
            }
            formatted_results.append(result)
            
        return formatted_results
    
    def get_file_info(self, kb_name: str, file_name: str) -> Dict[str, Any]:
        """
        获取知识库中特定文件的详细信息
        
        Args:
            kb_name: 知识库名称
            file_name: 文件名
            
        Returns:
            Dict: 文件详细信息
        """
        return self.vector_db.get_file_info(kb_name, file_name)
    
    def replace_file(self, kb_name: str, file_path: str, documents: List[Dict[str, Any]]) -> bool:
        """
        替换知识库中的文件内容
        
        Args:
            kb_name: 知识库名称
            file_path: 文件路径
            documents: 新的文档列表
            
        Returns:
            bool: 替换是否成功
        """
        if not self.vector_db.collection_exists(kb_name):
            logger.error(f"知识库 {kb_name} 不存在")
            return False
            
        try:
            # 提取文本并生成向量
            texts = [doc.get("text", "") for doc in documents]
            vectors = []
            
            for text in texts:
                vector = get_embedding(text)
                vectors.append(vector)
                
            # 替换文件
            return self.vector_db.replace_file(kb_name, file_path, vectors, documents)
            
        except Exception as e:
            logger.error(f"替换知识库 {kb_name} 中的文件 {file_path} 失败: {str(e)}")
            return False
    
    def delete_file(self, kb_name: str, file_name: str) -> bool:
        """
        从知识库中删除文件及其所有向量
        
        Args:
            kb_name: 知识库名称
            file_name: 文件名
            
        Returns:
            bool: 删除是否成功
        """
        return self.vector_db.delete_file(kb_name, file_name)
    
    def restore_file_version(self, kb_name: str, file_name: str, version: int) -> bool:
        """
        恢复文件的特定版本
        
        Args:
            kb_name: 知识库名称
            file_name: 文件名
            version: 要恢复的版本号
            
        Returns:
            bool: 恢复是否成功
        """
        return self.vector_db.restore_file_version(kb_name, file_name, version)
    
    def track_document_lineage(self, document_id: str, source_info: Dict[str, Any]) -> None:
        """
        跟踪文档的数据血缘关系
        
        Args:
            document_id: 文档ID
            source_info: 来源信息
        """
        self.lineage_tracker.track_document_creation(document_id, source_info)
    
    def diagnose_kb(self, kb_name: str) -> Dict[str, Any]:
        """
        诊断知识库是否存在数据一致性问题
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            Dict: 诊断结果
        """
        if not self.vector_db.collection_exists(kb_name):
            return {
                "status": "error",
                "message": f"知识库 {kb_name} 不存在",
                "collection_exists": False
            }
        
        return self.vector_db.diagnose_knowledge_base(kb_name)
    
    def repair_kb(self, kb_name: str) -> Dict[str, Any]:
        """
        修复知识库的数据一致性问题
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            Dict: 修复结果
        """
        if not self.vector_db.collection_exists(kb_name):
            return {
                "status": "error",
                "message": f"知识库 {kb_name} 不存在",
                "success": False
            }
        
        return self.vector_db.repair_knowledge_base(kb_name)
    
    def reindex_kb(self, kb_name: str, file_name: str = None) -> Dict[str, Any]:
        """
        重新索引知识库中的内容
        
        Args:
            kb_name: 知识库名称
            file_name: 文件名（可选，如果提供则只重新索引特定文件）
            
        Returns:
            Dict: 重新索引的结果
        """
        if not self.vector_db.collection_exists(kb_name):
            logger.error(f"知识库 {kb_name} 不存在")
            return {"error": f"知识库 {kb_name} 不存在"}
            
        try:
            # 获取全部文件信息
            all_files = self.vector_db.list_files(kb_name)
            
            if not all_files:
                logger.warning(f"知识库 {kb_name} 中没有文件需要重新索引")
                return {"message": "没有文件需要重新索引", "reindexed_files": 0}
                
            files_to_reindex = []
            if file_name:
                # 只重新索引特定文件
                file_info = next((f for f in all_files if f.get('file_name') == file_name), None)
                if file_info:
                    files_to_reindex.append(file_info)
                else:
                    return {"error": f"文件 {file_name} 在知识库 {kb_name} 中不存在"}
            else:
                # 重新索引所有文件
                files_to_reindex = all_files
                
            reindexed_files = 0
            for file_info in files_to_reindex:
                # 获取详细信息包括向量
                detailed_info = self.vector_db.get_file_info(kb_name, file_info['file_name'])
                
                if 'versions' in detailed_info and detailed_info['versions']:
                    # 获取最新版本的元数据
                    current_version = detailed_info['current_version']
                    current_version_info = next((v for v in detailed_info['versions'] if v['version'] == current_version), None)
                    
                    if current_version_info and 'vector_ids' in current_version_info:
                        # 获取向量ID列表
                        vector_ids = current_version_info['vector_ids']
                        
                        # 获取对应的元数据
                        metadata_list = []
                        for vid in vector_ids:
                            meta = self.vector_db.get_metadata_by_id(kb_name, vid)
                            if meta and 'text' in meta:
                                metadata_list.append(meta)
                        
                        if metadata_list:
                            # 删除旧文件
                            self.vector_db.delete_file(kb_name, file_info['file_name'])
                            
                            # 提取文本并生成新向量
                            texts = [doc.get("text", "") for doc in metadata_list]
                            vectors = []
                            
                            for text in texts:
                                if text:
                                    vector = get_embedding(text)
                                    vectors.append(vector)
                            
                            # 添加新向量
                            if vectors:
                                file_path = detailed_info.get('file_path', file_info.get('file_path', ''))
                                success = self.vector_db.add_vectors(kb_name, vectors, metadata_list, file_path)
                                
                                if success:
                                    reindexed_files += 1
                                    logger.info(f"成功重新索引文件 {file_info['file_name']}")
                                else:
                                    logger.error(f"重新索引文件 {file_info['file_name']} 失败")
            
            logger.info(f"完成知识库 {kb_name} 的重新索引，处理了 {reindexed_files}/{len(files_to_reindex)} 个文件")
            
            return {
                "message": f"成功重新索引 {reindexed_files} 个文件",
                "reindexed_files": reindexed_files,
                "total_files": len(files_to_reindex)
            }
            
        except Exception as e:
            logger.error(f"重新索引知识库 {kb_name} 时出错: {str(e)}")
            logger.exception(e)
            return {"error": str(e)}

    def chat_with_kb(self, kb_name: str, query: str, history: List[Dict[str, str]] = None,
                           top_k: int = 5, temperature: float = 0.7, use_rerank: bool = True):
        """
        基于知识库内容进行对话，返回结构化的流式响应
        
        参数:
            kb_name: 知识库名称
            query: 用户当前的查询内容
            history: 对话历史记录
            top_k: 知识库检索的结果数量
            temperature: 生成时的温度参数，控制输出的随机性
            use_rerank: 是否使用重排序
            
        返回:
            JSON字符串的生成器，每个JSON对象包含 type 和 data 字段
        """
        try:
            # 检查知识库是否存在
            if not self.kb_exists(kb_name):
                yield json.dumps({"type": "error", "data": f"知识库 {kb_name} 不存在。"}) + "\n"
                return
            
            # 1. 检索内容
            search_results = self.search(
                kb_name=kb_name,
                query=query,
                top_k=top_k,
                use_rerank=use_rerank,
                remove_duplicates=True
            )
            
            # 2. 将检索结果作为上下文发送给前端
            if search_results:
                yield json.dumps({"type": "context", "data": search_results}) + "\n"
            
            if not search_results:
                logger.warning(f"在知识库 {kb_name} 中未找到与查询 '{query}' 相关的内容")
                yield json.dumps({"type": "answer", "data": "很抱歉，我在知识库中没有找到与您问题相关的信息。请尝试用不同的方式提问，或者询问其他内容。"}) + "\n"
                return
            
            # 3. 整理上下文并生成回答
            context_texts = [res.get("content", "") for res in search_results if res.get("content")]
            
            try:
                from core.llm.local_llm_model import get_llm_model
                model = get_llm_model()
                
                # 准备历史记录
                formatted_history = []
                if history:
                    i = 0
                    while i < len(history) - 1:
                        if history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
                            formatted_history.append([history[i]["content"], history[i+1]["content"]])
                            i += 2
                        else:
                            i += 1
                
                # 4. 流式生成并发送模型回答
                for chunk in model.generate_stream(
                    query=query,
                    context=context_texts,
                    history=formatted_history,
                    temperature=temperature
                ):
                    yield json.dumps({"type": "answer", "data": chunk}) + "\n"
                
            except ImportError as e:
                logger.error(f"未能导入LLM模型: {str(e)}")
                yield json.dumps({"type": "error", "data": "系统未能加载语言模型，无法生成回答。"}) + "\n"
                
            except Exception as e:
                logger.error(f"生成回答时出错: {str(e)}")
                yield json.dumps({"type": "error", "data": f"生成回答时出错: {str(e)}"}) + "\n"
                
        except Exception as e:
            logger.error(f"与知识库对话失败: {str(e)}")
            yield json.dumps({"type": "error", "data": f"处理您的问题时发生错误: {str(e)}"}) + "\n"

    def chat_with_kb_sync(self, kb_name: str, query: str, history: List[Dict[str, str]] = None,
                           top_k: int = 5, temperature: float = 0.7, use_rerank: bool = True):
        """
        基于知识库内容进行对话，返回完整响应（非流式）
        
        Args:
            kb_name: 知识库名称
            query: 用户当前的查询内容
            history: 对话历史记录，格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            top_k: 知识库检索的结果数量
            temperature: 生成时的温度参数，控制输出的随机性
            use_rerank: 是否使用重排序
            
        Returns:
            生成的完整文本
        """
        try:
            # 检查知识库是否存在
            if not self.kb_exists(kb_name):
                return f"错误：知识库 {kb_name} 不存在。"
            
            # 从知识库中检索相关内容
            search_results = self.search(
                kb_name=kb_name,
                query=query,
                top_k=top_k,
                use_rerank=use_rerank,
                remove_duplicates=True
            )
            
            if not search_results:
                logger.warning(f"在知识库 {kb_name} 中未找到与查询 '{query}' 相关的内容")
                return "很抱歉，我在知识库中没有找到与您问题相关的信息。请尝试用不同的方式提问，或者询问其他内容。"
            
            # 整理检索到的内容，准备提供给语言模型
            context_texts = []
            for i, result in enumerate(search_results):
                content = result.get("content", "")
                if content:
                    # 格式化检索结果，包含相关性分数
                    context_text = f"[{i+1}] {content} (相关度: {result.get('score', 0.0)})"
                    context_texts.append(context_text)
            
            context = "\n\n".join(context_texts)
            context = f"总结参考信息{context}后回答问题"
            
            try:
                # 导入DeepSeekLLM模型
                from core.llm.local_llm_model import get_llm_model
                model = get_llm_model()
                
                # 准备对话历史（转换为local_llm_model格式）
                formatted_history = []
                if history:
                    # API传入的历史格式为[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
                    # 需要转换为DeepSeekLLM需要的格式：[[user_msg, assistant_msg], ...]
                    i = 0
                    while i < len(history) - 1:
                        user_msg = None
                        assistant_msg = None
                        
                        # 找到一对用户和助手消息
                        if history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
                            user_msg = history[i]["content"]
                            assistant_msg = history[i+1]["content"]
                            formatted_history.append([user_msg, assistant_msg])
                            i += 2
                        else:
                            # 如果格式不匹配，尝试向前移动一位
                            i += 1
                
                logger.info(f"对话历史记录已转换，共 {len(formatted_history)} 轮对话")
                
                # 生成完整回答（非流式）
                logger.info(f"开始生成回答查询: {query}")
                response = model.generate_response(
                    query=query,
                    context=context_texts,
                    history=formatted_history,
                    temperature=temperature
                )
                
                return response
                
            except ImportError as e:
                logger.error(f"未能导入LLM模型: {str(e)}")
                # 返回一个基于检索结果的简单回答
                return f"以下是与您问题相关的内容：\n\n{context}\n\n注：系统未能加载语言模型，仅返回知识库检索结果。"
                
            except Exception as e:
                logger.error(f"生成回答时出错: {str(e)}")
                logger.exception(e)
                return f"处理您的问题时发生错误: {str(e)}\n\n以下是相关的检索结果：\n\n{context}"
                
        except Exception as e:
            logger.error(f"与知识库对话失败: {str(e)}")
            logger.exception(e)
            return f"处理您的问题时发生错误: {str(e)}"

    def fix_dimension_mismatch(self, kb_name: str) -> Dict[str, Any]:
        """
        修复知识库的维度不匹配问题
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            Dict: 修复结果
        """
        return self.vector_db.fix_dimension_mismatch(kb_name, correct_dimension=512)


# if __name__ == "__main__":
#     # 文档上传
#     DocumentProcessor.add_file("test1", "test1.txt")

#     # 文档处理

#     # 文档搜索

#     # 文档管理

    
    
