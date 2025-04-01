#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件列表功能测试：专门测试FaissManager的文件列表功能
"""

import os
import logging
import tempfile
import shutil
import numpy as np
from typing import List, Dict, Any

# 导入要测试的模块
from core.faiss_connect import FaissManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_file_listing():
    """测试文件列表功能"""
    print("=" * 60)
    print("开始测试文件列表功能")
    print("=" * 60)
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化FaissManager
        faiss_manager = FaissManager(index_folder=test_dir)
        
        # 创建测试集合
        collection_name = "test_file_listing"
        dimension = 512
        
        print(f"\n创建测试集合: {collection_name}")
        create_result = faiss_manager.create_collection(collection_name, dimension, index_type="Flat")
        print(f"创建结果: {'成功' if create_result else '失败'}")
        
        # 添加多个文件
        test_files = [
            {"name": "document1.txt", "path": "C:/docs/document1.txt"},
            {"name": "report2023.pdf", "path": "D:/reports/report2023.pdf"},
            {"name": "data_analysis.csv", "path": "/data/analysis/data_analysis.csv"},
            {"name": "notes.docx", "path": os.path.join(os.getcwd(), "notes.docx")}
        ]
        
        print("\n添加测试文件:")
        
        for i, file_info in enumerate(test_files):
            # 为每个文件创建少量测试向量
            num_vectors = 3
            test_vectors = np.random.random((num_vectors, dimension)).astype(np.float32)
            
            # 创建测试元数据
            test_metadata = [
                {
                    "text": f"这是来自 {file_info['name']} 的测试文本 {j}",
                    "metadata": {
                        "source": file_info['name'],
                        "chunk_index": j,
                        "total_chunks": num_vectors
                    }
                } 
                for j in range(num_vectors)
            ]
            
            # 添加向量到集合，使用实际的文件路径
            result = faiss_manager.add_vectors(
                collection_name, 
                test_vectors, 
                test_metadata, 
                file_path=file_info['path']
            )
            
            print(f"  {i+1}. 添加 {file_info['name']} (路径: {file_info['path']}): " + 
                  f"{'成功' if result.get('status') == 'success' else '失败'}")
        
        # 测试文件列表功能
        print("\n获取文件列表:")
        files = faiss_manager.list_files(collection_name)
        
        print(f"找到 {len(files)} 个文件:")
        
        for i, file_data in enumerate(files):
            print(f"\n文件 #{i+1}:")
            for key, value in file_data.items():
                print(f"  {key}: {value}")
            
            # 验证文件名和路径
            file_name = file_data.get('file_name', '')
            file_path = file_data.get('file_path', '')
            
            # 检查文件名是否是完整路径的文件名部分
            if file_name and file_path:
                file_name_from_path = os.path.basename(file_path)
                if file_name != file_name_from_path:
                    print(f"  警告: 文件名不匹配 - 名称: {file_name}, 路径中的名称: {file_name_from_path}")
                else:
                    print(f"  验证: 文件名与路径匹配")
        
        # 测试获取单个文件详情
        if files:
            print("\n获取第一个文件的详细信息:")
            first_file = files[0]['file_name']
            file_details = faiss_manager.get_file_info(collection_name, first_file)
            
            print(f"文件 '{first_file}' 的详细信息:")
            for key, value in file_details.items():
                if key != 'versions':  # 版本信息可能很长，简化显示
                    print(f"  {key}: {value}")
            
            if 'versions' in file_details:
                print(f"  版本数量: {len(file_details['versions'])}")
                
                # 显示最新版本的简要信息
                if file_details['versions']:
                    latest_version = file_details['versions'][-1]
                    print("  最新版本信息:")
                    print(f"    版本号: {latest_version.get('version', '未知')}")
                    print(f"    向量数量: {latest_version.get('vector_count', 0)}")
                    print(f"    创建时间: {latest_version.get('created_at', '未知')}")
        
        print("\n测试完成！")
    
    finally:
        # 清理测试目录
        print(f"\n清理测试目录: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)
        
if __name__ == "__main__":
    test_file_listing() 