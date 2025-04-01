#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行器：允许用户选择运行不同的测试脚本
"""

import os
import sys
import logging
import importlib.util
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_module_from_file(file_path):
    """从文件路径导入模块"""
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def list_available_tests():
    """列出可用的测试脚本"""
    test_files = [
        f for f in os.listdir(".")
        if f.startswith("test_") and f.endswith(".py") or f.startswith("demo_") and f.endswith(".py")
    ]
    return test_files

def run_test_by_name(test_name):
    """运行指定名称的测试"""
    if not test_name.endswith(".py"):
        test_name += ".py"
    
    if not os.path.exists(test_name):
        logger.error(f"测试文件 {test_name} 不存在")
        return False
    
    logger.info(f"运行测试: {test_name}")
    
    try:
        # 导入模块并执行
        module = import_module_from_file(test_name)
        
        # 对于测试类
        if test_name == "test_rag_service.py" and hasattr(module, "RAGServiceTester"):
            tester = module.RAGServiceTester()
            tester.run_tests()
        # 对于演示脚本
        elif test_name == "demo_faiss_connect.py" and hasattr(module, "demo_faiss_manager"):
            module.demo_faiss_manager()
        # 对于文件列表测试
        elif test_name == "test_file_listing.py" and hasattr(module, "test_file_listing"):
            module.test_file_listing()
        # 对于unittest测试
        elif test_name == "test_faiss_connect.py" and hasattr(module, "unittest"):
            module.unittest.main(module=module)
        # 其他模块可能直接在__main__中执行测试
        else:
            logger.info(f"使用模块默认执行方式运行 {test_name}")
        
        return True
    except Exception as e:
        logger.error(f"运行测试 {test_name} 失败: {str(e)}")
        logger.exception(e)
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="EasyRAG测试运行器")
    parser.add_argument(
        "--test", 
        help="要运行的测试名称，不提供则显示可用测试列表"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="列出所有可用的测试"
    )
    
    args = parser.parse_args()
    
    if args.list or not args.test:
        print("\n可用的测试脚本:")
        for i, test_file in enumerate(list_available_tests(), 1):
            print(f"{i}. {test_file}")
        print("\n使用方式: python run_tests.py --test <测试名称>")
        print("例如: python run_tests.py --test demo_faiss_connect")
        return
    
    run_test_by_name(args.test)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EasyRAG测试运行器")
    print("=" * 60 + "\n")
    main() 