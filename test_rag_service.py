#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本：测试RAGService类的主要功能
"""

import os
import logging
import tempfile
import shutil
from typing import List, Dict, Any

# 导入要测试的模块
from main import RAGService, DocumentProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGServiceTester:
    """RAGService测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"创建测试目录: {self.test_dir}")
        
        # 初始化RAG服务
        self.rag_service = RAGService(db_path=self.test_dir)
        
        # 测试数据
        self.test_kb_name = "test_knowledge_base"
        self.test_documents = [
            {
                "text": "FAISS（Facebook AI Similarity Search）是Facebook研究院开发的一个高效相似性搜索和密集向量聚类的库。它包含了能够搜索任意大小向量集的算法，最高可达到数十亿向量级。",
                "metadata": {"source": "FAISS介绍", "category": "技术"}
            },
            {
                "text": "向量数据库是一种专门存储和检索向量嵌入（vector embeddings）的数据库系统。它针对高维向量的相似性搜索进行了优化，广泛应用于AI和机器学习领域。",
                "metadata": {"source": "向量数据库简介", "category": "技术"}
            },
            {
                "text": "RAG（检索增强生成）是一种将检索系统与生成式AI模型结合的技术。它通过从知识库中检索相关信息来增强大语言模型的回答能力，提高回答的准确性和可靠性。",
                "metadata": {"source": "RAG技术概述", "category": "AI"}
            },
            {
                "text": "Python是一种高级编程语言，以其简洁易读的语法和丰富的生态系统而闻名。它被广泛应用于网站开发、数据分析、人工智能和科学计算等领域。",
                "metadata": {"source": "Python编程语言", "category": "编程"}
            },
            {
                "text": "向量搜索是通过计算查询向量与数据库中存储向量之间的相似度来找到最相似内容的过程。常用的相似度计算方法包括余弦相似度、欧氏距离和点积等。",
                "metadata": {"source": "向量搜索原理", "category": "技术"}
            }
        ]
        
        # 测试查询
        self.test_queries = [
            "什么是FAISS?",
            "向量数据库的作用是什么?",
            "Python编程语言有什么特点?",
            "RAG技术是如何工作的?",
            "如何计算向量之间的相似度?"
        ]
    
    def cleanup(self):
        """清理测试环境"""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
            logger.info(f"已清理测试目录: {self.test_dir}")
        except Exception as e:
            logger.error(f"清理测试目录失败: {str(e)}")
    
    def run_tests(self):
        """运行所有测试"""
        try:
            print("=" * 60)
            print("开始RAGService功能测试")
            print("=" * 60)
            
            self.test_kb_management()
            self.test_document_addition()
            self.test_search()
            self.test_file_management()
            
            print("\n" + "=" * 60)
            print("测试完成!")
            print("=" * 60)
        finally:
            # 测试完成后清理环境
            self.cleanup()
    
    def test_kb_management(self):
        """测试知识库管理功能"""
        print("\n" + "=" * 40)
        print("测试知识库管理功能")
        print("=" * 40)
        
        # 1. 创建知识库
        print("\n1. 创建知识库")
        print("-" * 30)
        create_result = self.rag_service.create_knowledge_base(self.test_kb_name)
        print(f"创建知识库结果: {'成功' if create_result else '失败'}")
        
        # 2. 列出所有知识库
        print("\n2. 列出所有知识库")
        print("-" * 30)
        kb_list = self.rag_service.list_knowledge_bases()
        print(f"知识库列表: {kb_list}")
        assert self.test_kb_name in kb_list, "创建的知识库应该在列表中"
        
        # 3. 获取知识库信息
        print("\n3. 获取知识库信息")
        print("-" * 30)
        kb_info = self.rag_service.get_knowledge_base_info(self.test_kb_name)
        print(f"知识库名称: {kb_info.get('name', '未知')}")
        print(f"知识库维度: {kb_info.get('dimension', 0)}")
        print(f"索引类型: {kb_info.get('index_type', '未知')}")
        print(f"创建时间: {kb_info.get('created', '未知')}")
    
    def test_document_addition(self):
        """测试文档添加功能"""
        print("\n" + "=" * 40)
        print("测试文档添加功能")
        print("=" * 40)
        
        # 添加测试文档
        print("\n添加测试文档")
        print("-" * 30)
        
        # 定义进度回调函数
        def progress_callback(progress, message):
            if progress % 20 == 0:  # 每20%报告一次进度
                print(f"进度: {progress}% - {message}")
        
        # 添加文档到知识库
        add_result = self.rag_service.add_documents(
            self.test_kb_name, 
            self.test_documents, 
            file_path="test_data.txt",
            progress_callback=progress_callback
        )
        
        print(f"添加文档结果: {'成功' if add_result else '失败'}")
        
        # 验证添加结果
        kb_info = self.rag_service.get_knowledge_base_info(self.test_kb_name)
        print(f"添加后的向量数量: {kb_info.get('vectors_count', 0)}")
        assert kb_info.get('vectors_count', 0) == len(self.test_documents), "向量数量应与添加的文档数相符"
    
    def test_search(self):
        """测试搜索功能"""
        print("\n" + "=" * 40)
        print("测试搜索功能")
        print("=" * 40)
        
        for i, query in enumerate(self.test_queries):
            print(f"\n查询 {i+1}: {query}")
            print("-" * 30)
            
            # 执行搜索
            results = self.rag_service.search(
                self.test_kb_name,
                query,
                top_k=2,
                use_rerank=True
            )
            
            print(f"找到 {len(results)} 条结果")
            
            # 打印搜索结果
            for j, result in enumerate(results):
                print(f"\n结果 #{j+1}:")
                print(f"  相似度: {result.get('score', 0):.4f}")
                print(f"  内容: {result.get('content', '')[:100]}...")
                print(f"  元数据: {result.get('metadata', {})}")
    
    def test_file_management(self):
        """测试文件管理功能"""
        print("\n" + "=" * 40)
        print("测试文件管理功能")
        print("=" * 40)
        
        # 1. 列出知识库中的文件
        print("\n1. 列出知识库中的文件")
        print("-" * 30)
        files = self.rag_service.list_files(self.test_kb_name)
        print(f"文件数量: {len(files)}")
        
        if files:
            file_name = files[0].get('file_name', '')
            
            # 2. 获取文件信息
            print("\n2. 获取文件信息")
            print("-" * 30)
            file_info = self.rag_service.get_file_info(self.test_kb_name, file_name)
            print(f"文件名: {file_info.get('file_name', '未知')}")
            print(f"添加时间: {file_info.get('added', '未知')}")
            print(f"向量数量: {file_info.get('vectors_count', 0)}")
            
            # 3. 更新文件重要性
            print("\n3. 更新文件重要性")
            print("-" * 30)
            importance_factor = 2.0
            update_result = self.rag_service.update_file_importance(
                self.test_kb_name, 
                file_name, 
                importance_factor
            )
            print(f"更新文件重要性结果: {'成功' if update_result else '失败'}")
            
            # 4. 删除文件
            print("\n4. 删除文件")
            print("-" * 30)
            delete_result = self.rag_service.delete_file(self.test_kb_name, file_name)
            print(f"删除文件结果: {'成功' if delete_result else '失败'}")
            
            # 验证删除结果
            files_after = self.rag_service.list_files(self.test_kb_name)
            print(f"删除后的文件数量: {len(files_after)}")
        
        # 5. 删除测试知识库
        print("\n5. 删除测试知识库")
        print("-" * 30)
        delete_kb_result = self.rag_service.delete_knowledge_base(self.test_kb_name)
        print(f"删除知识库结果: {'成功' if delete_kb_result else '失败'}")

if __name__ == "__main__":
    tester = RAGServiceTester()
    tester.run_tests() 