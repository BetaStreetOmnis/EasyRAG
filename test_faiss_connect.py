import os
import unittest
import numpy as np
from typing import List, Dict, Any
import tempfile
import shutil
import logging

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入要测试的模块
from core.faiss_connect import FaissManager

class TestFaissManager(unittest.TestCase):
    """测试FaissManager类的功能"""

    def setUp(self):
        """在每个测试用例前运行，设置测试环境"""
        # 创建临时目录作为测试索引存储位置
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"创建测试目录: {self.test_dir}")
        self.faiss_manager = FaissManager(index_folder=self.test_dir)
        self.test_collection = "test_collection"
        self.dimension = 512  # 设置向量维度

    def tearDown(self):
        """在每个测试用例后运行，清理测试环境"""
        # 删除测试目录
        logger.info(f"清理测试目录: {self.test_dir}")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_collection(self):
        """测试创建集合功能"""
        logger.info("开始测试创建集合功能")
        try:
            # 创建测试集合
            result = self.faiss_manager.create_collection(self.test_collection, self.dimension)
            self.assertTrue(result, "创建集合应该成功")
            
            # 验证集合是否存在
            self.assertTrue(self.faiss_manager.collection_exists(self.test_collection), 
                            "创建后集合应该存在")
            
            # 获取集合信息并验证
            collection_info = self.faiss_manager.get_collection_info(self.test_collection)
            self.assertEqual(collection_info["dimension"], self.dimension, 
                             "集合维度应该与创建时指定的一致")
        except Exception as e:
            logger.error(f"测试创建集合失败: {str(e)}", exc_info=True)
            raise

    def test_add_vectors(self):
        """测试添加向量功能"""
        logger.info("开始测试添加向量功能")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 创建测试向量和元数据
            num_vectors = 10
            test_vectors = np.random.random((num_vectors, self.dimension)).astype(np.float32)
            test_metadata = [{"text": f"测试文本 {i}", "metadata": {"source": "test"}} for i in range(num_vectors)]
            
            # 添加向量
            result = self.faiss_manager.add_vectors(self.test_collection, test_vectors, test_metadata)
            self.assertEqual(result["status"], "success", "添加向量应该成功")
            
            # 验证添加后的向量数量
            collection_info = self.faiss_manager.get_collection_info(self.test_collection)
            self.assertEqual(collection_info["vectors_count"], num_vectors, 
                             f"集合应包含 {num_vectors} 个向量")
        except Exception as e:
            logger.error(f"测试添加向量失败: {str(e)}", exc_info=True)
            raise

    def test_search(self):
        """测试向量搜索功能"""
        logger.info("开始测试向量搜索功能")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 创建测试向量和元数据
            num_vectors = 10
            test_vectors = np.random.random((num_vectors, self.dimension)).astype(np.float32)
            test_metadata = [{"text": f"测试文本 {i}", "metadata": {"source": "test"}} for i in range(num_vectors)]
            
            # 添加向量
            self.faiss_manager.add_vectors(self.test_collection, test_vectors, test_metadata)
            
            # 创建查询向量
            query_vector = np.random.random(self.dimension).astype(np.float32)
            
            # 搜索
            indices, similarities, metadata_list = self.faiss_manager.search(self.test_collection, query_vector, top_k=3)
            
            # 验证搜索结果
            self.assertLessEqual(len(indices), 3, "搜索结果数量应该小于等于top_k")
            self.assertEqual(len(indices), len(similarities), "索引和相似度列表长度应该一致")
            self.assertEqual(len(indices), len(metadata_list), "索引和元数据列表长度应该一致")
        except Exception as e:
            logger.error(f"测试向量搜索失败: {str(e)}", exc_info=True)
            raise

    def test_file_management(self):
        """测试文件管理功能"""
        logger.info("开始测试文件管理功能")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 添加带文件信息的向量
            num_vectors = 5
            test_vectors = np.random.random((num_vectors, self.dimension)).astype(np.float32)
            test_file = "test_file.txt"
            test_metadata = [
                {"text": f"测试文档 {i}", 
                 "metadata": {"file_name": test_file, "chunk_index": i}} 
                for i in range(num_vectors)
            ]
            
            # 添加向量和文件信息
            self.faiss_manager.add_vectors(self.test_collection, test_vectors, test_metadata, file_path=test_file)
            
            # 获取文件列表
            files = self.faiss_manager.list_files(self.test_collection)
            self.assertEqual(len(files), 1, "应该有一个文件被注册")
            self.assertEqual(files[0]["file_name"], test_file, "文件名应该匹配")
            
            # 获取文件详情
            file_info = self.faiss_manager.get_file_info(self.test_collection, test_file)
            self.assertEqual(file_info["file_name"], test_file, "文件详情中的文件名应该匹配")
            
            # 删除文件
            delete_result = self.faiss_manager.delete_file(self.test_collection, test_file)
            self.assertTrue(delete_result, "删除文件应该成功")
            
            # 验证文件已删除
            files_after_delete = self.faiss_manager.list_files(self.test_collection)
            self.assertEqual(len(files_after_delete), 0, "删除后文件列表应该为空")
        except Exception as e:
            logger.error(f"测试文件管理失败: {str(e)}", exc_info=True)
            raise

    def test_delete_vectors(self):
        """测试删除向量功能"""
        logger.info("开始测试删除向量功能")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 添加测试向量
            num_vectors = 10
            test_vectors = np.random.random((num_vectors, self.dimension)).astype(np.float32)
            test_metadata = [{"text": f"测试文本 {i}", "metadata": {"source": "test"}} for i in range(num_vectors)]
            
            # 添加向量
            result = self.faiss_manager.add_vectors(self.test_collection, test_vectors, test_metadata)
            ids_to_delete = [0, 2, 4]  # 删除部分ID
            
            # 删除向量
            delete_result = self.faiss_manager.delete_vectors(self.test_collection, ids_to_delete)
            self.assertTrue(delete_result, "删除向量应该成功")
            
            # 验证删除后的向量数量
            collection_info = self.faiss_manager.get_collection_info(self.test_collection)
            expected_count = num_vectors - len(ids_to_delete)
            self.assertEqual(collection_info["vectors_count"], expected_count, 
                             f"删除后集合应包含 {expected_count} 个向量")
        except Exception as e:
            logger.error(f"测试删除向量失败: {str(e)}", exc_info=True)
            raise

    def test_delete_collection(self):
        """测试删除集合功能"""
        logger.info("开始测试删除集合功能")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 验证集合存在
            self.assertTrue(self.faiss_manager.collection_exists(self.test_collection))
            
            # 删除集合
            result = self.faiss_manager.delete_collection(self.test_collection)
            self.assertTrue(result, "删除集合应该成功")
            
            # 验证集合已删除
            self.assertFalse(self.faiss_manager.collection_exists(self.test_collection), 
                             "集合应该已被删除")
        except Exception as e:
            logger.error(f"测试删除集合失败: {str(e)}", exc_info=True)
            raise

    def test_error_handling(self):
        """测试错误处理情况"""
        logger.info("开始测试错误处理情况")
        try:
            # 测试操作不存在的集合
            non_existent = "non_existent_collection"
            
            # 搜索不存在的集合
            indices, similarities, metadata_list = self.faiss_manager.search(non_existent, np.random.random(self.dimension))
            self.assertEqual(indices, [], "搜索不存在的集合应返回空列表")
            
            # 获取不存在的集合信息
            collection_info = self.faiss_manager.get_collection_info(non_existent)
            self.assertFalse(collection_info.get("success", False), "获取不存在集合信息应失败")
            
            # 删除不存在的集合
            delete_result = self.faiss_manager.delete_collection(non_existent)
            self.assertFalse(delete_result, "删除不存在的集合应失败")
        except Exception as e:
            logger.error(f"测试错误处理失败: {str(e)}", exc_info=True)
            raise

    def test_file_path_handling(self):
        """测试文件路径和文件名的处理"""
        logger.info("开始测试文件路径和文件名处理")
        try:
            # 创建测试集合
            self.faiss_manager.create_collection(self.test_collection, self.dimension)
            
            # 创建带有实际文件路径的测试向量
            num_vectors = 5
            test_vectors = np.random.random((num_vectors, self.dimension)).astype(np.float32)
            
            # 定义测试文件路径（使用不同格式的路径）
            test_file_paths = [
                os.path.join(os.getcwd(), "test_document.txt"),  # 相对路径转绝对路径
                "C:/users/documents/report.pdf",  # Windows格式
                "/home/user/data/file.csv",  # Unix格式
                "..\\media\\image.jpg"  # Windows相对路径
            ]
            
            logger.info("添加不同路径格式的文件...")
            for i, file_path in enumerate(test_file_paths):
                # 提取文件名
                file_name = os.path.basename(file_path)
                
                # 创建测试元数据
                test_metadata = [
                    {"text": f"测试文档 {j} 来自 {file_path}", 
                     "metadata": {"source": file_path, "index": j}} 
                    for j in range(num_vectors)
                ]
                
                # 添加向量
                result = self.faiss_manager.add_vectors(
                    self.test_collection, 
                    test_vectors, 
                    test_metadata, 
                    file_path=file_path
                )
                
                self.assertEqual(result["status"], "success", f"添加向量应该成功，文件路径: {file_path}")
                logger.info(f"成功添加文件 {i+1}/{len(test_file_paths)}")
            
            # 获取文件列表
            files = self.faiss_manager.list_files(self.test_collection)
            self.assertEqual(len(files), len(test_file_paths), "文件列表长度应该与添加的文件数量一致")
            
            logger.info("验证文件名和路径...")
            for file_info in files:
                # 检查文件信息是否完整
                self.assertIn("file_name", file_info, "文件信息应包含file_name字段")
                self.assertIn("file_path", file_info, "文件信息应包含file_path字段")
                
                # 验证文件名是否是文件路径的basename
                file_name = file_info["file_name"]
                file_path = file_info["file_path"]
                expected_name = os.path.basename(file_path)
                
                self.assertEqual(file_name, expected_name, 
                                 f"文件名 '{file_name}' 应该与路径basename '{expected_name}' 一致")
                
            logger.info("文件路径和文件名处理测试通过")
            
            # 测试获取特定文件的详细信息
            if files:
                first_file = files[0]["file_name"]
                file_detail = self.faiss_manager.get_file_info(self.test_collection, first_file)
                
                self.assertEqual(file_detail["file_name"], first_file, "文件详情中的名称应与请求的文件名一致")
                self.assertIn("file_path", file_detail, "文件详情应包含file_path")
                
                logger.info(f"成功获取文件 '{first_file}' 的详细信息")
        
        except Exception as e:
            logger.error(f"测试文件路径和文件名处理失败: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    unittest.main()
    # test_error_handling()