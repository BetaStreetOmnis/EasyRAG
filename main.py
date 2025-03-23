import os
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional

# 导入自定义模块
from core.faiss_connect import FaissManager, DataLineageTracker
from core.embbeding_model import get_embedding
from core.rerank_model import reranker
from core.chunker.chunker_main import DocumentChunker, ChunkMethod
from core.file_read.file_handle import FileHandler

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
        self.file_handler = FileHandler()
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
        if not self.vector_db.collection_exists(kb_name):
            logger.error(f"知识库 {kb_name} 不存在")
            if progress_callback:
                progress_callback(100, f"添加失败：知识库 {kb_name} 不存在")
            return False
            
        try:
            if progress_callback:
                progress_callback(0, f"开始向知识库 {kb_name} 添加 {len(documents)} 个文档")
            
            # 提取文本并生成向量
            texts = [doc.get("text", "") for doc in documents]
            vectors = []
            
            total_texts = len(texts)
            
            if progress_callback:
                progress_callback(10, f"开始生成 {total_texts} 个文档的向量表示")
                
            for i, text in enumerate(texts):
                vector = get_embedding(text)
                vectors.append(vector)
                
                # 每处理10%的文档报告一次进度
                if progress_callback and i % max(1, total_texts // 10) == 0:
                    progress_percent = 10 + int((i / total_texts) * 40)  # 10%-50%的进度区间
                    progress_callback(progress_percent, f"已生成 {i}/{total_texts} 个向量")
            
            if progress_callback:
                progress_callback(50, f"向量生成完成，开始添加到知识库")
                
            # 添加向量到知识库，启用去重功能
            result = self.vector_db.add_vectors(kb_name, np.array(vectors), documents, file_path)
            
            if result.get("status") == "success" and progress_callback:
                progress_callback(100, f"成功添加文档到知识库 {kb_name}: {result.get('message', '')}")
                return True
            elif result.get("status") == "error" and progress_callback:
                progress_callback(100, f"添加文档到知识库 {kb_name} 失败: {result.get('message', '')}")
                return False
            
            # 根据status返回成功或失败
            return result.get("status") == "success"
            
        except Exception as e:
            logger.error(f"向知识库 {kb_name} 添加文档失败: {str(e)}")
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
    
    def search(self, kb_name: str, query: str, top_k: int = 5, use_rerank: bool = True, remove_duplicates: bool = True) -> List[Dict[str, Any]]:
        """
        在知识库中搜索与查询最相关的文档
        
        Args:
            kb_name: 知识库名称
            query: 查询文本
            top_k: 返回的最相似文档数量
            use_rerank: 是否使用重排序模型进一步优化结果
            remove_duplicates: 是否移除重复结果
            
        Returns:
            List[Dict]: 搜索结果列表，每个结果包含文档内容和相似度分数
        """
        if not self.vector_db.collection_exists(kb_name):
            logger.error(f"知识库 {kb_name} 不存在")
            return []
            
        try:
            # 将查询文本转换为向量
            query_vector = np.array(get_embedding(query))
            
            # 在向量数据库中搜索
            # 为重排序和去重获取更多候选
            search_top_k = top_k * 3 if (use_rerank or remove_duplicates) else top_k
            indices, similarities, metadata_list = self.vector_db.search(kb_name, query_vector, search_top_k)
            
            # 检查搜索结果
            if not indices or len(indices) == 0:
                logger.warning(f"在知识库 {kb_name} 中未找到与查询 '{query}' 相关的内容")
                return []
            
            # 提取文档文本
            documents = [meta.get("text", "") for meta in metadata_list]
            logger.info(f"向量搜索返回了 {len(documents)} 条结果")
            
            results = []
            
            # 如果启用重排序且有足够的结果
            if use_rerank and documents:
                logger.info(f"使用重排序模型对 {len(documents)} 条结果进行重排序")
                try:
                    # 使用重排序模型
                    ranked_results = reranker(query, documents)
                    
                    # 重新组织结果
                    seen_texts = set() if remove_duplicates else None
                    
                    for i, (doc, score) in enumerate(ranked_results):
                        # 跳过重复文本
                        if remove_duplicates:
                            doc_text = doc.strip()
                            if not doc_text or doc_text in seen_texts:
                                logger.info(f"跳过重复文本: {doc_text[:30]}...")
                                continue
                            seen_texts.add(doc_text)
                        
                        # 找到对应的原始元数据
                        try:
                            original_index = documents.index(doc)
                            metadata = metadata_list[original_index]
                        except ValueError:
                            logger.warning(f"无法找到文档的原始元数据: {doc[:50]}...")
                            metadata = {"text": doc}
                        
                        results.append({
                            "text": doc,
                            "score": float(score),
                            "metadata": metadata
                        })
                        
                        # 如果已经收集了足够的不重复结果，就停止
                        if len(results) >= top_k:
                            break
                
                except Exception as e:
                    logger.error(f"重排序过程中发生错误: {str(e)}")
                    # 如果重排序失败，回退到向量搜索结果
                    use_rerank = False
                
            # 不使用重排序，或者重排序失败，直接返回向量搜索结果
            if not use_rerank or not results:
                logger.info("使用向量搜索结果")
                seen_texts = set() if remove_duplicates else None
                
                for i, (idx, sim, meta) in enumerate(zip(indices, similarities, metadata_list)):
                    doc_text = meta.get("text", "").strip()
                    
                    # 跳过重复文本
                    if remove_duplicates:
                        if not doc_text or doc_text in seen_texts:
                            logger.info(f"跳过重复文本: {doc_text[:30]}...")
                            continue
                        seen_texts.add(doc_text)
                    
                    results.append({
                        "text": doc_text,
                        "score": float(sim * 100),  # 转换为百分比
                        "metadata": meta
                    })
                    
                    # 如果已经收集了足够的不重复结果，就停止
                    if len(results) >= top_k:
                        break
            
            logger.info(f"最终返回 {len(results)} 条结果")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"搜索知识库 {kb_name} 时出错: {str(e)}")
            logger.exception(e)
            return []
    
    def list_files(self, kb_name: str) -> List[Dict[str, Any]]:
        """
        获取知识库中的所有文件信息
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            List[Dict]: 文件信息列表
        """
        return self.vector_db.list_files(kb_name)
    
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


if __name__ == "__main__":
    # 文档上传
    DocumentProcessor.add_file("test1", "test1.txt")

    # 文档处理

    # 文档搜索

    # 文档管理

    
    
