import os
import numpy as np
import faiss
import pickle
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
import time
import json
from datetime import datetime
import urllib.parse
import math
import traceback

logger = logging.getLogger(__name__)

class FaissManager:
    """
    FAISS向量数据库管理类，提供创建、查询、写入、删除等操作，
    并支持文件级别的管理，包括文件版本控制和文件替换
    """
    
    def __init__(self, index_folder: str = "../db/faiss_indexes"):
        """
        初始化FAISS管理器
        
        Args:
            index_folder: 索引文件夹路径
        """
        try:
            # 设置索引存储路径
            self.index_folder = index_folder
            os.makedirs(index_folder, exist_ok=True)
            
            # 存储映射: 集合名称 -> 索引/元数据
            self.indexes = {}  # 存储加载的FAISS索引
            self.metadata = {}  # 存储向量对应的元数据
            self.file_registry = {}  # 存储文件信息
            self.file_change_history = {}  # 存储文件变更历史
            
            # 检查版本和依赖
            logger.info(f"初始化FAISS管理器，FAISS版本: {faiss.__version__}")
            logger.info(f"索引存储路径: {os.path.abspath(index_folder)}")
            
            # 检查预先存在的集合
            collections = self.list_collections()
            logger.info(f"发现 {len(collections)} 个已存在的知识库集合: {collections}")
            
            # 记录初始化事件
            logger.info("FAISS管理器初始化完成")
        except Exception as e:
            logger.error(f"初始化FAISS管理器时出错: {str(e)}")
            logger.exception(e)
            # 尽管发生错误，但仍然初始化对象，以便后续操作可以尝试恢复
            self.indexes = {}
            self.metadata = {}
            self.file_registry = {}
            self.file_change_history = {}
        
    def _get_index_path(self, collection_name: str) -> str:
        """
        获取索引文件路径
        
        Args:
            collection_name: 集合名称
            
        Returns:
            str: 索引文件路径
        """
        # 对集合名称进行URL编码，避免中文路径问题
        safe_name = urllib.parse.quote(collection_name, safe='')
        return os.path.join(self.index_folder, f"{safe_name}.index")
        
    def _get_metadata_path(self, collection_name: str) -> str:
        """
        获取元数据文件路径
        
        Args:
            collection_name: 集合名称
            
        Returns:
            str: 元数据文件路径
        """
        # 对集合名称进行URL编码，避免中文路径问题
        safe_name = urllib.parse.quote(collection_name, safe='')
        return os.path.join(self.index_folder, f"{safe_name}.meta")
        
    def kb_exists(self, kb_name: str) -> bool:
        """
        检查知识库是否存在
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            bool: 知识库是否存在
        """
        try:
            # 检查索引文件和元数据文件是否存在
            index_path = self._get_index_path(kb_name)
            metadata_path = self._get_metadata_path(kb_name)
            
            # 如果两个文件都存在，则认为知识库存在
            return os.path.exists(index_path) and os.path.exists(metadata_path)
        except Exception as e:
            logger.error(f"检查知识库 {kb_name} 是否存在时出错: {str(e)}")
            return False
    
    def _get_file_registry_path(self, collection_name: str) -> str:
        """
        获取文件注册表路径
        
        Args:
            collection_name: 集合名称
            
        Returns:
            str: 文件注册表路径
        """
        # 对集合名称进行URL编码，避免中文路径问题
        safe_name = urllib.parse.quote(collection_name, safe='')
        return os.path.join(self.index_folder, f"{safe_name}.files.json")
    
    def _get_file_history_path(self, collection_name: str) -> str:
        """
        获取文件变更历史记录路径
        
        Args:
            collection_name: 集合名称
            
        Returns:
            str: 文件历史记录路径
        """
        # 对集合名称进行URL编码，避免中文路径问题
        safe_name = urllib.parse.quote(collection_name, safe='')
        return os.path.join(self.index_folder, f"{safe_name}.history.json")
    
    def _get_collection_info_path(self) -> str:
        """
        获取集合信息文件路径
        
        Returns:
            str: 集合信息文件路径
        """
        return os.path.join(self.index_folder, "collections_info.json")
    
    def create_collection(self, collection_name: str, dimension: int = 1536, index_type: str = "Flat") -> bool:
        """
        创建新的向量集合
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度，默认1536（适用于多种嵌入模型）
            index_type: 索引类型，支持"Flat"（精确搜索）、"IVF"（倒排索引）、"HNSW"（层次导航小世界图）
            
        Returns:
            bool: 创建是否成功
        """
        try:
            index_path = self._get_index_path(collection_name)
            metadata_path = self._get_metadata_path(collection_name)
            file_registry_path = self._get_file_registry_path(collection_name)
            file_history_path = self._get_file_history_path(collection_name)
            
            # 检查集合是否已存在
            if os.path.exists(index_path):
                logger.warning(f"集合 {collection_name} 已存在")
                return False
            
            # 根据索引类型创建相应的FAISS索引
            if index_type == "Flat":
                index = faiss.IndexFlatL2(dimension)  # 使用L2距离的Flat索引
            elif index_type == "IVF":
                # 创建量化器
                quantizer = faiss.IndexFlatL2(dimension)
                # 创建倒排索引，nlist为聚类中心数量
                nlist = max(4, int(math.sqrt(1000)))  # 根据预期向量数量调整
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
                # 训练空索引（理想情况下应该有训练数据）
                if not self._train_index(index, dimension):
                    return False
            elif index_type == "HNSW":
                # 创建HNSW索引，M为每个节点的最大连接数
                M = 16  # 默认值通常为16-64之间
                index = faiss.IndexHNSWFlat(dimension, M, faiss.METRIC_L2)
            else:
                logger.error(f"不支持的索引类型: {index_type}")
                return False
            
            # 写入索引到文件
            try:
                logger.info(f"创建索引文件: {index_path}")
                faiss.write_index(index, index_path)
            except Exception as e:
                logger.error(f"写入索引文件失败: {str(e)}")
                return False
            
            # 创建元数据文件
            try:
                logger.info(f"创建元数据文件: {metadata_path}")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"创建元数据文件失败: {str(e)}")
                # 清理已创建的索引文件
                if os.path.exists(index_path):
                    os.remove(index_path)
                return False
            
            # 创建文件注册表
            try:
                logger.info(f"创建文件注册表: {file_registry_path}")
                with open(file_registry_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception as e:
                logger.error(f"创建文件注册表失败: {str(e)}")
                # 清理已创建的文件
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                return False
            
            # 创建文件历史记录
            try:
                logger.info(f"创建文件历史记录: {file_history_path}")
                with open(file_history_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(f"创建文件历史记录失败: {str(e)}")
                # 清理已创建的文件
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                if os.path.exists(file_registry_path):
                    os.remove(file_registry_path)
                return False
            
            # 保存集合信息
            if not self._save_collection_info(collection_name, dimension, index_type):
                logger.error(f"保存集合信息失败")
                # 清理已创建的文件
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                if os.path.exists(file_registry_path):
                    os.remove(file_registry_path)
                if os.path.exists(file_history_path):
                    os.remove(file_history_path)
                return False
            
            logger.info(f"集合 {collection_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def _save_index(self, collection_name: str) -> bool:
        """
        保存索引到文件
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if collection_name in self.indexes:
                index_path = self._get_index_path(collection_name)
                # 确保在写入前索引状态是最新的
                index = self.indexes[collection_name]
                logger.info(f"保存索引 {collection_name}, 当前索引包含 {index.ntotal} 个向量")
                
                # 写入索引
                faiss.write_index(index, index_path)
                
                # 强制同步文件系统
                try:
                    os.fsync(os.open(index_path, os.O_RDONLY))
                except Exception as sync_err:
                    logger.warning(f"同步索引文件时出错 (非致命): {str(sync_err)}")
                
                # 验证索引文件是否成功写入及其大小
                if os.path.exists(index_path) and os.path.getsize(index_path) > 0:
                    # 再次读取索引文件以验证其完整性
                    try:
                        test_index = faiss.read_index(index_path)
                        if test_index.ntotal != index.ntotal:
                            logger.error(f"索引验证失败: 内存中有 {index.ntotal} 个向量，但文件中有 {test_index.ntotal} 个向量")
                            return False
                        logger.info(f"成功保存并验证索引到文件: {index_path}, 大小: {os.path.getsize(index_path)} 字节, 向量数: {test_index.ntotal}")
                        return True
                    except Exception as verify_err:
                        logger.error(f"验证索引文件时出错: {str(verify_err)}")
                        return False
                else:
                    logger.error(f"索引文件写入失败或为空: {index_path}")
                    return False
            else:
                logger.error(f"集合 {collection_name} 的索引不存在，无法保存")
                return False
        except Exception as e:
            logger.error(f"保存索引 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _save_metadata(self, collection_name: str) -> bool:
        """
        保存元数据到文件
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if collection_name in self.metadata:
                metadata_path = self._get_metadata_path(collection_name)
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata[collection_name], f)
                
                # 验证元数据文件是否成功写入
                if os.path.exists(metadata_path) and os.path.getsize(metadata_path) > 0:
                    logger.info(f"成功保存元数据到文件: {metadata_path}, 大小: {os.path.getsize(metadata_path)} 字节")
                    return True
                else:
                    logger.error(f"元数据文件写入失败或为空: {metadata_path}")
                    return False
            else:
                logger.error(f"集合 {collection_name} 的元数据不存在，无法保存")
                return False
        except Exception as e:
            logger.error(f"保存元数据 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _save_file_registry(self, collection_name: str) -> bool:
        """
        将文件注册表保存到文件
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if collection_name in self.file_registry:
                registry_path = self._get_file_registry_path(collection_name)
                
                # 检查文件注册表是否为空对象
                if not self.file_registry[collection_name]:
                    logger.warning(f"警告: 正在保存空的文件注册表 {collection_name}")
                    
                # 确保文件注册表至少包含基本信息
                if not isinstance(self.file_registry[collection_name], dict):
                    logger.error(f"文件注册表格式错误，非字典类型: {type(self.file_registry[collection_name])}")
                    self.file_registry[collection_name] = {
                        "_created_at": datetime.now().isoformat(),
                        "_last_updated": datetime.now().isoformat(),
                        "_file_count": 0,
                        "_vector_count": 0
                    }
                elif len(self.file_registry[collection_name]) == 0:
                    self.file_registry[collection_name] = {
                        "_created_at": datetime.now().isoformat(),
                        "_last_updated": datetime.now().isoformat(),
                        "_file_count": 0,
                        "_vector_count": 0
                    }
                else:
                    # 更新最后修改时间
                    self.file_registry[collection_name]["_last_updated"] = datetime.now().isoformat()
                    
                    # 计算并更新文件和向量计数
                    file_count = 0
                    vector_count = 0
                    for key, value in self.file_registry[collection_name].items():
                        if not key.startswith('_') and isinstance(value, dict):
                            file_count += 1
                            if "vector_count" in value:
                                vector_count += value["vector_count"]
                    
                    self.file_registry[collection_name]["_file_count"] = file_count
                    self.file_registry[collection_name]["_vector_count"] = vector_count
                
                # 写入文件注册表
                with open(registry_path, 'w', encoding='utf-8') as f:
                    json.dump(self.file_registry[collection_name], f, ensure_ascii=False, indent=2)
                
                # 同步文件系统
                try:
                    os.fsync(os.open(registry_path, os.O_RDONLY))
                except Exception as sync_err:
                    logger.warning(f"同步文件注册表时出错 (非致命): {str(sync_err)}")
                
                # 验证文件注册表是否成功写入
                if os.path.exists(registry_path) and os.path.getsize(registry_path) > 0:
                    # 再次读取文件以验证其完整性
                    try:
                        with open(registry_path, 'r', encoding='utf-8') as f:
                            test_registry = json.load(f)
                            logger.info(f"成功保存并验证文件注册表到文件: {registry_path}, 大小: {os.path.getsize(registry_path)} 字节, 条目数: {len(test_registry)}")
                            return True
                    except Exception as verify_err:
                        logger.error(f"验证文件注册表时出错: {str(verify_err)}")
                        return False
                else:
                    logger.error(f"文件注册表写入失败或为空: {registry_path}")
                    return False
            else:
                logger.error(f"集合 {collection_name} 的文件注册表不存在，无法保存")
                return False
        except Exception as e:
            logger.error(f"保存文件注册表 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _save_file_history(self, collection_name: str) -> None:
        """保存文件变更历史记录到文件"""
        if collection_name in self.file_change_history:
            with open(self._get_file_history_path(collection_name), 'w', encoding='utf-8') as f:
                json.dump(self.file_change_history[collection_name], f)
    
    def _record_collection_event(self, collection_name: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """记录集合事件"""
        if collection_name not in self.file_change_history:
            self.file_change_history[collection_name] = []
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": event_data
        }
        
        self.file_change_history[collection_name].append(event)
        self._save_file_history(collection_name)
    
    def _record_file_event(self, collection_name: str, file_name: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """记录文件事件"""
        if collection_name not in self.file_change_history:
            self.file_change_history[collection_name] = []
        
        event = {
            "event_type": event_type,
            "file_name": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": event_data
        }
        
        self.file_change_history[collection_name].append(event)
        self._save_file_history(collection_name)
    
    def _load_index(self, collection_name: str) -> bool:
        """
        从文件加载索引
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 加载是否成功
        """
        try:
            index_path = self._get_index_path(collection_name)
            if os.path.exists(index_path):
                file_size = os.path.getsize(index_path)
                logger.info(f"开始加载索引文件: {index_path}, 文件大小: {file_size} 字节")
                
                if file_size == 0:
                    logger.error(f"索引文件存在但为空: {index_path}")
                    return False
                
                # 尝试加载索引
                try:
                    index = faiss.read_index(index_path)
                    self.indexes[collection_name] = index
                    
                    # 记录索引信息
                    logger.info(f"成功加载索引 {collection_name}: 包含 {index.ntotal} 个向量, 维度: {index.d}")
                    
                    # 如果索引是空的，那可能是有问题的
                    if index.ntotal == 0:
                        logger.warning(f"索引 {collection_name} 加载成功，但不包含任何向量")
                        
                        # 检查元数据大小进行交叉验证
                        metadata_path = self._get_metadata_path(collection_name)
                        if os.path.exists(metadata_path) and os.path.getsize(metadata_path) > 100:
                            logger.warning(f"元数据文件大小 ({os.path.getsize(metadata_path)} 字节) 表明应该有数据，但索引为空")
                    
                    return True
                except Exception as e:
                    logger.error(f"索引文件损坏或格式错误: {str(e)}")
                    # 如果文件存在但读取失败，尝试备份并重新创建索引
                    backup_path = f"{index_path}.bak.{int(time.time())}"
                    try:
                        import shutil
                        shutil.copy2(index_path, backup_path)
                        logger.warning(f"已将损坏的索引文件备份到: {backup_path}")
                    except Exception as backup_err:
                        logger.error(f"备份损坏的索引文件失败: {str(backup_err)}")
                    
                    return False
            else:
                logger.warning(f"索引文件不存在: {index_path}")
                return False
        except Exception as e:
            logger.error(f"加载索引 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _load_metadata(self, collection_name: str) -> bool:
        """
        从文件加载元数据，支持JSON和pickle格式
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 加载是否成功
        """
        import pickle
        metadata_path = self._get_metadata_path(collection_name)
        if not os.path.exists(metadata_path):
            logger.warning(f"元数据文件不存在: {metadata_path}")
            self.metadata[collection_name] = {}
            return True
            
        # 首先尝试JSON格式
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata[collection_name] = json.load(f)
                logger.info(f"成功使用JSON格式加载元数据: {metadata_path}")
                return True
        except json.JSONDecodeError as e:
            logger.warning(f"使用JSON格式加载元数据失败，将尝试pickle格式: {str(e)}")
        except Exception as e:
            if "invalid load key" in str(e):
                logger.warning(f"可能是pickle格式的文件: {str(e)}")
            else:
                logger.error(f"加载元数据失败: {str(e)}")
                return False
                
        # 如果JSON失败，尝试pickle格式
        try:
            with open(metadata_path, 'rb') as f:
                self.metadata[collection_name] = pickle.load(f)
            logger.info(f"成功使用pickle格式加载元数据: {metadata_path}")
            
            # 将pickle格式转换为JSON格式保存回文件
            try:
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata[collection_name], f)
                logger.info(f"已将元数据从pickle格式转换为JSON格式: {metadata_path}")
            except Exception as e:
                logger.warning(f"将元数据从pickle转换为JSON失败: {str(e)}")
                
            return True
        except Exception as e:
            logger.error(f"使用pickle格式加载元数据也失败: {str(e)}")
            self.metadata[collection_name] = {}  # 初始化为空字典
            return False
    
    def _load_file_registry(self, collection_name: str) -> bool:
        """
        从文件加载文件注册表，支持JSON和pickle格式
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 加载是否成功
        """
        import pickle
        registry_path = self._get_file_registry_path(collection_name)
        if not os.path.exists(registry_path):
            logger.warning(f"文件注册表不存在: {registry_path}")
            self.file_registry[collection_name] = {}
            return True
            
        # 首先尝试JSON格式
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                self.file_registry[collection_name] = json.load(f)
                logger.info(f"成功使用JSON格式加载文件注册表: {registry_path}")
                return True
        except json.JSONDecodeError as e:
            logger.warning(f"使用JSON格式加载文件注册表失败，将尝试pickle格式: {str(e)}")
        except Exception as e:
            if "invalid load key" in str(e):
                logger.warning(f"可能是pickle格式的文件: {str(e)}")
            else:
                logger.error(f"加载文件注册表失败: {str(e)}")
                self.file_registry[collection_name] = {}
                return False
                
        # 如果JSON失败，尝试pickle格式
        try:
            with open(registry_path, 'rb') as f:
                self.file_registry[collection_name] = pickle.load(f)
            logger.info(f"成功使用pickle格式加载文件注册表: {registry_path}")
            
            # 将pickle格式转换为JSON格式保存回文件
            try:
                with open(registry_path, 'w', encoding='utf-8') as f:
                    json.dump(self.file_registry[collection_name], f)
                logger.info(f"已将文件注册表从pickle格式转换为JSON格式: {registry_path}")
            except Exception as e:
                logger.warning(f"将文件注册表从pickle转换为JSON失败: {str(e)}")
                
            return True
        except Exception as e:
            logger.error(f"使用pickle格式加载文件注册表也失败: {str(e)}")
            self.file_registry[collection_name] = {}
            return False
    
    def _load_file_history(self, collection_name: str) -> bool:
        """
        从文件加载文件变更历史记录，支持JSON和pickle格式
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 加载是否成功
        """
        import pickle
        history_path = self._get_file_history_path(collection_name)
        if not os.path.exists(history_path):
            logger.warning(f"文件变更历史记录不存在: {history_path}")
            self.file_change_history[collection_name] = []
            return True
            
        # 首先尝试JSON格式
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                self.file_change_history[collection_name] = json.load(f)
                logger.info(f"成功使用JSON格式加载文件变更历史: {history_path}")
                return True
        except json.JSONDecodeError as e:
            logger.warning(f"使用JSON格式加载文件变更历史失败，将尝试pickle格式: {str(e)}")
        except Exception as e:
            if "invalid load key" in str(e):
                logger.warning(f"可能是pickle格式的文件: {str(e)}")
            else:
                logger.error(f"加载文件变更历史失败: {str(e)}")
                self.file_change_history[collection_name] = []
                return False
                
        # 如果JSON失败，尝试pickle格式
        try:
            with open(history_path, 'rb') as f:
                self.file_change_history[collection_name] = pickle.load(f)
            logger.info(f"成功使用pickle格式加载文件变更历史: {history_path}")
            
            # 将pickle格式转换为JSON格式保存回文件
            try:
                with open(history_path, 'w', encoding='utf-8') as f:
                    json.dump(self.file_change_history[collection_name], f)
                logger.info(f"已将文件变更历史从pickle格式转换为JSON格式: {history_path}")
            except Exception as e:
                logger.warning(f"将文件变更历史从pickle转换为JSON失败: {str(e)}")
                
            return True
        except Exception as e:
            logger.error(f"使用pickle格式加载文件变更历史也失败: {str(e)}")
            self.file_change_history[collection_name] = []
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        检查集合是否存在
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 集合是否存在
        """
        # 先检查内存中是否已加载
        if collection_name in self.indexes:
            return True
            
        # 再检查文件是否存在
        index_path = self._get_index_path(collection_name)
        metadata_path = self._get_metadata_path(collection_name)
        return os.path.exists(index_path) and os.path.exists(metadata_path)
    
    def list_collections(self) -> List[str]:
        """
        获取所有集合名称列表
        
        Returns:
            List[str]: 集合名称列表
        """
        collections = []
        for filename in os.listdir(self.index_folder):
            if filename.endswith('.index'):
                collections.append(filename[:-6])  # 去掉.index后缀
        return collections
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            Dict: 集合信息，包括向量数量、维度等
        """
        if not self.collection_exists(collection_name):
            return {"error": f"集合 {collection_name} 不存在"}
            
        # 确保索引已加载
        if collection_name not in self.indexes:
            self._load_index(collection_name)
            
        # 确保文件注册表已加载
        if collection_name not in self.file_registry:
            self._load_file_registry(collection_name)
            
        index = self.indexes[collection_name]
        return {
            "name": collection_name,
            "vector_count": index.ntotal,
            "dimension": index.d,
            "index_type": type(index).__name__,
            "file_count": len(self.file_registry[collection_name])
        }
    
    def add_vectors(self, collection_name: str, vectors: np.ndarray, metadata: List[Dict[str, Any]], file_path: str = None) -> Dict[str, Any]:
        """
        将向量添加到集合中
        
        Args:
            collection_name: 集合名称
            vectors: 向量数组
            metadata: 元数据列表
            file_path: 文件路径（可选）
            
        Returns:
            Dict: 添加结果信息
        """
        try:
            # 确保集合存在
            if not self.collection_exists(collection_name):
                self._ensure_collection_exists(collection_name)
                logger.info(f"集合 {collection_name} 不存在，已创建新集合")
            
            # 确保索引和元数据已加载
            if collection_name not in self.indexes:
                load_success = self._load_index(collection_name)
                if not load_success:
                    return {"status": "error", "message": f"无法加载集合 {collection_name} 的索引"}
            
            if collection_name not in self.metadata:
                load_success = self._load_metadata(collection_name)
                if not load_success:
                    return {"status": "error", "message": f"无法加载集合 {collection_name} 的元数据"}
            
            if collection_name not in self.file_registry:
                load_success = self._load_file_registry(collection_name)
                if not load_success:
                    return {"status": "error", "message": f"无法加载集合 {collection_name} 的文件注册表"}
            
            # 获取已加载的对象
            index = self.indexes[collection_name]
            collection_metadata = self.metadata[collection_name]
            print("collection_metadata", collection_metadata)
            
            # 检查元数据条目数量是否与向量数量匹配
            if len(metadata) != len(vectors):
                logger.error(f"元数据条目数量 ({len(metadata)}) 与向量数量 ({len(vectors)}) 不匹配")
                return {"status": "error", "message": "元数据条目数量与向量数量不匹配"}
            
            # 如果是空索引，直接添加所有向量
            if index.ntotal == 0:
                logger.info(f"索引为空，直接添加所有 {len(vectors)} 个向量到集合 {collection_name}")
                try:
                    # 复制向量以防止修改原始数据
                    vectors_to_add = np.array(vectors)
                    
                    # 记录添加前的计数，应该为0
                    before_count = index.ntotal
                    
                    # 添加向量到索引
                    index.add(vectors_to_add)
                    
                    # 验证索引更新
                    after_count = index.ntotal
                    added_count = after_count - before_count
                    
                    if added_count != len(vectors_to_add):
                        logger.warning(f"添加的向量数量不匹配: 期望添加 {len(vectors_to_add)} 个，实际添加 {added_count} 个")
                    
                    # 更新元数据
                    if isinstance(collection_metadata, list):
                        # 如果元数据是列表，直接扩展
                        collection_metadata.extend(metadata)
                    elif isinstance(collection_metadata, dict):
                        # 如果元数据是字典，使用索引作为键
                        for i in range(added_count):
                            if i < len(metadata):
                                collection_metadata[str(before_count + i)] = metadata[i]
                    
                    # 如果提供了文件路径，更新文件注册表
                    if file_path:
                        if collection_name not in self.file_registry:
                            self.file_registry[collection_name] = {
                                "_created_at": datetime.now().isoformat(),
                                "_last_updated": datetime.now().isoformat(),
                                "_file_count": 0,
                                "_vector_count": 0
                            }
                        
                        file_name = os.path.basename(file_path)
                        if file_name not in self.file_registry[collection_name]:
                            # 创建完整的文件记录结构
                            self.file_registry[collection_name][file_name] = {
                                "file_name": file_name,  # 明确存储文件名
                                "file_path": file_path,  # 存储完整路径
                                "added_at": datetime.now().isoformat(),
                                "vector_count": added_count,
                                "last_updated": datetime.now().isoformat(),
                                "versions": [
                                    {
                                        "version": 1,
                                        "vector_count": added_count,
                                        "vector_ids": list(range(before_count, before_count + added_count)),
                                        "created_at": datetime.now().isoformat()
                                    }
                                ],
                                "current_version": 1
                            }
                            
                            # 更新元数据信息，确保每个向量都有文件信息
                            for i, meta in enumerate(metadata):
                                vector_idx = before_count + i
                                if isinstance(collection_metadata, dict):
                                    if str(vector_idx) in collection_metadata:
                                        if "metadata" not in collection_metadata[str(vector_idx)]:
                                            collection_metadata[str(vector_idx)]["metadata"] = {}
                                        collection_metadata[str(vector_idx)]["metadata"]["file_name"] = file_name
                                        collection_metadata[str(vector_idx)]["metadata"]["file_path"] = file_path
                                elif isinstance(collection_metadata, list) and vector_idx < len(collection_metadata):
                                    if "metadata" not in collection_metadata[vector_idx]:
                                        collection_metadata[vector_idx]["metadata"] = {}
                                    collection_metadata[vector_idx]["metadata"]["file_name"] = file_name
                                    collection_metadata[vector_idx]["metadata"]["file_path"] = file_path
                            
                            logger.info(f"文件注册表: 添加新文件 {file_name} 记录，包含 {added_count} 个向量")
                        else:
                            # 更新现有文件记录
                            current_file = self.file_registry[collection_name][file_name]
                            
                            # 确保文件名和路径字段存在
                            if "file_name" not in current_file:
                                current_file["file_name"] = file_name
                            if "file_path" not in current_file:
                                current_file["file_path"] = file_path
                                
                            # 确保vector_count字段存在
                            if "vector_count" not in current_file:
                                current_file["vector_count"] = 0
                                
                            current_file["vector_count"] += added_count
                            current_file["last_updated"] = datetime.now().isoformat()
                            
                            # 确保versions字段存在
                            if "versions" not in current_file:
                                current_file["versions"] = []
                                
                            # 创建新版本
                            next_version = 1
                            if current_file["versions"]:
                                next_version = max([v.get("version", 0) for v in current_file["versions"]]) + 1
                                
                            new_version = {
                                "version": next_version,
                                "vector_count": added_count,
                                "vector_ids": list(range(before_count, before_count + added_count)),
                                "created_at": datetime.now().isoformat()
                            }
                            
                            current_file["versions"].append(new_version)
                            current_file["current_version"] = next_version
                            logger.info(f"文件注册表: 更新文件 {file_name} 记录，添加版本 {next_version}，包含 {added_count} 个新向量")
                    
                    # 保存更新后的数据
                    logger.info(f"开始保存索引、元数据和文件注册表...")
                    index_saved = self._save_index(collection_name)
                    metadata_saved = self._save_metadata(collection_name)
                    registry_saved = self._save_file_registry(collection_name)
                    
                    # 检查所有组件是否成功保存
                    if not index_saved:
                        logger.error(f"索引保存失败，索引包含 {index.ntotal} 个向量")
                    if not metadata_saved:
                        logger.error(f"元数据保存失败，包含 {len(collection_metadata)} 个条目")
                    if not registry_saved:
                        logger.error(f"文件注册表保存失败: {self.file_registry.get(collection_name, {})}")
                    
                    if not (index_saved and metadata_saved and registry_saved):
                        logger.error(f"添加向量时保存失败: 索引={index_saved}, 元数据={metadata_saved}, 文件注册表={registry_saved}")
                        return {"status": "error", "message": "向量添加成功但保存数据失败"}
                    
                    logger.info(f"成功添加 {added_count} 个向量到空索引 {collection_name}")
                    return {"status": "success", "message": f"添加了 {added_count} 个向量到集合 {collection_name}", "count": added_count}
                except Exception as e:
                    logger.error(f"向空索引添加向量时发生错误: {str(e)}")
                    logger.error(traceback.format_exc())
                    return {"status": "error", "message": f"添加向量时发生错误: {str(e)}"}
            
            # 对于非空索引，首先检查重复
            accepted_vectors = []
            accepted_metadata = []
            duplicates_count = 0
            
            for i, (vector, meta) in enumerate(zip(vectors, metadata)):
                # 搜索最相似的向量
                D, I = index.search(np.array([vector]), 1)
                
                # 检查是否有匹配结果以及距离是否小于阈值
                if I[0][0] != -1 and D[0][0] < 0.01:
                    duplicates_count += 1
                    existing_idx = I[0][0]
                    
                    if isinstance(collection_metadata, list) and 0 <= existing_idx < len(collection_metadata):
                        existing_meta = collection_metadata[existing_idx]
                    elif isinstance(collection_metadata, dict) and str(existing_idx) in collection_metadata:
                        existing_meta = collection_metadata[str(existing_idx)]
                    else:
                        existing_meta = {"text": "未知文档"}
                    
                    logger.info(f"发现重复向量: 距离={D[0][0]}, 索引={I[0][0]}, 现有文本: {existing_meta.get('text', '')[:50]}...")
                else:
                    logger.info(f"接受新向量 #{i}: 距离={D[0][0] if I[0][0] != -1 else 'N/A'}, 原因: {'距离 > 阈值(0.01)' if I[0][0] != -1 else '没有找到匹配项'}")
                    accepted_vectors.append(vector)
                    accepted_metadata.append(meta)
            
            # 如果有向量被接受，则添加它们
            if accepted_vectors:
                try:
                    # 将接受的向量转换为NumPy数组
                    vectors_to_add = np.array(accepted_vectors)
                    
                    # 添加向量到索引
                    before_count = index.ntotal
                    index.add(vectors_to_add)
                    after_count = index.ntotal
                    added_count = after_count - before_count
                    
                    if added_count != len(vectors_to_add):
                        logger.warning(f"添加的向量数量不匹配: 期望添加 {len(vectors_to_add)} 个，实际添加 {added_count} 个")
                    
                    # 更新元数据
                    if isinstance(collection_metadata, list):
                        # 如果元数据是列表，直接扩展
                        collection_metadata.extend(accepted_metadata)
                    elif isinstance(collection_metadata, dict):
                        # 如果元数据是字典，使用索引作为键
                        for i in range(added_count):
                            if i < len(accepted_metadata):
                                collection_metadata[str(before_count + i)] = accepted_metadata[i]
                    
                    # 如果提供了文件路径，更新文件注册表
                    if file_path:
                        if collection_name not in self.file_registry:
                            self.file_registry[collection_name] = {
                                "_created_at": datetime.now().isoformat(),
                                "_last_updated": datetime.now().isoformat(),
                                "_file_count": 0,
                                "_vector_count": 0
                            }
                        
                        file_name = os.path.basename(file_path)
                        if file_name not in self.file_registry[collection_name]:
                            # 创建完整的文件记录结构
                            self.file_registry[collection_name][file_name] = {
                                "file_name": file_name,  # 明确存储文件名
                                "file_path": file_path,  # 存储完整路径
                                "added_at": datetime.now().isoformat(),
                                "vector_count": added_count,
                                "last_updated": datetime.now().isoformat(),
                                "versions": [
                                    {
                                        "version": 1,
                                        "vector_count": added_count,
                                        "vector_ids": list(range(before_count, before_count + added_count)),
                                        "created_at": datetime.now().isoformat()
                                    }
                                ],
                                "current_version": 1
                            }
                            
                            # 更新元数据信息，确保每个向量都有文件信息
                            for i, meta in enumerate(metadata):
                                vector_idx = before_count + i
                                if isinstance(collection_metadata, dict):
                                    if str(vector_idx) in collection_metadata:
                                        if "metadata" not in collection_metadata[str(vector_idx)]:
                                            collection_metadata[str(vector_idx)]["metadata"] = {}
                                        collection_metadata[str(vector_idx)]["metadata"]["file_name"] = file_name
                                        collection_metadata[str(vector_idx)]["metadata"]["file_path"] = file_path
                                elif isinstance(collection_metadata, list) and vector_idx < len(collection_metadata):
                                    if "metadata" not in collection_metadata[vector_idx]:
                                        collection_metadata[vector_idx]["metadata"] = {}
                                    collection_metadata[vector_idx]["metadata"]["file_name"] = file_name
                                    collection_metadata[vector_idx]["metadata"]["file_path"] = file_path
                            
                            logger.info(f"文件注册表: 添加新文件 {file_name} 记录，包含 {added_count} 个向量")
                        else:
                            # 更新现有文件记录
                            current_file = self.file_registry[collection_name][file_name]
                            
                            # 确保文件名和路径字段存在
                            if "file_name" not in current_file:
                                current_file["file_name"] = file_name
                            if "file_path" not in current_file:
                                current_file["file_path"] = file_path
                                
                            # 确保vector_count字段存在
                            if "vector_count" not in current_file:
                                current_file["vector_count"] = 0
                                
                            current_file["vector_count"] += added_count
                            current_file["last_updated"] = datetime.now().isoformat()
                            
                            # 确保versions字段存在
                            if "versions" not in current_file:
                                current_file["versions"] = []
                                
                            # 创建新版本
                            next_version = 1
                            if current_file["versions"]:
                                next_version = max([v.get("version", 0) for v in current_file["versions"]]) + 1
                                
                            new_version = {
                                "version": next_version,
                                "vector_count": added_count,
                                "vector_ids": list(range(before_count, before_count + added_count)),
                                "created_at": datetime.now().isoformat()
                            }
                            
                            current_file["versions"].append(new_version)
                            current_file["current_version"] = next_version
                            logger.info(f"文件注册表: 更新文件 {file_name} 记录，添加版本 {next_version}，包含 {added_count} 个新向量")
                    
                    # 保存更新后的数据
                    logger.info(f"开始保存索引、元数据和文件注册表...")
                    index_saved = self._save_index(collection_name)
                    metadata_saved = self._save_metadata(collection_name)
                    registry_saved = self._save_file_registry(collection_name)
                    
                    # 检查所有组件是否成功保存
                    if not index_saved:
                        logger.error(f"索引保存失败，索引包含 {after_count} 个向量")
                    if not metadata_saved:
                        logger.error(f"元数据保存失败，包含 {len(collection_metadata)} 个条目")
                    if not registry_saved:
                        logger.error(f"文件注册表保存失败: {self.file_registry.get(collection_name, {})}")
                    
                    if not (index_saved and metadata_saved and registry_saved):
                        logger.error(f"添加向量时保存失败: 索引={index_saved}, 元数据={metadata_saved}, 文件注册表={registry_saved}")
                        return {"status": "error", "message": "向量添加成功但保存数据失败"}
                    
                    logger.info(f"成功添加 {added_count} 个向量到索引 {collection_name}, 拒绝了 {duplicates_count} 个重复向量")
                    return {
                        "status": "success", 
                        "message": f"添加了 {added_count} 个向量到集合 {collection_name}, 跳过了 {duplicates_count} 个重复向量", 
                        "count": added_count, 
                        "duplicates": duplicates_count
                    }
                except Exception as e:
                    logger.error(f"添加向量时发生错误: {str(e)}")
                    logger.error(traceback.format_exc())
                    return {"status": "error", "message": f"添加向量时发生错误: {str(e)}"}
            else:
                logger.info(f"所有 {len(vectors)} 个向量都被视为重复，没有添加任何向量到索引 {collection_name}")
                return {
                    "status": "success", 
                    "message": f"所有 {len(vectors)} 个向量都是重复的，没有添加任何新向量", 
                    "count": 0, 
                    "duplicates": duplicates_count
                }
        
        except Exception as e:
            logger.error(f"添加向量到集合 {collection_name} 时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return {"status": "error", "message": f"添加向量失败: {str(e)}"}
    
    def search(self, collection_name: str, query_vector: np.ndarray, top_k: int = 5) -> Tuple[List[int], List[float], List[Dict]]:
        """
        搜索与查询向量最相似的文档
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回的最相似文档数量
            
        Returns:
            Tuple: (索引列表, 相似度列表, 元数据列表)
        """
        if collection_name not in self.indexes:
            self._load_index(collection_name)
        if collection_name not in self.metadata:
            self._load_metadata(collection_name)
        
        if collection_name not in self.indexes:
            logger.error(f"搜索失败: 无法加载索引 {collection_name}")
            return [], [], []
        
        if collection_name not in self.metadata:
            logger.error(f"搜索失败: 无法加载元数据 {collection_name}")
            return [], [], []
        
        consistency_check = self.check_and_fix_collection_consistency(collection_name)
        if not consistency_check:
            logger.warning(f"集合 {collection_name} 可能存在一致性问题，搜索结果可能不完整")
        
        try:
            logger.info(f"搜索集合：{collection_name}，当前索引总数：{self.indexes[collection_name].ntotal}，请求top_k：{top_k}")
            
            if self.indexes[collection_name].ntotal == 0:
                logger.warning(f"集合 {collection_name} 是空的，没有可搜索的向量")
                
                if collection_name in self.file_registry and self.file_registry[collection_name]:
                    registry_items = sum(1 for k in self.file_registry[collection_name] if not k.startswith('_'))
                    logger.warning(f"文件注册表存在并包含 {registry_items} 个文件，但索引为空")
                    for fname, finfo in self.file_registry[collection_name].items():
                        if not fname.startswith('_'):  # 跳过内部字段
                            logger.warning(f"文件 {fname} 信息: {finfo}")
                
                if collection_name in self.metadata and self.metadata[collection_name]:
                    if isinstance(self.metadata[collection_name], dict):
                        logger.warning(f"元数据存在并包含 {len(self.metadata[collection_name])} 个条目，但索引为空")
                    elif isinstance(self.metadata[collection_name], list):
                        logger.warning(f"元数据存在并包含 {len(self.metadata[collection_name])} 个条目，但索引为空")
                
                return [], [], []
            
            # 确保向量格式正确
            query_vector = np.array(query_vector).astype('float32').reshape(1, -1)
            
            # 检查向量维度
            expected_dim = self.indexes[collection_name].d
            actual_dim = query_vector.shape[1]
            
            # 记录向量维度信息
            logger.info(f"查询向量维度: {actual_dim}, 索引期望维度: {expected_dim}")
            
            if expected_dim != actual_dim:
                logger.error(f"查询向量维度错误: 期望{expected_dim}维，但提供{actual_dim}维")
                return [], [], []
            
            # 执行搜索
            D, I = self.indexes[collection_name].search(query_vector, min(top_k, self.indexes[collection_name].ntotal))
            
            # 展平结果
            indices = I[0].tolist()
            similarities = D[0].tolist()
            
            # 输出详细日志用于诊断
            logger.info(f"在索引{collection_name}中搜索返回的原始索引: {indices}")
            logger.info(f"原始相似度分数: {similarities}")
            
            # 检查无效索引(-1表示没有找到匹配)
            valid_pairs = []
            for idx, sim in zip(indices, similarities):
                if idx != -1:
                    valid_pairs.append((idx, sim))
                else:
                    logger.warning("搜索返回了-1索引，这表示没有找到足够的匹配项")
                
            if not valid_pairs:
                logger.warning("没有找到有效的匹配项")
                return [], [], []
            
            # 重建结果列表，只包含有效索引
            indices = [idx for idx, _ in valid_pairs]
            similarities = [sim for _, sim in valid_pairs]
            
            # 获取元数据
            metadata_list = []
            metadata = self.metadata[collection_name]
            
            # 添加元数据诊断信息
            logger.info(f"元数据类型: {type(metadata)}")
            if isinstance(metadata, dict):
                logger.info(f"元数据包含 {len(metadata)} 个条目")
            elif isinstance(metadata, list):
                logger.info(f"元数据包含 {len(metadata)} 个条目")
            
            for idx in indices:
                # 处理字典和列表类型的元数据
                if isinstance(metadata, dict):
                    # 尝试使用字符串和整数键
                    meta = metadata.get(str(idx)) or metadata.get(idx, {})
                elif isinstance(metadata, list) and 0 <= idx < len(metadata):
                    meta = metadata[idx]
                else:
                    logger.error(f"元数据格式错误，无法获取索引 {idx} 的元数据")
                    meta = {}
                
                if not meta:
                    logger.warning(f"索引 {idx} 没有对应的元数据")
                
                metadata_list.append(meta)
            
            # 标准化相似度为0-1范围
            # 注意：FAISS返回的是L2距离，需要转换为相似度
            # 距离越小，相似度越高，使用负指数转换
            similarities = [float(np.exp(-sim)) for sim in similarities]
            
            return indices, similarities, metadata_list
            
        except Exception as e:
            logger.error(f"搜索集合 {collection_name} 时出错: {str(e)}")
            logger.exception(e)
            return [], [], []
            
    def _match_filter_condition(self, metadata: Dict, filter_condition: Dict) -> bool:
        """
        检查元数据是否符合筛选条件
        
        Args:
            metadata: 元数据字典
            filter_condition: 筛选条件字典
            
        Returns:
            bool: 是否符合筛选条件
        """
        try:
            for key, value in filter_condition.items():
                # 处理嵌套字段，如 "file.type"
                if "." in key:
                    parts = key.split(".")
                    current = metadata
                    for part in parts[:-1]:
                        if part not in current:
                            return False
                        current = current[part]
                    if parts[-1] not in current or current[parts[-1]] != value:
                        return False
                # 处理简单字段
                elif key not in metadata or metadata[key] != value:
                    return False
            return True
        except Exception as e:
            logger.error(f"应用筛选条件时出错: {str(e)}")
            return False
    
    def delete_vectors(self, collection_name: str, ids: List[int]) -> bool:
        """
        从集合中删除指定ID的向量
        
        Args:
            collection_name: 集合名称
            ids: 要删除的向量ID列表
            
        Returns:
            bool: 删除是否成功
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return False
            
        # 确保索引和元数据已加载
        if collection_name not in self.indexes:
            self._load_index(collection_name)
        if collection_name not in self.metadata:
            self._load_metadata(collection_name)
        if collection_name not in self.file_registry:
            self._load_file_registry(collection_name)
        if collection_name not in self.file_change_history:
            self._load_file_history(collection_name)
            
        try:
            # 注意：FAISS不直接支持删除操作，需要重建索引
            # 获取当前索引中的所有向量
            index = self.indexes[collection_name]
            total = index.ntotal
            
            if total == 0:
                logger.warning(f"集合 {collection_name} 为空，无需删除")
                return True
                
            # 创建一个新的索引
            new_index = faiss.IndexFlatL2(index.d)
            
            # 获取所有向量
            all_vectors = np.zeros((total, index.d), dtype='float32')
            for i in range(total):
                if i not in ids:  # 只保留不在删除列表中的向量
                    # 这里需要实现获取单个向量的逻辑，FAISS没有直接API
                    # 这是一个简化实现，实际应用中可能需要更复杂的处理
                    pass
            
            # 更新元数据
            new_metadata = {}
            for i in range(total):
                if i not in ids:
                    new_metadata[i] = self.metadata[collection_name].get(i, {})
            
            # 更新文件注册表中的向量ID引用
            for file_name, file_info in self.file_registry[collection_name].items():
                for version in file_info['versions']:
                    old_vector_count = version['vector_count']
                    version['vector_ids'] = [vid for vid in version['vector_ids'] if vid not in ids]
                    version['vector_count'] = len(version['vector_ids'])
                    
                    # 如果向量数量发生变化，记录文件变更事件
                    if old_vector_count != version['vector_count']:
                        self._record_file_event(collection_name, file_name, "vector_delete", {
                            "version": version['version'],
                            "deleted_count": old_vector_count - version['vector_count'],
                            "remaining_count": version['vector_count']
                        })
            
            # 更新索引和元数据
            self.indexes[collection_name] = new_index
            self.metadata[collection_name] = new_metadata
            
            # 保存索引、元数据和文件注册表
            self._save_index(collection_name)
            self._save_metadata(collection_name)
            self._save_file_registry(collection_name)
            
            # 记录向量删除事件
            self._record_collection_event(collection_name, "vector_delete", {
                "deleted_count": len(ids),
                "remaining_count": total - len(ids)
            })
            
            logger.info(f"成功从集合 {collection_name} 中删除 {len(ids)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"从集合 {collection_name} 中删除向量失败: {str(e)}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        删除整个集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 删除是否成功
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return False
            
        try:
            # 删除索引、元数据和文件注册表文件
            index_path = self._get_index_path(collection_name)
            metadata_path = self._get_metadata_path(collection_name)
            registry_path = self._get_file_registry_path(collection_name)
            history_path = self._get_file_history_path(collection_name)
            
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            if os.path.exists(registry_path):
                os.remove(registry_path)
            if os.path.exists(history_path):
                os.remove(history_path)
                
            # 从内存中移除
            if collection_name in self.indexes:
                del self.indexes[collection_name]
            if collection_name in self.metadata:
                del self.metadata[collection_name]
            if collection_name in self.file_registry:
                del self.file_registry[collection_name]
            if collection_name in self.file_change_history:
                del self.file_change_history[collection_name]
                
            logger.info(f"成功删除集合 {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除集合 {collection_name} 失败: {str(e)}")
            return False
    
    def list_files(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        获取集合中的所有文件信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            List[Dict]: 文件信息列表，每个文件包含file_name, file_path, chunks_count等字段
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return []
            
        # 确保文件注册表已加载
        if collection_name not in self.file_registry:
            logger.info(f"加载集合 {collection_name} 的文件注册表")
            success = self._load_file_registry(collection_name)
            if not success:
                logger.error(f"加载集合 {collection_name} 的文件注册表失败")
                return []
                
        try:
            logger.info(f"列出集合 {collection_name} 中的文件")
            files_info = []
            file_registry = self.file_registry.get(collection_name, {})
            
            # 过滤掉以下划线开头的元数据字段，只处理实际文件
            for file_name, file_info in file_registry.items():
                # 跳过元数据字段
                if file_name.startswith('_'):
                    continue
                    
                try:
                    # 确保file_info是一个字典类型
                    if not isinstance(file_info, dict):
                        logger.warning(f"文件 {file_name} 的信息不是字典类型: {type(file_info)}")
                        continue
                    
                    # 提取文件信息
                    file_data = {
                        'file_name': file_name,
                        'file_path': file_info.get('file_path', ''),
                    }
                    
                    # 添加时间信息（可能是字符串或日期对象）
                    added_at = file_info.get('added_at', '')
                    if added_at:
                        file_data['add_time'] = str(added_at)
                    
                    # 计算向量数量
                    if 'versions' in file_info and isinstance(file_info['versions'], list):
                        # 获取最新版本的向量数量
                        if file_info['versions']:
                            current_version = file_info.get('current_version')
                            if current_version is not None:
                                # 查找当前版本
                                version_info = next((v for v in file_info['versions'] if v.get('version') == current_version), None)
                                if version_info:
                                    file_data['chunks_count'] = version_info.get('vector_count', 0)
                                else:
                                    # 如果找不到当前版本，使用最后一个版本
                                    file_data['chunks_count'] = file_info['versions'][-1].get('vector_count', 0)
                            else:
                                # 如果没有current_version字段，使用最后一个版本
                                file_data['chunks_count'] = file_info['versions'][-1].get('vector_count', 0)
                        else:
                            file_data['chunks_count'] = 0
                    else:
                        file_data['chunks_count'] = 0
                    
                    # 尝试获取文件大小
                    if 'file_path' in file_info and os.path.exists(file_info['file_path']):
                        file_data['file_size'] = os.path.getsize(file_info['file_path'])
                    else:
                        file_data['file_size'] = 0
                        
                    files_info.append(file_data)
                    logger.debug(f"已添加文件信息: {file_data}")
                except Exception as e:
                    logger.error(f"处理文件 {file_name} 信息时出错: {str(e)}")
                    logger.exception(e)
            
            logger.info(f"找到 {len(files_info)} 个文件")
            return files_info
        except Exception as e:
            logger.error(f"获取文件列表时出错: {str(e)}")
            logger.exception(e)
            return []
    
    def get_file_info(self, collection_name: str, file_name: str) -> Dict[str, Any]:
        """
        获取集合中特定文件的详细信息
        
        Args:
            collection_name: 集合名称
            file_name: 文件名
            
        Returns:
            Dict: 文件详细信息
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return {'error': f"集合 {collection_name} 不存在"}
            
        # 确保文件注册表已加载
        if collection_name not in self.file_registry:
            success = self._load_file_registry(collection_name)
            if not success:
                logger.error(f"加载集合 {collection_name} 的文件注册表失败")
                return {'error': f"加载集合 {collection_name} 的文件注册表失败"}
            
        if file_name not in self.file_registry[collection_name]:
            return {'error': f"文件 {file_name} 在集合 {collection_name} 中不存在"}
            
        return self.file_registry[collection_name][file_name]
    
    def get_file_change_history(self, collection_name: str, file_name: str = None) -> List[Dict[str, Any]]:
        """
        获取文件变更历史记录
        
        Args:
            collection_name: 集合名称
            file_name: 文件名，如果为None则返回集合的所有文件变更历史
            
        Returns:
            List[Dict]: 文件变更历史记录列表
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return []
            
        # 确保文件变更历史记录已加载
        if collection_name not in self.file_change_history:
            self._load_file_history(collection_name)
            
        if file_name:
            # 返回特定文件的变更历史
            return [event for event in self.file_change_history[collection_name] 
                   if 'file_name' in event and event['file_name'] == file_name]
        else:
            # 返回所有文件变更历史
            return self.file_change_history[collection_name]
    
    def replace_file(self, collection_name: str, file_path: str, vectors: np.ndarray, metadata: List[Dict]) -> bool:
        """
        替换集合中的文件（创建新版本）
        
        Args:
            collection_name: 集合名称
            file_path: 文件路径
            vectors: 新的向量数组
            metadata: 新的元数据列表
            
        Returns:
            bool: 替换是否成功
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return False
            
        # 确保索引、元数据和文件注册表已加载
        if collection_name not in self.indexes:
            self._load_index(collection_name)
        if collection_name not in self.metadata:
            self._load_metadata(collection_name)
        if collection_name not in self.file_registry:
            self._load_file_registry(collection_name)
            
        file_name = os.path.basename(file_path)
        
        try:
            # 如果文件已存在，先删除旧版本的向量
            if file_name in self.file_registry[collection_name]:
                file_info = self.file_registry[collection_name][file_name]
                current_version = file_info['current_version']
                current_version_info = next((v for v in file_info['versions'] if v['version'] == current_version), None)
                
                if current_version_info:
                    # 删除当前版本的向量
                    self.delete_vectors(collection_name, current_version_info['vector_ids'])
            
            # 添加新版本的向量
            success = self.add_vectors(collection_name, vectors, metadata, file_path)
            
            if success:
                logger.info(f"成功替换文件 {file_name} 在集合 {collection_name} 中的内容")
            return success
            
        except Exception as e:
            logger.error(f"替换文件 {file_name} 在集合 {collection_name} 中的内容失败: {str(e)}")
            return False
    
    def delete_file(self, collection_name: str, file_name: str) -> bool:
        """
        从集合中删除指定文件
        
        Args:
            collection_name: 集合名称
            file_name: 文件名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not self._ensure_collection_exists(collection_name):
                return False
                
            # 加载索引和元数据（如果还没有加载）
            if collection_name not in self.indexes:
                self._load_index(collection_name)
            if collection_name not in self.metadata:
                self._load_metadata(collection_name)
            if collection_name not in self.file_registry:
                self._load_file_registry(collection_name)
                
            # 获取文件注册表
            file_registry = self.file_registry.get(collection_name, {})
            
            # 检查文件是否存在
            if file_name not in file_registry:
                logger.warning(f"文件 {file_name} 不存在于集合 {collection_name} 中")
                return False
                
            # 获取文件信息，以便记录删除事件
            file_info = file_registry[file_name]
            
            # 删除与该文件关联的向量
            vector_ids = file_info.get("vector_ids", [])
            if vector_ids:
                logger.info(f"从集合 {collection_name} 中删除与文件 {file_name} 关联的 {len(vector_ids)} 个向量")
                self.delete_vectors(collection_name, vector_ids)
            
            # 从文件注册表中删除文件
            del file_registry[file_name]
            
            # 保存更新后的文件注册表
            self._save_file_registry(collection_name)
            
            # 记录文件删除事件
            event_data = {
                "file_name": file_name,
                "timestamp": datetime.now().isoformat(),
                "action": "delete",
                "vector_count": len(vector_ids) if vector_ids else 0
            }
            self._record_file_event(collection_name, file_name, "delete", event_data)
            
            # 更新集合统计信息
            self._update_collection_stats(collection_name)
            
            logger.info(f"文件 {file_name} 已从集合 {collection_name} 中删除")
            return True
        except Exception as e:
            logger.error(f"删除文件 {file_name} 时出错: {str(e)}")
            logger.exception(e)
            return False
    
    def update_file_metadata(self, collection_name: str, file_name: str, metadata_update: Dict[str, Any]) -> bool:
        """
        更新文件的元数据信息，包括重要性系数等
        
        Args:
            collection_name: 集合名称
            file_name: 文件名
            metadata_update: 要更新的元数据字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not self._ensure_collection_exists(collection_name):
                return False
                
            # 加载文件注册表（如果还没有加载）
            if collection_name not in self.file_registry:
                self._load_file_registry(collection_name)
                
            # 获取文件注册表
            file_registry = self.file_registry.get(collection_name, {})
            
            # 检查文件是否存在
            if file_name not in file_registry:
                logger.warning(f"文件 {file_name} 不存在于集合 {collection_name} 中")
                return False
            
            # 更新文件元数据
            updated = False
            for key, value in metadata_update.items():
                if key not in file_registry[file_name] or file_registry[file_name][key] != value:
                    file_registry[file_name][key] = value
                    updated = True
            
            if not updated:
                logger.info(f"文件 {file_name} 的元数据无变化，不需要更新")
                return True
                
            # 保存更新后的文件注册表
            self._save_file_registry(collection_name)
            
            # 记录元数据更新事件
            event_data = {
                "file_name": file_name,
                "timestamp": datetime.now().isoformat(),
                "action": "update_metadata",
                "metadata_changes": metadata_update
            }
            self._record_file_event(collection_name, file_name, "update_metadata", event_data)
            
            logger.info(f"文件 {file_name} 的元数据已更新")
            return True
        except Exception as e:
            logger.error(f"更新文件 {file_name} 的元数据时出错: {str(e)}")
            logger.exception(e)
            return False
    
    def restore_file_version(self, collection_name: str, file_name: str, version: int) -> bool:
        """
        恢复文件的特定版本
        
        Args:
            collection_name: 集合名称
            file_name: 文件名
            version: 要恢复的版本号
            
        Returns:
            bool: 恢复是否成功
        """
        if not self.collection_exists(collection_name):
            logger.error(f"集合 {collection_name} 不存在")
            return False
            
        # 确保文件注册表已加载
        if collection_name not in self.file_registry:
            self._load_file_registry(collection_name)
            
        if file_name not in self.file_registry[collection_name]:
            logger.error(f"文件 {file_name} 在集合 {collection_name} 中不存在")
            return False
            
        file_info = self.file_registry[collection_name][file_name]
        
        # 检查版本是否存在
        version_info = next((v for v in file_info['versions'] if v['version'] == version), None)
        if not version_info:
            logger.error(f"文件 {file_name} 的版本 {version} 不存在")
            return False
            
        # 如果已经是当前版本，无需操作
        if file_info['current_version'] == version:
            logger.info(f"文件 {file_name} 已经是版本 {version}")
            return True
            
        try:
            # 更新当前版本
            file_info['current_version'] = version
            self._save_file_registry(collection_name)
            
            logger.info(f"成功将文件 {file_name} 恢复到版本 {version}")
            return True
            
        except Exception as e:
            logger.error(f"恢复文件 {file_name} 到版本 {version} 失败: {str(e)}")
            return False

    def _save_collection_info(self, collection_name: str, dimension: int, index_type: str) -> bool:
        """
        保存集合信息
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            index_type: 索引类型
            
        Returns:
            bool: 保存是否成功
        """
        collections_info_path = self._get_collection_info_path()
        
        # 读取现有集合信息
        collections_info = {}
        if os.path.exists(collections_info_path):
            try:
                with open(collections_info_path, 'r', encoding='utf-8') as f:
                    collections_info = json.load(f)
            except Exception as e:
                logger.error(f"读取集合信息文件失败: {str(e)}")
                collections_info = {}
        
        # 更新集合信息
        # 注意：在集合信息中使用原始名称，但对应的文件使用编码后的名称
        collections_info[collection_name] = {
            "name": collection_name,
            "dimension": dimension,
            "index_type": index_type,
            "created_at": datetime.now().isoformat(),
            "vectors_count": 0,
            "files_count": 0
        }
        
        # 保存集合信息
        try:
            with open(collections_info_path, 'w', encoding='utf-8') as f:
                json.dump(collections_info, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存集合信息失败: {str(e)}")
            return False

    def _update_collection_stats(self, collection_name: str, vectors_count: int = None, files_count: int = None) -> bool:
        """
        更新集合统计信息
        
        Args:
            collection_name: 集合名称
            vectors_count: 向量数量
            files_count: 文件数量
            
        Returns:
            bool: 更新是否成功
        """
        collections_info_path = self._get_collection_info_path()
        
        # 读取现有集合信息
        if os.path.exists(collections_info_path):
            try:
                with open(collections_info_path, 'r', encoding='utf-8') as f:
                    collections_info = json.load(f)
            except Exception as e:
                logger.error(f"读取集合信息文件失败: {str(e)}")
                return False
            
            # 更新集合统计信息
            if collection_name in collections_info:
                if vectors_count is not None:
                    collections_info[collection_name]["vectors_count"] = vectors_count
                if files_count is not None:
                    collections_info[collection_name]["files_count"] = files_count
                
                # 保存更新后的集合信息
                try:
                    with open(collections_info_path, 'w', encoding='utf-8') as f:
                        json.dump(collections_info, f, ensure_ascii=False, indent=2)
                    return True
                except Exception as e:
                    logger.error(f"保存更新后的集合信息失败: {str(e)}")
                    return False
        
        return False

    def _train_index(self, index, dimension: int, n_samples: int = 1000) -> bool:
        """
        训练FAISS索引，用于IVF等需要训练的索引类型
        
        Args:
            index: FAISS索引对象
            dimension: 向量维度
            n_samples: 训练样本数量
            
        Returns:
            bool: 训练是否成功
        """
        try:
            # 生成随机训练数据
            np.random.seed(42)  # 设置随机种子确保可重复性
            training_data = np.random.random((n_samples, dimension)).astype('float32')
            
            # 训练索引
            logger.info(f"训练索引，样本数量: {n_samples}")
            index.train(training_data)
            return True
        except Exception as e:
            logger.error(f"训练索引失败: {str(e)}")
            return False

    def load_collection(self, collection_name: str) -> bool:
        """
        加载已有的向量集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 加载是否成功
        """
        try:
            index_path = self._get_index_path(collection_name)
            metadata_path = self._get_metadata_path(collection_name)
            file_registry_path = self._get_file_registry_path(collection_name)
            file_history_path = self._get_file_history_path(collection_name)
            
            # 检查文件是否存在
            if not os.path.exists(index_path):
                logger.error(f"集合 {collection_name} 的索引文件不存在")
                return False
            
            # 加载索引
            try:
                logger.info(f"加载索引文件: {index_path}")
                index = faiss.read_index(index_path)
                self.indexes[collection_name] = index
            except Exception as e:
                logger.error(f"加载索引 {collection_name} 失败: {str(e)}")
                return False
            
            # 加载元数据
            try:
                logger.info(f"加载元数据文件: {metadata_path}")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        self.metadata[collection_name] = json.load(f)
                else:
                    logger.warning(f"元数据文件不存在，创建空元数据")
                    self.metadata[collection_name] = []
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
            except Exception as e:
                logger.error(f"加载元数据失败: {str(e)}")
                # 移除已加载的索引
                if collection_name in self.indexes:
                    del self.indexes[collection_name]
                return False
            
            # 加载文件注册表
            try:
                logger.info(f"加载文件注册表: {file_registry_path}")
                if os.path.exists(file_registry_path):
                    with open(file_registry_path, 'r', encoding='utf-8') as f:
                        self.file_registry[collection_name] = json.load(f)
                else:
                    logger.warning(f"文件注册表不存在，创建空注册表")
                    self.file_registry[collection_name] = {}
                    with open(file_registry_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
            except Exception as e:
                logger.error(f"加载文件注册表失败: {str(e)}")
                # 移除已加载的数据
                if collection_name in self.indexes:
                    del self.indexes[collection_name]
                if collection_name in self.metadata:
                    del self.metadata[collection_name]
                return False
            
            # 加载文件变更历史
            try:
                logger.info(f"加载文件变更历史: {file_history_path}")
                if os.path.exists(file_history_path):
                    with open(file_history_path, 'r', encoding='utf-8') as f:
                        self.file_change_history[collection_name] = json.load(f)
                else:
                    logger.warning(f"文件变更历史不存在，创建空历史记录")
                    self.file_change_history[collection_name] = []
                    with open(file_history_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
            except Exception as e:
                logger.error(f"加载文件变更历史失败: {str(e)}")
                # 移除已加载的数据
                if collection_name in self.indexes:
                    del self.indexes[collection_name]
                if collection_name in self.metadata:
                    del self.metadata[collection_name]
                if collection_name in self.file_registry:
                    del self.file_registry[collection_name]
                return False
            
            # 更新集合统计信息
            vectors_count = len(self.metadata[collection_name]) if collection_name in self.metadata else 0
            files_count = len(self.file_registry[collection_name]) if collection_name in self.file_registry else 0
            self._update_collection_stats(collection_name, vectors_count, files_count)
            
            logger.info(f"集合 {collection_name} 加载成功，包含 {vectors_count} 个向量，{files_count} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"加载集合 {collection_name} 时出错: {str(e)}")
            traceback.print_exc()
            return False

    def repair_collection_files(self) -> Dict[str, Dict[str, bool]]:
        """
        修复所有集合的文件格式问题，将pickle格式转换为JSON格式
        
        Returns:
            Dict: 修复结果报告
        """
        import pickle
        import glob
        import os
        
        logger.info("开始修复集合文件格式...")
        results = {}
        
        # 获取所有索引文件
        index_files = glob.glob(os.path.join(self.index_folder, "*.index"))
        collection_names = [os.path.basename(f).replace('.index', '') for f in index_files]
        
        for name in collection_names:
            results[name] = {
                "metadata": False,
                "file_registry": False,
                "file_history": False
            }
            
            logger.info(f"修复集合: {name}")
            
            # 修复元数据
            metadata_path = self._get_metadata_path(name)
            if os.path.exists(metadata_path):
                try:
                    # 尝试以pickle格式加载
                    with open(metadata_path, 'rb') as f:
                        try:
                            metadata = pickle.load(f)
                            # 以JSON格式保存
                            with open(metadata_path, 'w', encoding='utf-8') as jf:
                                json.dump(metadata, jf)
                            logger.info(f"成功将元数据从pickle转换为JSON: {metadata_path}")
                            results[name]["metadata"] = True
                        except Exception as e:
                            # 如果pickle加载失败，尝试JSON格式
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as jf:
                                    json.load(jf)
                                logger.info(f"元数据已经是JSON格式: {metadata_path}")
                                results[name]["metadata"] = True
                            except Exception as je:
                                logger.error(f"元数据文件无法修复: {str(je)}")
                except Exception as e:
                    logger.error(f"处理元数据时出错: {str(e)}")
            
            # 修复文件注册表
            registry_path = self._get_file_registry_path(name)
            if os.path.exists(registry_path):
                try:
                    # 尝试以pickle格式加载
                    with open(registry_path, 'rb') as f:
                        try:
                            registry = pickle.load(f)
                            # 以JSON格式保存
                            with open(registry_path, 'w', encoding='utf-8') as jf:
                                json.dump(registry, jf)
                            logger.info(f"成功将文件注册表从pickle转换为JSON: {registry_path}")
                            results[name]["file_registry"] = True
                        except Exception as e:
                            # 如果pickle加载失败，尝试JSON格式
                            try:
                                with open(registry_path, 'r', encoding='utf-8') as jf:
                                    json.load(jf)
                                logger.info(f"文件注册表已经是JSON格式: {registry_path}")
                                results[name]["file_registry"] = True
                            except Exception as je:
                                logger.error(f"文件注册表无法修复: {str(je)}")
                except Exception as e:
                    logger.error(f"处理文件注册表时出错: {str(e)}")
            
            # 修复文件历史
            history_path = self._get_file_history_path(name)
            if os.path.exists(history_path):
                try:
                    # 尝试以pickle格式加载
                    with open(history_path, 'rb') as f:
                        try:
                            history = pickle.load(f)
                            # 以JSON格式保存
                            with open(history_path, 'w', encoding='utf-8') as jf:
                                json.dump(history, jf)
                            logger.info(f"成功将文件历史从pickle转换为JSON: {history_path}")
                            results[name]["file_history"] = True
                        except Exception as e:
                            # 如果pickle加载失败，尝试JSON格式
                            try:
                                with open(history_path, 'r', encoding='utf-8') as jf:
                                    json.load(jf)
                                logger.info(f"文件历史已经是JSON格式: {history_path}")
                                results[name]["file_history"] = True
                            except Exception as je:
                                logger.error(f"文件历史无法修复: {str(je)}")
                except Exception as e:
                    logger.error(f"处理文件历史时出错: {str(e)}")
                    
        logger.info(f"集合文件修复完成: {results}")
        return results

    def synchronize_index_and_metadata(self, collection_name):
        """
        同步索引和元数据，确保它们一致
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 同步是否成功
        """
        if collection_name not in self.indexes:
            self._load_index(collection_name)
        if collection_name not in self.metadata:
            self._load_metadata(collection_name)
        
        if collection_name not in self.indexes:
            logger.error(f"同步失败: 无法加载索引 {collection_name}")
            return False
        
        if collection_name not in self.metadata:
            logger.error(f"同步失败: 无法加载元数据 {collection_name}")
            return False
        
        try:
            index = self.indexes[collection_name]
            metadata = self.metadata[collection_name]
            index_size = index.ntotal
            
            logger.info(f"开始同步 {collection_name}: 索引大小={index_size}, 元数据类型={type(metadata).__name__}")
            
            # 转换元数据格式为字典
            if isinstance(metadata, list):
                logger.info(f"将元数据从列表转换为字典")
                new_metadata = {}
                for i, meta in enumerate(metadata):
                    if i < index_size:
                        new_metadata[str(i)] = meta
                metadata = new_metadata
                self.metadata[collection_name] = metadata
            
            # 确保每个索引位置都有元数据
            if isinstance(metadata, dict):
                missing_keys = []
                for i in range(index_size):
                    str_key = str(i)
                    if str_key not in metadata and i not in metadata:
                        logger.warning(f"索引 {i} 缺少元数据，添加空记录")
                        metadata[str_key] = {"text": f"索引 {i} 的元数据缺失", "missing": True}
                        missing_keys.append(i)
            
            # 删除超出索引范围的元数据
            keys_to_remove = []
            for key in metadata.keys():
                try:
                    idx = int(key) if isinstance(key, str) else key
                    if idx >= index_size:
                        keys_to_remove.append(key)
                except ValueError:
                    continue
                    
            for key in keys_to_remove:
                logger.warning(f"删除超出索引范围的元数据: {key}")
                metadata.pop(key, None)
                
            logger.info(f"同步完成：添加了 {len(missing_keys)} 个缺失的元数据记录，删除了 {len(keys_to_remove)} 个超出范围的记录")
        
            # 保存更新后的元数据
            self._save_metadata(collection_name)
            
            return True
        except Exception as e:
            logger.error(f"同步索引和元数据时出错: {str(e)}")
            logger.exception(e)
            return False

    def diagnose_and_repair_kb(self, collection_name: str) -> Dict:
        """
        诊断知识库的索引和元数据，尝试发现并修复不一致问题
        
        Args:
            collection_name: 集合名称
            
        Returns:
            Dict: 诊断结果和修复报告
        """
        if not self.collection_exists(collection_name):
            return {"error": f"集合 {collection_name} 不存在"}
            
        # 加载索引、元数据和文件注册表
        if collection_name not in self.indexes:
            self._load_index(collection_name)
        if collection_name not in self.metadata:
            self._load_metadata(collection_name)
        if collection_name not in self.file_registry:
            self._load_file_registry(collection_name)
            
        result = {
            "index_loaded": collection_name in self.indexes,
            "metadata_loaded": collection_name in self.metadata,
            "file_registry_loaded": collection_name in self.file_registry,
            "repairs_made": [],
            "warnings": [],
            "errors": []
        }
        
        # 检查索引是否存在和加载成功
        if not result["index_loaded"]:
            result["errors"].append("索引未能成功加载")
            return result
            
        # 检查元数据是否存在和加载成功
        if not result["metadata_loaded"]:
            result["errors"].append("元数据未能成功加载")
            return result
            
        # 检查文件注册表是否存在和加载成功
        if not result["file_registry_loaded"]:
            result["errors"].append("文件注册表未能成功加载")
            return result
            
        # 获取索引信息
        index = self.indexes[collection_name]
        index_size = index.ntotal
        index_dim = index.d
        
        result["index_info"] = {
            "size": index_size,
            "dimension": index_dim
        }
        
        # 检查元数据格式和大小
        metadata = self.metadata[collection_name]
        if isinstance(metadata, dict):
            metadata_size = len(metadata)
            metadata_type = "dict"
        elif isinstance(metadata, list):
            metadata_size = len(metadata)
            metadata_type = "list"
        else:
            metadata_size = 0
            metadata_type = str(type(metadata))
            result["errors"].append(f"元数据类型异常: {metadata_type}")
            
        result["metadata_info"] = {
            "size": metadata_size,
            "type": metadata_type
        }
        
        # 检查文件注册表
        file_registry = self.file_registry[collection_name]
        file_count = len(file_registry)
        total_vectors_in_registry = 0
        vector_ids_in_registry = set()
        
        for file_name, file_info in file_registry.items():
            for version in file_info.get('versions', []):
                total_vectors_in_registry += version.get('vector_count', 0)
                vector_ids_in_registry.update(version.get('vector_ids', []))
                
        result["file_registry_info"] = {
            "file_count": file_count,
            "total_vectors": total_vectors_in_registry,
            "unique_vector_ids": len(vector_ids_in_registry)
        }
        
        # 检查索引和元数据大小不匹配的情况
        if index_size != metadata_size:
            result["warnings"].append(f"索引大小({index_size})与元数据大小({metadata_size})不匹配")
            
            # 尝试修复元数据
            if metadata_type == "dict" and index_size > metadata_size:
                # 添加缺失的元数据条目
                missing_ids = [i for i in range(index_size) if str(i) not in metadata]
                for i in missing_ids:
                    metadata[str(i)] = {"warning": "自动添加的空元数据"}
                result["repairs_made"].append(f"为缺失的 {len(missing_ids)} 个索引项添加了空元数据")
                
            elif metadata_type == "list" and index_size > metadata_size:
                # 扩展列表到匹配索引大小
                for i in range(metadata_size, index_size):
                    metadata.append({"warning": "自动添加的空元数据"})
                result["repairs_made"].append(f"将元数据列表扩展了 {index_size - metadata_size} 个条目")
                
        # 检查文件注册表中的向量ID是否有效
        max_valid_id = index_size - 1
        invalid_ids = [vid for vid in vector_ids_in_registry if vid > max_valid_id]
        
        if invalid_ids:
            result["warnings"].append(f"文件注册表中包含 {len(invalid_ids)} 个无效的向量ID")
            
            # 尝试修复文件注册表
            fixed_files = 0
            for file_name, file_info in file_registry.items():
                for version in file_info.get('versions', []):
                    old_count = version.get('vector_count', 0)
                    version['vector_ids'] = [vid for vid in version.get('vector_ids', []) if vid <= max_valid_id]
                    version['vector_count'] = len(version['vector_ids'])
                    
                    if old_count != version['vector_count']:
                        fixed_files += 1
                        
            if fixed_files > 0:
                result["repairs_made"].append(f"修复了 {fixed_files} 个文件版本的无效向量ID")
                
        # 如果进行了修复，保存更新后的数据
        if result["repairs_made"]:
            self._save_metadata(collection_name)
            self._save_file_registry(collection_name)
            result["saved"] = True
            
        return result

    def diagnose_knowledge_base(self, collection_name: str) -> Dict[str, Any]:
        """
        诊断知识库是否存在数据一致性问题
        
        Args:
            collection_name: 知识库名称
            
        Returns:
            Dict: 诊断结果
        """
        result = {
            "status": "unknown",
            "collection_exists": False,
            "index_exists": False,
            "metadata_exists": False,
            "file_registry_exists": False,
            "index_count": 0,
            "metadata_count": 0,
            "file_registry_count": 0,
            "is_consistent": False,
            "issues": [],
            "paths": {}
        }
        
        try:
            # 检查集合是否存在
            result["collection_exists"] = self.collection_exists(collection_name)
            if not result["collection_exists"]:
                result["status"] = "error"
                result["issues"].append(f"集合 {collection_name} 不存在")
                return result
            
            # 获取文件路径
            index_path = self._get_index_path(collection_name)
            metadata_path = self._get_metadata_path(collection_name)
            registry_path = self._get_file_registry_path(collection_name)
            
            result["paths"] = {
                "index_path": index_path,
                "metadata_path": metadata_path,
                "registry_path": registry_path
            }
            
            # 检查文件是否存在
            result["index_exists"] = os.path.exists(index_path) and os.path.getsize(index_path) > 0
            result["metadata_exists"] = os.path.exists(metadata_path) and os.path.getsize(metadata_path) > 0
            result["file_registry_exists"] = os.path.exists(registry_path) and os.path.getsize(registry_path) > 0
            
            # 加载索引和元数据
            index = None
            metadata = None
            file_registry = None
            
            try:
                index = self._load_index(collection_name)
                result["index_count"] = index.ntotal if index else 0
            except Exception as e:
                result["issues"].append(f"加载索引失败: {str(e)}")
            
            try:
                metadata = self._load_metadata(collection_name)
                result["metadata_count"] = len(metadata) if metadata else 0
            except Exception as e:
                result["issues"].append(f"加载元数据失败: {str(e)}")
            
            try:
                file_registry = self._load_file_registry(collection_name)
                result["file_registry_count"] = len(file_registry) if file_registry else 0
            except Exception as e:
                result["issues"].append(f"加载文件注册表失败: {str(e)}")
            
            # 检查一致性
            if index is not None and metadata is not None:
                if isinstance(metadata, list) and index.ntotal == len(metadata):
                    result["is_consistent"] = True
                elif isinstance(metadata, dict) and index.ntotal == len(metadata):
                    result["is_consistent"] = True
                else:
                    result["is_consistent"] = False
                    result["issues"].append(f"索引数量 ({index.ntotal}) 与元数据数量 ({len(metadata) if metadata else 0}) 不匹配")
            
            # 设置状态
            if result["issues"]:
                result["status"] = "warning"
            elif result["is_consistent"]:
                result["status"] = "ok"
            else:
                result["status"] = "error"
                result["issues"].append("数据一致性检查失败")
            
            # 添加修复建议
            if not result["is_consistent"]:
                result["repair_suggestion"] = "调用 repair_knowledge_base 方法修复数据一致性问题"
            
            return result
            
        except Exception as e:
            logger.error(f"诊断知识库 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            result["status"] = "error"
            result["issues"].append(f"诊断过程发生错误: {str(e)}")
            return result
            
    def repair_knowledge_base(self, collection_name: str) -> Dict[str, Any]:
        """
        修复知识库的数据一致性问题
        
        Args:
            collection_name: 知识库名称
            
        Returns:
            Dict: 修复结果
        """
        result = {
            "status": "unknown",
            "issues_found": [],
            "repairs_made": [],
            "success": False
        }
        
        try:
            # 首先进行诊断
            diagnosis = self.diagnose_knowledge_base(collection_name)
            
            if diagnosis["status"] == "ok" and diagnosis["is_consistent"]:
                result["status"] = "success"
                result["success"] = True
                result["message"] = "知识库数据一致性正常，不需要修复"
                return result
            
            # 记录发现的问题
            result["issues_found"] = diagnosis["issues"]
            
            # 加载所有可用的数据
            index = None
            metadata = None
            file_registry = None
            
            try:
                index = self._load_index(collection_name)
            except Exception:
                pass
                
            try:
                metadata = self._load_metadata(collection_name)
            except Exception:
                pass
                
            try:
                file_registry = self._load_file_registry(collection_name)
            except Exception:
                pass
            
            # 修复策略：以索引为准，重新整理元数据
            if index is not None and index.ntotal > 0:
                # 如果索引存在但元数据不存在或不匹配
                if metadata is None or (isinstance(metadata, list) and len(metadata) != index.ntotal):
                    # 创建新的元数据结构
                    if metadata is None:
                        metadata = [{"text": f"Unknown document {i}", "repaired": True} for i in range(index.ntotal)]
                        result["repairs_made"].append("创建了新的元数据结构")
                    elif isinstance(metadata, list) and len(metadata) < index.ntotal:
                        # 元数据数量少于索引，添加缺失的条目
                        original_count = len(metadata)
                        for i in range(original_count, index.ntotal):
                            metadata.append({"text": f"Unknown document {i}", "repaired": True})
                        result["repairs_made"].append(f"添加了 {index.ntotal - original_count} 个缺失的元数据条目")
                    elif isinstance(metadata, list) and len(metadata) > index.ntotal:
                        # 元数据数量多于索引，截断
                        metadata = metadata[:index.ntotal]
                        result["repairs_made"].append(f"截断了多余的元数据条目，保留了 {index.ntotal} 个")
                    
                    # 保存修复后的元数据
                    self.metadata[collection_name] = metadata
                    metadata_saved = self._save_metadata(collection_name)
                    if metadata_saved:
                        result["repairs_made"].append("成功保存了修复后的元数据")
                    else:
                        result["issues_found"].append("保存修复后的元数据失败")
            
            # 如果索引为空但元数据存在，重建索引
            elif (index is None or index.ntotal == 0) and metadata is not None and len(metadata) > 0:
                result["issues_found"].append("索引为空但元数据存在，需要重建索引")
                result["repairs_made"].append("无法自动修复此问题，请考虑重新添加文档")
            
            # 如果文件注册表为空或不存在，尝试重建
            if file_registry is None or len(file_registry) == 0:
                self.file_registry[collection_name] = {}
                registry_saved = self._save_file_registry(collection_name)
                if registry_saved:
                    result["repairs_made"].append("创建了新的文件注册表")
                else:
                    result["issues_found"].append("创建文件注册表失败")
            
            # 再次检查一致性
            diagnosis_after = self.diagnose_knowledge_base(collection_name)
            if diagnosis_after["is_consistent"]:
                result["status"] = "success"
                result["success"] = True
                result["message"] = "成功修复了知识库数据一致性问题"
            else:
                result["status"] = "error"
                result["success"] = False
                result["message"] = "修复失败，仍存在数据一致性问题"
                result["remaining_issues"] = diagnosis_after["issues"]
            
            return result
            
        except Exception as e:
            logger.error(f"修复知识库 {collection_name} 失败: {str(e)}")
            logger.error(traceback.format_exc())
            result["status"] = "error"
            result["success"] = False
            result["message"] = f"修复过程发生错误: {str(e)}"
            return result

    def _ensure_collection_exists(self, collection_name: str) -> bool:
        """
        确保集合存在，如果不存在则创建
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 集合是否存在或已成功创建
        """
        try:
            if not self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 不存在，将创建新集合")
                # 默认使用512维度创建集合
                return self.create_collection(collection_name, dimension=512, index_type="Flat")
            return True
        except Exception as e:
            logger.error(f"确保集合 {collection_name} 存在时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def verify_indexes(self, repair: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        验证所有索引的完整性，检查索引、元数据和文件注册表是否一致
        
        Args:
            repair: 是否自动修复发现的问题
            
        Returns:
            Dict: 验证报告
        """
        logger.info(f"开始验证所有索引，repair={repair}")
        results = {}
        
        # 获取所有集合
        collections = self.list_collections()
        
        # 如果没有集合，返回空结果
        if not collections:
            logger.info("没有找到任何集合")
            return {"status": "empty", "message": "没有找到任何集合"}
        
        logger.info(f"发现 {len(collections)} 个集合: {collections}")
        
        # 检查每个集合
        for collection_name in collections:
            try:
                logger.info(f"检查集合: {collection_name}")
                result = {
                    "status": "ok",
                    "errors": [],
                    "warnings": [],
                    "repairs": []
                }
                
                # 检查索引文件是否存在
                index_path = self._get_index_path(collection_name)
                metadata_path = self._get_metadata_path(collection_name)
                registry_path = self._get_file_registry_path(collection_name)
                
                if not os.path.exists(index_path):
                    result["errors"].append(f"索引文件不存在: {index_path}")
                    result["status"] = "error"
                    continue
                
                if not os.path.exists(metadata_path):
                    result["errors"].append(f"元数据文件不存在: {metadata_path}")
                    result["status"] = "error"
                    continue
                
                if not os.path.exists(registry_path):
                    result["warnings"].append(f"文件注册表不存在: {registry_path}")
                    result["status"] = "warning"
                
                # 尝试加载索引和元数据
                index_loaded = self._load_index(collection_name)
                if not index_loaded:
                    result["errors"].append("索引加载失败")
                    result["status"] = "error"
                    results[collection_name] = result
                    continue
                
                metadata_loaded = self._load_metadata(collection_name)
                if not metadata_loaded:
                    result["errors"].append("元数据加载失败")
                    result["status"] = "error"
                    results[collection_name] = result
                    continue
                
                registry_loaded = self._load_file_registry(collection_name)
                if not registry_loaded and os.path.exists(registry_path):
                    result["warnings"].append("文件注册表加载失败")
                    result["status"] = "warning"
                
                # 检查索引和元数据大小是否一致
                index = self.indexes[collection_name]
                metadata = self.metadata[collection_name]
                
                index_size = index.ntotal
                result["index_size"] = index_size
                
                # 计算元数据大小
                if isinstance(metadata, list):
                    metadata_size = len(metadata)
                elif isinstance(metadata, dict):
                    metadata_size = len(metadata)
                else:
                    metadata_size = 0
                    result["errors"].append(f"元数据格式错误: {type(metadata)}")
                    result["status"] = "error"
                
                result["metadata_size"] = metadata_size
                
                # 检查索引和元数据大小是否一致
                if index_size != metadata_size:
                    result["errors"].append(f"索引大小 ({index_size}) 和元数据大小 ({metadata_size}) 不匹配")
                    result["status"] = "error"
                    
                    # 如果需要修复，执行修复操作
                    if repair:
                        repair_result = self.repair_knowledge_base(collection_name)
                        result["repairs"].append(repair_result)
                
                # 如果有文件注册表，检查文件注册表中的向量数量是否与索引匹配
                if collection_name in self.file_registry:
                    registry = self.file_registry[collection_name]
                    total_vectors = 0
                    
                    for file_name, file_info in registry.items():
                        if file_name.startswith('_'):  # 跳过内部字段
                            continue
                            
                        if "vector_count" in file_info:
                            total_vectors += file_info["vector_count"]
                    
                    result["registry_vector_count"] = total_vectors
                    
                    if total_vectors != index_size:
                        result["warnings"].append(f"文件注册表中的向量总数 ({total_vectors}) 与索引大小 ({index_size}) 不匹配")
                        if result["status"] == "ok":
                            result["status"] = "warning"
                    
                # 保存结果
                results[collection_name] = result
                logger.info(f"集合 {collection_name} 验证结果: {result['status']}")
                
            except Exception as e:
                logger.error(f"验证集合 {collection_name} 时出错: {str(e)}")
                results[collection_name] = {
                    "status": "error",
                    "errors": [f"验证过程异常: {str(e)}"]
                }
        
        # 返回总体结果
        return {
            "status": "completed",
            "checked_collections": len(collections),
            "results": results
        }

    def check_and_fix_collection_consistency(self, collection_name: str) -> bool:
        """
        检查集合的索引和元数据是否一致，如果不一致则尝试修复
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 检查和修复是否成功
        """
        try:
            # 确保索引和元数据已加载
            if collection_name not in self.indexes:
                load_success = self._load_index(collection_name)
                if not load_success:
                    logger.error(f"检查一致性时无法加载索引 {collection_name}")
                    return False
            
            if collection_name not in self.metadata:
                load_success = self._load_metadata(collection_name)
                if not load_success:
                    logger.error(f"检查一致性时无法加载元数据 {collection_name}")
                    return False
            
            # 获取已加载的对象
            index = self.indexes[collection_name]
            metadata = self.metadata[collection_name]
            
            # 获取索引和元数据的大小
            index_size = index.ntotal
            
            if isinstance(metadata, dict):
                metadata_size = len(metadata)
            elif isinstance(metadata, list):
                metadata_size = len(metadata)
            else:
                logger.error(f"元数据格式错误: {type(metadata)}")
                return False
            
            logger.info(f"检查集合 {collection_name} 一致性: 索引大小={index_size}, 元数据大小={metadata_size}")
            
            # 如果索引为空但有元数据，尝试修复
            if index_size == 0 and metadata_size > 0:
                logger.warning(f"检测到不一致: 索引为空但元数据不为空，尝试修复...")
                
                # 记录错误
                logger.error(f"集合 {collection_name} 索引和元数据不一致。请运行 repair_knowledge_base 函数进行修复。")
                
                # 提示用户运行repair_knowledge_base
                logger.info(f"建议: 请通过调用 repair_knowledge_base('{collection_name}') 来修复此问题。")
                
                return False
            
            # 如果索引和元数据大小不一致，记录警告但不尝试修复
            if index_size != metadata_size:
                logger.warning(f"集合 {collection_name} 索引大小 ({index_size}) 与元数据大小 ({metadata_size}) 不一致")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查集合 {collection_name} 一致性时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False





class DataLineageTracker:
    def track_document_creation(self, document_id, source_info):
        """记录文档创建的来源信息"""
        lineage_record = {
            "document_id": document_id,
            "created_at": datetime.now(),
            "source_type": source_info.get("type"),
            "source_id": source_info.get("id"),
            "transformation": source_info.get("transformation"),
            "upstream_documents": source_info.get("references", [])
        }
        self.lineage_store.insert(lineage_record)


if __name__ == "__main__":
    faiss_manager = FaissManager()
    faiss_manager.create_collection("test_collection", dimension=1536, index_type="Flat")
    faiss_manager.add_vectors("test_collection", np.random.random((1000, 1536)).astype('float32'), [{"text": "test"}], "test.txt")
    results = faiss_manager.search("test_collection", np.random.random((1536,)).astype('float32'), top_k=5)
    print(results)
    # files_info = faiss_manager.list_files("test")
    # print(files_info)
    # file_info = faiss_manager.get_file_info("test", "test.txt")
    # print(file_info)
    # faiss_manager.replace_file("test_collection", "test.txt", np.random.random((1000, 1536)).astype('float32'), [{"text": "test"}])
    # faiss_manager.delete_file("test_collection", "test.txt")
    # faiss_manager.delete_collection("test_collection")

