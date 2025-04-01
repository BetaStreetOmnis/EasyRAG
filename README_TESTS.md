# EasyRAG 测试指南

本文档提供了有关如何运行和使用EasyRAG测试脚本的指南。

## 测试脚本概述

EasyRAG项目包含以下测试脚本：

1. **test_faiss_connect.py** - 使用unittest框架测试FaissManager类的核心功能
2. **demo_faiss_connect.py** - 演示脚本，直观展示FaissManager的主要功能
3. **test_rag_service.py** - 集成测试，测试RAGService类的各项功能
4. **test_file_listing.py** - 专门测试文件列表、文件路径和文件名处理功能
5. **run_tests.py** - 测试运行器，可以方便地选择运行不同的测试

## 运行测试

您可以使用测试运行器来选择和运行测试：

```bash
# 列出所有可用的测试
python run_tests.py --list

# 运行特定测试
python run_tests.py --test test_faiss_connect
python run_tests.py --test demo_faiss_connect
python run_tests.py --test test_rag_service
python run_tests.py --test test_file_listing
```

或者，您可以直接运行各个测试脚本：

```bash
# 运行FaissManager单元测试
python test_faiss_connect.py

# 运行FAISS演示
python demo_faiss_connect.py

# 运行RAGService测试
python test_rag_service.py

# 运行文件列表测试
python test_file_listing.py
```

## 测试脚本详情

### test_faiss_connect.py

这是一个基于unittest的测试套件，测试FaissManager类的各项功能：

- 创建和删除集合
- 添加和删除向量
- 向量搜索
- 文件管理
- 错误处理
- 文件路径和文件名处理

测试会自动创建临时目录作为测试环境，测试完成后会自动清理。

### demo_faiss_connect.py

这是一个直观的演示脚本，逐步展示FaissManager的核心功能：

1. 创建向量集合
2. 添加向量和元数据
3. 获取集合信息
4. 执行向量搜索
5. 文件管理功能
6. 删除向量
7. 清理资源

运行此脚本可以观察到每个步骤的输出结果，有助于理解FaissManager的工作方式。

### test_rag_service.py

这是对RAGService类的功能测试，包括：

- 知识库管理（创建、列出、获取信息）
- 文档添加
- 向量搜索
- 文件管理（列出文件、获取文件信息、更新文件重要性、删除文件）

此测试使用预定义的测试数据和查询，输出详细的测试结果。

### test_file_listing.py

这是一个专门测试文件列表功能的脚本，重点关注：

- 文件路径格式处理（Windows路径、Unix路径）
- 文件名与路径的一致性
- 文件元数据的正确存储和检索
- 文件版本信息的管理

此测试创建多种格式的文件路径，验证系统能正确处理这些路径并返回准确的文件信息。

## 注意事项

- 所有测试脚本都会创建临时目录作为测试环境，测试完成后会自动清理
- 测试过程中可能需要下载或加载嵌入模型，首次运行可能会较慢
- 如果测试失败，请检查相关依赖是否正确安装
- 对于文件路径测试，会使用多种路径格式，但并不实际创建这些文件

## 依赖

运行测试需要以下依赖：

- numpy
- faiss-cpu (或 faiss-gpu)
- unittest (Python标准库)
- 其他EasyRAG项目依赖

## 自定义测试

如果您需要针对特定功能进行测试，可以基于现有测试脚本进行修改。例如：

1. 修改 `test_rag_service.py` 中的 `test_documents` 和 `test_queries` 以测试特定领域的内容
2. 调整 `demo_faiss_connect.py` 中的向量维度和数量以测试不同规模的数据
3. 在 `test_faiss_connect.py` 中添加新的测试用例以覆盖更多边缘情况
4. 修改 `test_file_listing.py` 中的文件路径以测试特定文件系统结构 