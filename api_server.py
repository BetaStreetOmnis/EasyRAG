import os
import json
import traceback
import sys
import uuid
import os.path
import time
from urllib.parse import quote
from typing import List, Dict, Any, Optional, Union

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

# 确保当前目录在sys.path中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from main import RAGService, DocumentProcessor
# 添加进度跟踪字典
# 格式: {task_id: {"status": "processing/completed/failed", "progress": 0-100, "message": "处理中..."}}
processing_tasks = {}

# 定义API模型
class KnowledgeBaseCreate(BaseModel):
    kb_name: str
    dimension: int = 512
    index_type: str = "Flat"

class SearchQuery(BaseModel):
    kb_name: str
    query: str
    top_k: int = 5
    use_rerank: bool = True
    remove_duplicates: bool = True
    filter_criteria: str = ""

class ChunkConfig(BaseModel):
    method: str = "text_semantic"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    similarity_threshold: float = 0.7
    min_chunk_size: int = 100
    headers_to_split_on: Optional[List[Dict]] = None
    separators: Optional[List[str]] = None

# 添加文件管理相关模型
class FileInfo(BaseModel):
    kb_name: str
    file_path: str
    file_name: Optional[str] = None

# 初始化FastAPI应用
app = FastAPI(title="知识库管理API", description="提供知识库管理和检索的RESTful API")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加静态文件服务
web_dir = os.path.join(current_dir, "web")
os.makedirs(web_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=web_dir), name="static")

# 初始化RAG服务和文件处理器
rag_service = RAGService()
file_handler = None


@app.get("/")
async def root():
    """API根路径，重定向到首页"""
    return RedirectResponse(url="/static/index.html")

@app.get("/file-manager")
async def file_manager_page():
    """返回文件管理页面"""
    file_path = os.path.join(web_dir, "file_manager.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="文件管理页面不存在")

@app.post("/kb/create")
async def create_knowledge_base(kb_data: KnowledgeBaseCreate):
    """创建新的知识库"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        success = rag_service.create_knowledge_base(
            kb_data.kb_name, 
            kb_data.dimension, 
            kb_data.index_type
        )
        if success:
            return {"status": "success", "message": f"成功创建知识库：{kb_data.kb_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"创建知识库失败，可能已存在同名知识库：{kb_data.kb_name}")
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}\n{error_trace}")

@app.get("/kb/list")
async def list_knowledge_bases():
    """获取所有知识库列表"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        kb_list = rag_service.list_knowledge_bases()
        return {"status": "success", "data": kb_list}
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}\n{error_trace}")

@app.get("/kb/info/{kb_name}")
async def get_knowledge_base_info(kb_name: str):
    """获取指定知识库的信息"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        info = rag_service.get_knowledge_base_info(kb_name)
        if info:
            return {"status": "success", "data": info}
        else:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"获取知识库信息失败: {str(e)}\n{error_trace}")

@app.delete("/kb/delete/{kb_name}")
async def delete_knowledge_base(kb_name: str):
    """删除指定的知识库"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        success = rag_service.delete_knowledge_base(kb_name)
        if success:
            return {"status": "success", "message": f"成功删除知识库：{kb_name}"}
        else:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}\n{error_trace}")

@app.get("/kb/progress/{task_id}")
async def get_processing_progress(task_id: str):
    """获取任务处理进度"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail=f"任务ID {task_id} 不存在")
    
    return {
        "status": "success",
        "data": processing_tasks[task_id]
    }
@app.post("/kb/upload")
async def upload_files(
    kb_name: str = Form(...),
    files: List[UploadFile] = File(...),
    chunk_config: str = Form("{}")
):
    """上传文件到知识库"""
    try:
        # 检查必要的组件是否初始化
        rag_service = RAGService()
        document_processor = DocumentProcessor()
        task_id = str(uuid.uuid4())
        processing_tasks[task_id] = {
            "status": "processing", 
            "progress": 0, 
            "message": "准备处理文件..."
        }
        
        print(f"开始处理上传任务: {task_id}, 知识库: {kb_name}")
        print(f"文件数量: {len(files)}")
        for i, file in enumerate(files):
            print(f"文件 {i+1}: {file.filename}, 类型: {file.content_type}")
        
        # 解析分块配置
        config = json.loads(chunk_config)
        chunk_method = config.get("method", "text_semantic")
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 200)
        
        print(f"分块配置: 方法={chunk_method}, 大小={chunk_size}, 重叠={chunk_overlap}")
        
        total_docs = 0
        failed_files = []
        total_files = len(files)
        
        for file_index, file in enumerate(files):
            temp_file_path = None
            try:
                # 更新处理进度
                file_progress = int((file_index / total_files) * 100)
                processing_tasks[task_id] = {
                    "status": "processing", 
                    "progress": file_progress, 
                    "message": f"处理文件 {file_index+1}/{total_files}: {file.filename}"
                }
                
                print(f"开始处理文件 {file_index+1}/{total_files}: {file.filename}")
                
                # 修改这里：确保只使用文件名，而不是完整路径
                # 从原始文件名中提取文件名部分（忽略任何路径）
                orig_filename = os.path.basename(file.filename)
                safe_filename = quote(orig_filename)
                
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_files")
                os.makedirs(temp_dir, exist_ok=True)
                
                # 使用uuid生成唯一临时文件名，避免冲突
                temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{safe_filename}")
                
                # 打印文件信息
                print(f"原始文件名: {file.filename}")
                print(f"提取的文件名: {orig_filename}")
                print(f"安全处理后文件名: {safe_filename}")
                print(f"临时文件路径: {temp_file_path}")
                
                # 读取整个文件内容（只读取一次）
                file_content = await file.read()
                # print(4444, file_content)
                # 检查文件是否为空
                if not file_content or len(file_content) == 0:
                    error_msg = f"文件 {orig_filename} 为空，跳过处理"
                    print(error_msg)
                    failed_files.append(f"{orig_filename} (文件为空)")
                    processing_tasks[task_id]["message"] = error_msg
                    continue
                
                print(f"文件 '{orig_filename}' 大小: {len(file_content)} 字节")
                
                # 直接将文件内容写入临时文件
                print(f"写入临时文件: {temp_file_path}")
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(file_content)
                
                # 确认文件写入成功
                if not os.path.exists(temp_file_path):
                    error_msg = f"临时文件创建失败: {temp_file_path}"
                    print(error_msg)
                    failed_files.append(f"{orig_filename} (临时文件创建失败)")
                    continue
                
                temp_file_size = os.path.getsize(temp_file_path)
                if temp_file_size == 0:
                    error_msg = f"临时文件为空: {temp_file_path}"
                    print(error_msg)
                    failed_files.append(f"{orig_filename} (临时文件为空)")
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    continue
                
                print(f"临时文件写入成功，大小: {temp_file_size} 字节")
                
                # 定义进度回调函数
                def update_progress(progress, message):
                    # 计算总进度：文件进度(0-90) + 当前文件处理进度(最后10%)
                    file_base_progress = int((file_index / total_files) * 90)
                    current_progress = int(progress * 0.1)  # 当前文件进度占总进度的10%
                    total_progress = file_base_progress + current_progress
                    
                    processing_tasks[task_id] = {
                        "status": "processing", 
                        "progress": total_progress, 
                        "message": message
                    }
                
                # 使用DocumentProcessor处理文件
                processing_tasks[task_id]["message"] = f"处理文件 {orig_filename}..."
                print(f"使用DocumentProcessor处理文件: {temp_file_path}")
                
                try:
                    # 使用DocumentProcessor处理文件
                    document = document_processor.process_document(
                        file_path=temp_file_path,
                        chunk_method=chunk_method,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        progress_callback=update_progress
                    )
                    print(33333333333, document)
                    # 使用RAGService添加文档到知识库
                    processing_tasks[task_id]["message"] = f"添加文件 {orig_filename} 到知识库..."
                    success = rag_service.add_documents(
                        kb_name=kb_name,
                        documents=document
                    )
                    
                    if success:
                        print(f"文件 {orig_filename} 处理并添加成功")
                        total_docs += 1  # 增加成功处理的文档计数
                    else:
                        print(f"文件 {orig_filename} 添加到知识库失败")
                        failed_files.append(f"{orig_filename} (添加到知识库失败)")
                except Exception as e:
                    print(f"处理并添加文档时出错: {str(e)}")
                    traceback.print_exc()
                    failed_files.append(f"{orig_filename} (处理错误: {str(e)})")
                
                # 清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        print(f"临时文件已删除: {temp_file_path}")
                    except Exception as e:
                        print(f"删除临时文件时出错: {str(e)}")
            
            except Exception as e:
                error_trace = traceback.format_exc()
                error_msg = f"处理文件 {file.filename} 时发生未捕获的异常: {str(e)}"
                print(f"{error_msg}\n{error_trace}")
                # 使用提取的文件名报告错误
                orig_filename = os.path.basename(file.filename)
                failed_files.append(f"{orig_filename} (错误: {str(e)})")
                
                # 确保清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        print(f"清理临时文件: {temp_file_path}")
                    except:
                        pass
        
        # 更新处理完成状态
        processing_tasks[task_id] = {
            "status": "completed", 
            "progress": 100, 
            "message": "处理完成"
        }
        print(f"任务 {task_id} 处理完成")
        
        if failed_files:
            print(f"部分文件处理失败: {failed_files}")
            return {
                "status": "partial_success",
                "message": f"成功添加 {total_docs} 个文档，但以下文件处理失败：",
                "failed_files": failed_files,
                "task_id": task_id
            }
        else:
            print(f"所有文件处理成功")
            return {
                "status": "success",
                "message": f"成功添加 {total_docs} 个文档到知识库 {kb_name}",
                "task_id": task_id
            }
    except Exception as e:
        error_trace = traceback.format_exc()
        error_msg = f"文件上传处理失败: {str(e)}"
        print(f"{error_msg}\n{error_trace}")
        
        if 'task_id' in locals() and task_id in processing_tasks:
            processing_tasks[task_id] = {
                "status": "failed", 
                "progress": 0, 
                "message": f"处理失败: {str(e)}"
            }
        
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}\n{error_trace}")

@app.post("/kb/search")
async def search_knowledge_base(query: SearchQuery):
    """在知识库中搜索内容"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        results = rag_service.search(
            query.kb_name,
            query.query,
            query.top_k,
            query.use_rerank,
            query.remove_duplicates
        )
        
        if not results:
            return {
                "status": "success",
                "message": "未找到相关内容",
                "data": []
            }
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"搜索知识库失败: {str(e)}\n{error_trace}")

@app.post("/kb/delete_documents")
async def delete_documents(
    kb_name: str = Body(...),
    filter_criteria: str = Body(...)
):
    """根据过滤条件删除知识库中的文档"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        if not filter_criteria:
            raise HTTPException(status_code=400, detail="必须提供过滤条件")
        
        result = rag_service.delete_documents(kb_name, filter_criteria)
        
        return {
            "status": "success",
            "message": f"成功从知识库 {kb_name} 中删除 {result.get('deleted', 0)} 个文档"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}\n{error_trace}")

@app.get("/chunker/methods")
async def get_chunker_methods():
    """获取所有可用的分块方法"""
    try:
        ChunkMethod = None
        try:
            # 尝试绝对导入
            from llm_sass_server.core.rag_service.core.chunker.chunker_main import ChunkMethod
            print("成功导入ChunkMethod（使用绝对路径）")
        except ImportError:
            try:
                # 尝试相对导入
                from core.chunker.chunker_main import ChunkMethod
                print("成功导入ChunkMethod（使用相对路径）")
            except ImportError:
                print("无法导入ChunkMethod，使用模拟类")
                ChunkMethod = MockChunkMethod
        
        if ChunkMethod is None:
            ChunkMethod = MockChunkMethod
            
        if hasattr(ChunkMethod, 'values'):
            methods = ChunkMethod.values()
        else:
            methods = [method.value for method in ChunkMethod]
            
        return {
            "status": "success",
            "data": methods
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取分块方法失败: {str(e)}")
        print(error_trace)
        # 提供一个后备方案
        return {
            "status": "success",
            "message": "使用默认分块方法",
            "data": ["text_semantic", "semantic", "hierarchical", "markdown_header", "recursive_character", "bm25"]
        }

@app.post("/extract_text_from_file")
async def extract_text_from_file(file: UploadFile = File(...)):
    """
    从文件中提取文本，不进行分块
    """
    try:
        document_processor = DocumentProcessor()
        if not document_processor:
            raise HTTPException(status_code=500, detail="文件处理器未正确初始化")
            
        # 从原始文件名中提取文件名部分（忽略任何路径）
        orig_filename = os.path.basename(file.filename)
        print(f"开始处理文件: {orig_filename}")
        
        # 为每个文件创建唯一的临时文件名
        safe_filename = quote(orig_filename)
        temp_filename = f"temp_{str(uuid.uuid4())}_{safe_filename}"
        
        # 创建temp_files目录（如果不存在）
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_files")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # 一次性读取整个文件内容
        file_content = await file.read()
        
        # 检查文件是否为空
        if not file_content or len(file_content) == 0:
            print(f"警告: 上传的文件 '{orig_filename}' 内容为空")
            raise HTTPException(status_code=400, detail=f"上传的文件内容为空: {orig_filename}")
        
        print(f"文件 '{orig_filename}' 大小: {len(file_content)} 字节")
        
        # 保存临时文件
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        # 检查保存的临时文件是否存在
        if not os.path.exists(temp_path):
            print(f"错误: 临时文件未成功创建: {temp_path}")
            raise HTTPException(status_code=500, detail=f"临时文件创建失败: {temp_path}")
        
        # 检查临时文件大小
        temp_file_size = os.path.getsize(temp_path)
        if temp_file_size == 0:
            print(f"错误: 保存的临时文件为空: {temp_path}")
            os.remove(temp_path)  # 清理空文件
            raise HTTPException(status_code=500, detail=f"临时文件为空: {temp_path}")
        
        print(f"临时文件创建成功: {temp_path}, 大小: {temp_file_size} 字节")
        
        # 获取文件扩展名
        _, file_ext = os.path.splitext(orig_filename.lower())
        print(f"文件扩展名: {file_ext}")
        
        # 特别处理.doc文件
        if file_ext == '.doc':
            print(f"检测到.doc文件，将使用专门的处理方法: {orig_filename}")
            
        # 调用DocumentProcessor处理文件
        try:
            result = document_processor.extract_text(temp_path)
            print(f"文件处理成功，提取内容长度: {len(result.get('content', ''))}")
            
            if not result.get('content'):
                print(f"警告: 文件内容提取为空: {orig_filename}")
                raise HTTPException(status_code=400, detail=f"无法从文件中提取内容: {orig_filename}")
                
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            
            # 对于特定错误类型给出更详细的错误信息
            if "PackageNotFoundError" in str(e):
                print(f"检测到PackageNotFoundError错误，可能是.doc文件格式处理问题")
                print(f"临时文件位置: {temp_path}, 大小: {os.path.getsize(temp_path)} 字节")
                print(f"建议检查服务器是否安装了处理.doc文件所需的库")
                
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")
        
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"status": "success", "message": "文本提取成功", "data": result}
        
    except HTTPException as e:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"API处理文件时发生未预期错误: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"API处理文件时出错: {str(e)}")

@app.get("/kb/files/{kb_name}")
async def list_files_in_kb(kb_name: str):
    """获取知识库中的所有文件"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        print(f"获取知识库 {kb_name} 的文件列表")
        files = rag_service.list_files(kb_name)
        print(f"获取到的文件列表: {files}")
        
        if files is None:
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
            
        # 如果files是空列表，返回空数组而不是错误
        return {
            "status": "success",
            "data": files if files else []
        }
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"获取文件列表失败: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}\n{error_trace}")

@app.get("/kb/file/{kb_name}/{file_name}")
async def get_file_info(kb_name: str, file_name: str):
    """获取知识库中特定文件的详细信息"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        # URL解码文件名
        decoded_file_name = quote(file_name, safe='')
        
        file_info = rag_service.get_file_info(kb_name, decoded_file_name)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"文件 {file_name} 在知识库 {kb_name} 中不存在")
            
        return {
            "status": "success",
            "data": file_info
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}\n{error_trace}")

@app.delete("/kb/file/{kb_name}/{file_name}")
async def delete_file_from_kb(kb_name: str, file_name: str):
    """从知识库中删除文件"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        # URL解码文件名
        decoded_file_name = quote(file_name, safe='')
        
        success = rag_service.delete_file(kb_name, decoded_file_name)
        if success:
            return {
                "status": "success",
                "message": f"成功从知识库 {kb_name} 中删除文件 {file_name}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"文件 {file_name} 在知识库 {kb_name} 中不存在或删除失败")
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}\n{error_trace}")

@app.post("/kb/replace_file")
async def replace_file(
    kb_name: str = Form(...),
    file_to_replace: str = Form(...),
    file: UploadFile = File(...),
    chunk_config: str = Form("{}")
):
    """替换知识库中的文件"""
    try:
        # 检查必要的组件是否初始化
        document_processor = DocumentProcessor()
        task_id = str(uuid.uuid4())
        processing_tasks[task_id] = {
            "status": "processing", 
            "progress": 0, 
            "message": "准备替换文件..."
        }
        
        # 从原始文件名中提取文件名部分（忽略任何路径）
        orig_filename = os.path.basename(file.filename)
        
        print(f"开始替换文件: {file_to_replace} -> {orig_filename} 在知识库: {kb_name}")
        
        # 解析分块配置
        config = json.loads(chunk_config)
        chunk_method = config.get("method", "text_semantic")
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 200)
        
        # 处理上传的新文件
        temp_file_path = None
        try:
            # 更新处理进度
            processing_tasks[task_id] = {
                "status": "processing", 
                "progress": 10, 
                "message": f"处理替换文件: {orig_filename}"
            }
            
            # 安全处理文件名，避免特殊字符问题
            safe_filename = quote(orig_filename)
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_files")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 使用uuid生成唯一临时文件名，避免冲突
            temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{safe_filename}")
            
            # 打印文件信息
            print(f"原始文件名: {file.filename}")
            print(f"提取的文件名: {orig_filename}")
            print(f"安全处理后文件名: {safe_filename}")
            print(f"临时文件路径: {temp_file_path}")
            
            # 读取整个文件内容
            file_content = await file.read()
            
            # 检查文件是否为空
            if not file_content or len(file_content) == 0:
                raise HTTPException(status_code=400, detail=f"替换文件 {orig_filename} 为空")
            
            print(f"文件 '{orig_filename}' 大小: {len(file_content)} 字节")
            
            # 将文件内容写入临时文件
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_content)
            
            # 确认文件写入成功
            if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                raise HTTPException(status_code=500, detail="临时文件创建失败")
            
            # 定义进度回调函数
            def update_progress(progress, message):
                file_progress = 10 + int(progress * 0.8)  # 10-90%
                processing_tasks[task_id] = {
                    "status": "processing", 
                    "progress": file_progress, 
                    "message": message
                }
            
            # 使用DocumentProcessor处理文件
            documents = document_processor.process_document(
                file_path=temp_file_path,
                chunk_method=chunk_method,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                progress_callback=update_progress
            )
            
            # 替换知识库中的文件
            processing_tasks[task_id]["message"] = f"正在替换知识库中的文件..."
            success = rag_service.replace_file(kb_name, file_to_replace, documents)
            
            # 更新处理完成状态
            processing_tasks[task_id] = {
                "status": "completed", 
                "progress": 100, 
                "message": "文件替换完成"
            }
            
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"临时文件已删除: {temp_file_path}")
            
            if success:
                return {
                    "status": "success",
                    "message": f"成功替换知识库 {kb_name} 中的文件 {file_to_replace}",
                    "task_id": task_id
                }
            else:
                return {
                    "status": "error",
                    "message": f"替换知识库 {kb_name} 中的文件 {file_to_replace} 失败",
                    "task_id": task_id
                }
                
        except Exception as e:
            error_msg = f"替换文件时出错: {str(e)}"
            print(f"{error_msg}\n{traceback.format_exc()}")
            
            # 更新处理失败状态
            processing_tasks[task_id] = {
                "status": "failed", 
                "progress": 0, 
                "message": error_msg
            }
            
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    print(f"清理临时文件: {temp_file_path}")
                except:
                    pass
                    
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"替换文件失败: {str(e)}\n{error_trace}")

@app.post("/kb/load_documents")
async def load_documents(
    request: Request
):
    """
    直接加载文档到知识库，不需要上传文件
    """
    try:
        # 解析请求数据
        data = await request.json()
        kb_name = data.get("kb_name")
        documents = data.get("documents", [])
        chunk_config = data.get("chunk_config", {})
        
        if not kb_name:
            raise HTTPException(status_code=400, detail="必须提供知识库名称")
            
        if not documents:
            raise HTTPException(status_code=400, detail="必须提供文档列表")
            
        print(f"加载文档到知识库: {kb_name}, 文档数量: {len(documents)}")
        print(f"分块配置: {chunk_config}")
        
        # 解析分块配置
        chunk_method = chunk_config.get("method", "text_semantic")
        chunk_size = chunk_config.get("chunk_size", 1000)
        chunk_overlap = chunk_config.get("chunk_overlap", 200)
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        processing_tasks[task_id] = {
            "status": "processing", 
            "progress": 0, 
            "message": "准备处理文档..."
        }
        
        # 处理文档
        try:
            # 直接添加文档到知识库
            success = rag_service.add_documents(
                kb_name=kb_name,
                documents=documents,
                file_path=None,  # 这里不提供文件路径，让系统自动生成
                progress_callback=lambda progress, message: update_processing_task(task_id, progress, message)
            )
            
            # 更新处理状态
            if success:
                processing_tasks[task_id] = {
                    "status": "completed", 
                    "progress": 100, 
                    "message": f"成功加载 {len(documents)} 个文档到知识库 {kb_name}"
                }
                
                return {
                    "status": "success",
                    "message": f"成功加载 {len(documents)} 个文档到知识库 {kb_name}",
                    "task_id": task_id
                }
            else:
                processing_tasks[task_id] = {
                    "status": "failed", 
                    "progress": 0, 
                    "message": "加载文档失败"
                }
                
                return {
                    "status": "error",
                    "message": "加载文档失败",
                    "task_id": task_id
                }
                
        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = f"处理文档时出错: {str(e)}"
            print(f"{error_msg}\n{error_trace}")
            
            processing_tasks[task_id] = {
                "status": "failed", 
                "progress": 0, 
                "message": error_msg
            }
            
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        error_msg = f"加载文档请求处理失败: {str(e)}"
        print(f"{error_msg}\n{error_trace}")
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/kb/repair")
async def repair_knowledge_bases():
    """修复所有知识库的文件格式问题，将pickle格式转换为JSON格式"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        if not hasattr(rag_service.faiss_manager, 'repair_collection_files'):
            return {
                "status": "failed",
                "message": "当前版本不支持修复功能，请更新代码"
            }
        
        repair_results = rag_service.faiss_manager.repair_collection_files()
        
        return {
            "status": "success",
            "message": "知识库文件修复完成",
            "data": repair_results
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"修复知识库文件失败: {str(e)}\n{error_trace}")

@app.get("/kb/diagnose/{kb_name}")
async def diagnose_knowledge_base(kb_name: str):
    """诊断知识库的问题并报告状态"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        # 确保知识库存在
        if not rag_service.vector_db.collection_exists(kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
        
        # 获取知识库信息
        info = rag_service.vector_db.get_collection_info(kb_name)
        
        # 加载并检查索引和元数据
        if kb_name not in rag_service.vector_db.indexes:
            rag_service.vector_db._load_index(kb_name)
        if kb_name not in rag_service.vector_db.metadata:
            rag_service.vector_db._load_metadata(kb_name)
            
        # 获取诊断信息
        index = rag_service.vector_db.indexes[kb_name]
        index_size = index.ntotal
        dimension = index.d
        
        metadata = rag_service.vector_db.metadata[kb_name]
        metadata_type = type(metadata).__name__
        metadata_size = len(metadata)
        
        # 检查元数据和索引是否一致
        is_consistent = False
        if isinstance(metadata, dict):
            # 检查是否所有向量ID都有对应的元数据
            valid_keys = 0
            for i in range(index_size):
                if str(i) in metadata or i in metadata:
                    valid_keys += 1
            is_consistent = (valid_keys == index_size)
        
        # 获取文件信息
        files_info = rag_service.vector_db.list_files(kb_name)
        
        # 返回诊断结果
        return {
            "status": "success",
            "data": {
                "kb_name": kb_name,
                "index_size": index_size,
                "dimension": dimension,
                "metadata_type": metadata_type,
                "metadata_size": metadata_size,
                "is_consistent": is_consistent,
                "consistency_ratio": valid_keys / index_size if index_size > 0 else 1.0,
                "file_count": len(files_info),
                "files": files_info
            }
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"诊断知识库失败: {str(e)}\n{error_trace}")

@app.post("/kb/fix/{kb_name}")
async def fix_knowledge_base(kb_name: str):
    """修复知识库的问题"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        # 确保知识库存在
        if not rag_service.vector_db.collection_exists(kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
            
        # 尝试同步并修复
        success = rag_service.vector_db.synchronize_index_and_metadata(kb_name)
        
        if success:
            return {
                "status": "success",
                "message": f"成功修复知识库 {kb_name}"
            }
        else:
            raise HTTPException(status_code=500, detail=f"修复知识库 {kb_name} 失败")
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"修复知识库失败: {str(e)}\n{error_trace}")

@app.post("/kb/rebuild/{kb_name}")
async def rebuild_knowledge_base(kb_name: str):
    """从头重建知识库（危险操作）"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
            
        # 确保知识库存在
        if not rag_service.vector_db.collection_exists(kb_name):
            raise HTTPException(status_code=404, detail=f"知识库 {kb_name} 不存在")
            
        # 获取知识库信息
        info = rag_service.vector_db.get_collection_info(kb_name)
        
        # 备份原始文件
        index_path = rag_service.vector_db._get_index_path(kb_name)
        metadata_path = rag_service.vector_db._get_metadata_path(kb_name)
        backup_index_path = index_path + ".bak"
        backup_metadata_path = metadata_path + ".bak"
        
        import shutil
        if os.path.exists(index_path):
            shutil.copyfile(index_path, backup_index_path)
        if os.path.exists(metadata_path):
            shutil.copyfile(metadata_path, backup_metadata_path)
            
        # 删除原知识库
        rag_service.vector_db.delete_collection(kb_name)
        
        # 重新创建知识库
        dimension = info.get("dimension", 512)
        rag_service.vector_db.create_collection(kb_name, dimension=dimension, index_type="Flat")
        
        return {
            "status": "success",
            "message": f"成功重建知识库 {kb_name}，原始文件已备份"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"重建知识库失败: {str(e)}\n{error_trace}")

@app.post("/kb/search_debug")
async def search_knowledge_base_debug(query: SearchQuery):
    """在知识库中搜索内容并返回详细的调试信息"""
    try:
        if not rag_service:
            raise HTTPException(status_code=500, detail="RAG服务未正确初始化")
        
        # 获取原始搜索结果
        results = rag_service.search(
            query.kb_name,
            query.query,
            query.top_k,
            query.use_rerank,
            query.remove_duplicates
        )
        
        # 创建详细的调试信息
        debug_info = {
            "query": query.query,
            "kb_name": query.kb_name,
            "top_k": query.top_k,
            "use_rerank": query.use_rerank,
            "remove_duplicates": query.remove_duplicates,
            "results_count": len(results),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 获取知识库诊断信息
        try:
            kb_info = rag_service.vector_db.get_collection_info(query.kb_name)
            debug_info["kb_info"] = kb_info
            
            # 获取索引大小
            if query.kb_name in rag_service.vector_db.indexes:
                debug_info["index_size"] = rag_service.vector_db.indexes[query.kb_name].ntotal
            else:
                # 尝试加载索引
                rag_service.vector_db._load_index(query.kb_name)
                if query.kb_name in rag_service.vector_db.indexes:
                    debug_info["index_size"] = rag_service.vector_db.indexes[query.kb_name].ntotal
                else:
                    debug_info["index_size"] = "未知"
        except Exception as e:
            debug_info["kb_info_error"] = str(e)
        
        # 获取查询向量
        try:
            from core.embbeding_model import get_embedding
            query_vector = get_embedding(query.query)
            debug_info["query_vector_sample"] = query_vector[:5].tolist()  # 只显示前5个维度
            debug_info["query_vector_dimension"] = len(query_vector)
        except Exception as e:
            debug_info["query_vector_error"] = str(e)
        
        # 添加更详细的结果信息
        detailed_results = []
        for i, result in enumerate(results):
            detailed_result = {
                "position": i + 1,
                "text": result.get("text", "")[:200] + "..." if len(result.get("text", "")) > 200 else result.get("text", ""),
                "score": result.get("score"),
                "metadata": {
                    k: str(v)[:100] + "..." if isinstance(v, str) and len(v) > 100 else v
                    for k, v in result.get("metadata", {}).items()
                }
            }
            detailed_results.append(detailed_result)
        
        if not results:
            return {
                "status": "success",
                "message": "未找到相关内容",
                "debug_info": debug_info,
                "data": []
            }
        
        return {
            "status": "success",
            "debug_info": debug_info,
            "data": detailed_results
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"搜索知识库失败: {str(e)}\n{error_trace}")

def update_processing_task(task_id: str, progress: int, message: str):
    """更新任务处理状态"""
    if task_id in processing_tasks:
        processing_tasks[task_id] = {
            "status": "processing", 
            "progress": progress, 
            "message": message
        }

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务器"""
    import uvicorn
    try:
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        print(f"API服务器启动失败: {e}")
        traceback.print_exc()
        # 防止直接退出
        input("按Enter键退出...")

if __name__ == "__main__":
    start_api_server()