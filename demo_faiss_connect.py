#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
演示脚本：展示FaissManager的核心功能
"""

import os
import numpy as np
import logging
from typing import List, Dict, Any
import time

# 导入要测试的模块
from core.faiss_connect import FaissManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_faiss_manager():
    """演示FaissManager的主要功能"""
    print("=" * 50)
    print("FAISS向量数据库功能演示")
    print("=" * 50)
    
    # 创建测试目录
    test_dir = os.path.join(os.path.dirname(__file__), "test_faiss_db")
    os.makedirs(test_dir, exist_ok=True)
    print(f"测试数据库路径: {test_dir}")
    
    # 初始化FaissManager
    faiss_manager = FaissManager(index_folder=test_dir)
    test_collection = "demo_collection"
    dimension = 512  # 向量维度
    
    # 1. 创建集合
    print("\n1. 创建向量集合")
    print("-" * 30)
    if faiss_manager.collection_exists(test_collection):
        print(f"集合 '{test_collection}' 已存在，正在删除...")
        faiss_manager.delete_collection(test_collection)
    
    result = faiss_manager.create_collection(test_collection, dimension, index_type="Flat")
    print(f"创建集合结果: {'成功' if result else '失败'}")
    
    # 2. 添加向量
    print("\n2. 添加向量")
    print("-" * 30)
    num_vectors = 5
    # 创建随机测试向量
    test_vectors = np.random.random((num_vectors, dimension)).astype(np.float32)
    # 创建测试元数据
    test_metadata = [
        {
            "text": f"这是测试文档 {i}，用于演示FAISS的向量存储和检索功能",
            "metadata": {
                "source": "demo",
                "doc_id": f"doc_{i}",
                "importance": (i + 1) / num_vectors
            }
        } 
        for i in range(num_vectors)
    ]
    
    # 添加向量到集合
    add_result = faiss_manager.add_vectors(test_collection, test_vectors, test_metadata, file_path="demo_file.txt")
    print(f"添加向量结果: {add_result.get('status', '未知')}")
    print(f"添加的向量数量: {add_result.get('vectors_added', 0)}")
    
    # 3. 获取集合信息
    print("\n3. 获取集合信息")
    print("-" * 30)
    collection_info = faiss_manager.get_collection_info(test_collection)
    print(f"集合名称: {collection_info.get('name', '未知')}")
    print(f"向量维度: {collection_info.get('dimension', 0)}")
    print(f"索引类型: {collection_info.get('index_type', '未知')}")
    print(f"向量数量: {collection_info.get('vectors_count', 0)}")
    print(f"文件数量: {collection_info.get('files_count', 0)}")
    
    # 4. 执行向量搜索
    print("\n4. 执行向量搜索")
    print("-" * 30)
    # 使用第一个向量作为查询向量
    query_vector = test_vectors[0]
    print("查询向量:", query_vector[:5], "...")  # 只显示前几个元素
    
    # 搜索向量
    start_time = time.time()
    indices, similarities, metadata_list = faiss_manager.search(test_collection, query_vector, top_k=3)
    search_time = time.time() - start_time
    
    print(f"搜索耗时: {search_time:.4f}秒")
    print(f"找到 {len(indices)} 条结果:")
    
    # 显示搜索结果
    for i, (idx, sim, meta) in enumerate(zip(indices, similarities, metadata_list)):
        print(f"\n结果 #{i+1}:")
        print(f"  索引ID: {idx}")
        print(f"  相似度: {sim:.4f}")
        print(f"  文本: {meta.get('text', '')[:50]}...")
        print(f"  元数据: {meta.get('metadata', {})}")
    
    # 5. 文件管理功能
    print("\n5. 文件管理功能")
    print("-" * 30)
    # 列出所有文件
    files = faiss_manager.list_files(test_collection)
    print(f"集合中的文件数量: {len(files)}")
    
    for i, file_info in enumerate(files):
        print(f"\n文件 #{i+1}:")
        print(f"  文件名: {file_info.get('file_name', '未知')}")
        print(f"  添加时间: {file_info.get('added', '未知')}")
        print(f"  向量数量: {file_info.get('vectors_count', 0)}")
    
    # 6. 删除向量
    print("\n6. 删除向量")
    print("-" * 30)
    # 删除第一个向量
    ids_to_delete = [0]
    delete_result = faiss_manager.delete_vectors(test_collection, ids_to_delete)
    print(f"删除向量结果: {'成功' if delete_result else '失败'}")
    
    # 验证删除结果
    collection_info = faiss_manager.get_collection_info(test_collection)
    print(f"删除后的向量数量: {collection_info.get('vectors_count', 0)}")
    
    # 7. 清理测试资源
    print("\n7. 清理测试资源")
    print("-" * 30)
    # 删除测试集合
    delete_collection_result = faiss_manager.delete_collection(test_collection)
    print(f"删除集合结果: {'成功' if delete_collection_result else '失败'}")
    
    print("\n演示完成!")

if __name__ == "__main__":
    demo_faiss_manager() 