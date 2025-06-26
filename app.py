import os
import json
import traceback
import sys
import uuid
import os.path
import time
import locale
from urllib.parse import quote, unquote
from typing import List, Dict, Any, Optional, Union


# 设置默认编码为UTF-8
if sys.platform.startswith('win'):
    # 在Windows下设置控制台编码
    os.system('chcp 65001 > nul')
    # 设置Python的默认编码
    if sys.getdefaultencoding() != 'utf-8':
        import importlib
        importlib.reload(sys)
        # 在Python 3中，sys.setdefaultencoding已被移除，以下代码可能无效
        # sys.setdefaultencoding('utf-8')  

# 输出当前系统编码信息
print(f"系统默认编码: {locale.getpreferredencoding()}")
print(f"Python默认编码: {sys.getdefaultencoding()}")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
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

# 导入DeepSeek LLM模型
from core.llm.local_llm_model import get_llm_model
from core.chunker.chunker_main import ChunkMethod

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

# 添加聊天相关模型
class ChatQuery(BaseModel):
    kb_name: str
    query: str
    history: List[Dict[str, str]] = []
    top_k: int = 3
    temperature: float = 0.1

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

# 挂载静态文件目录
static_dir = os.path.join(current_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html")

# 初始化RAG服务和文件处理器
rag_service = None
document_processor = None

# 定义一个模拟的ChunkMethod类，用于在导入失败时提供备选方案
class MockChunkMethod:
    @staticmethod
    def values():
        return ["text_semantic", "semantic", "hierarchical", "markdown_header", "recursive_character", "bm25"]




@app.post("/kb/create")
async def create_knowledge_base(kb_data: KnowledgeBaseCreate):
    """创建新的知识库"""
    try:
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
        kb_list = rag_service.list_knowledge_bases()
        return {"status": "success", "data": kb_list}
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}\n{error_trace}")

@app.get("/kb/info/{kb_name}")
async def get_knowledge_base_info(kb_name: str):
    """获取指定知识库的信息"""
    try:
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        global rag_service, document_processor
        if not rag_service:
            rag_service = RAGService()
        if not document_processor:
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
                safe_filename = orig_filename
                
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
                    
                    # 检查文档处理结果
                    if not document:
                        error_msg = f"文档处理失败：{orig_filename} - 无法提取文档内容"
                        print(error_msg)
                        failed_files.append(f"{orig_filename} (文档处理失败)")
                        continue
                    
                    print(f"文档处理成功，共生成 {len(document)} 个分块")
                    
                    # 使用RAGService添加文档到知识库
                    processing_tasks[task_id]["message"] = f"添加文件 {orig_filename} 到知识库..."
                    print(f"开始添加文档到知识库: {orig_filename}")
                    
                    try:
                        success = rag_service.add_documents(
                            kb_name=kb_name,
                            documents=document
                        )
                        
                        if success:
                            print(f"文件 {orig_filename} 处理并添加成功")
                            total_docs += 1  # 增加成功处理的文档计数
                        else:
                            # 获取更详细的错误信息
                            error_msg = f"文件 {orig_filename} 添加到知识库失败 - RAGService.add_documents返回False"
                            print(error_msg)
                            
                            # 尝试获取更多诊断信息
                            try:
                                kb_info = rag_service.get_knowledge_base_info(kb_name)
                                print(f"知识库状态: {kb_info}")
                            except Exception as diag_e:
                                print(f"无法获取知识库诊断信息: {str(diag_e)}")
                            
                            failed_files.append(f"{orig_filename} (添加到知识库失败)")
                    
                    except Exception as add_e:
                        error_msg = f"添加文档到知识库时发生异常: {str(add_e)}"
                        print(error_msg)
                        traceback.print_exc()
                        failed_files.append(f"{orig_filename} (添加异常: {str(add_e)})")
                
                except Exception as e:
                    error_msg = f"处理并添加文档时出错: {str(e)}"
                    print(error_msg)
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        # 定义一个模拟的ChunkMethod类，作为后备方案
        
        ChunkMethod = ChunkMethod
            
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
        global document_processor
        if not document_processor:
            document_processor = DocumentProcessor()
            
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
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
    """从知识库中删除指定文件"""
    try:
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
        # URL解码文件名
        decoded_file_name = unquote(file_name)
        print(f"删除文件请求 - 原始文件名: {file_name}, 解码后: {decoded_file_name}")
        
        # 使用解码后的文件名进行删除操作
        success = rag_service.delete_file(kb_name, decoded_file_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"文件 {decoded_file_name} 在知识库 {kb_name} 中不存在或删除失败")
        
        return {
            "status": "success",
            "message": f"成功从知识库 {kb_name} 中删除文件 {decoded_file_name}"
        }
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
        global rag_service, document_processor
        if not rag_service:
            rag_service = RAGService()
        if not document_processor:
            document_processor = DocumentProcessor()
        
        # URL解码文件名
        decoded_file_to_replace = quote(file_to_replace, safe='')

        # 检查文件是否存在
        if not rag_service.file_exists(kb_name, decoded_file_to_replace):
            raise HTTPException(status_code=404, detail=f"文件 {file_to_replace} 在知识库 {kb_name} 中不存在")
        
        # 解析分块配置
        config = json.loads(chunk_config)
        chunk_method = config.get("method", "text_semantic")
        chunk_size = config.get("chunk_size", 1000)
        chunk_overlap = config.get("chunk_overlap", 200)
        
        print(f"分块配置: 方法={chunk_method}, 大小={chunk_size}, 重叠={chunk_overlap}")
        
        # 保存上传的文件到临时目录
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_id = str(uuid.uuid4())
        temp_path = os.path.join(temp_dir, f"{temp_file_id}_{file.filename}")
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取文件扩展名
        _, file_ext = os.path.splitext(file.filename.lower())
        print(f"文件扩展名: {file_ext}")
        
        # 处理文件内容
        try:
            # 调用DocumentProcessor处理文件
            result = document_processor.extract_text(temp_path)
            
            if not result.get('content'):
                os.remove(temp_path)  # 清理临时文件
                raise HTTPException(status_code=400, detail=f"无法从文件中提取内容: {file.filename}")
            
            # 替换知识库中的文件
            success = rag_service.replace_file(
                kb_name=kb_name,
                file_to_replace=decoded_file_to_replace,
                new_file_path=temp_path,
                new_file_name=file.filename,
                chunk_method=chunk_method,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 清理临时文件
            os.remove(temp_path)
            
            if success:
                return {
                    "status": "success",
                    "message": f"成功替换知识库 {kb_name} 中的文件 {file_to_replace}"
                }
            else:
                raise HTTPException(status_code=500, detail=f"替换文件失败")
                
        except Exception as e:
            # 确保清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"替换文件失败: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"替换文件失败: {str(e)}")
        

@app.post("/kb/chat")
async def chat_with_knowledge_base(query: ChatQuery):
    """与知识库对话"""
    try:
        # 检查必要的组件是否初始化
        rag_service = RAGService()
            
        # 检查知识库是否存在
        if not rag_service.kb_exists(query.kb_name):
            return {"status": "error", "message": f"知识库 {query.kb_name} 不存在"}
            
        # 获取历史对话格式化
        history_msgs = []
        if query.history:
            for msg in query.history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    history_msgs.append(msg)
        
        # 调用RAG服务进行知识库对话
        result = rag_service.chat_with_kb(
            kb_name=query.kb_name,
            query=query.query,
            history=history_msgs,
            top_k=query.top_k,
            temperature=query.temperature
        )
        
        return {"status": "success", "answer": result}
    except Exception as e:
        error_msg = f"与知识库对话失败: {str(e)}"
        error_trace = traceback.format_exc()
        print(f"{error_msg}\n{error_trace}")
        return {"status": "error", "message": error_msg}

@app.post("/kb/chat_stream")
async def chat_with_knowledge_base_stream(query: ChatQuery):
    """与知识库对话（流式响应）"""
    from fastapi.responses import StreamingResponse
    
    async def stream_response():
        try:
            # 检查必要的组件是否初始化
            rag_service = RAGService()
                
            # 检查知识库是否存在
            if not rag_service.kb_exists(query.kb_name):
                yield f"错误：知识库 {query.kb_name} 不存在"
                return
                
            # 获取历史对话格式化
            history_msgs = []
            if query.history:
                for msg in query.history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        history_msgs.append(msg)
            
            # 调用RAG服务进行知识库对话（流式）
            for chunk in rag_service.chat_with_kb(
                kb_name=query.kb_name,
                query=query.query,
                history=history_msgs,
                top_k=query.top_k,
                temperature=query.temperature
            ):
                yield chunk
                
        except Exception as e:
            error_msg = f"与知识库对话失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            yield error_msg
    
    return StreamingResponse(stream_response(), media_type="text/plain")

class ImportanceUpdate(BaseModel):
    kb_name: str
    file_name: str
    importance_factor: float

@app.post("/kb/set_importance")
async def set_file_importance(request: ImportanceUpdate):
    """设置文件的重要性系数"""
    try:
        # 检查必要的组件是否初始化
        rag_service = RAGService()
            
        # 检查知识库是否存在
        if not rag_service.kb_exists(request.kb_name):
            return {"status": "error", "message": f"知识库 {request.kb_name} 不存在"}
        
        # 检查参数有效性
        if request.importance_factor < 0.1 or request.importance_factor > 5.0:
            return {"status": "error", "message": "重要性系数必须在0.1到5.0之间"}

        # 检查文件是否存在
        files = rag_service.list_files(request.kb_name)
        file_exists = False
        for file in files:
            if "file_name" in file and file["file_name"] == request.file_name:
                file_exists = True
                break
        
        if not file_exists:
            return {"status": "error", "message": f"文件 {request.file_name} 不存在于知识库 {request.kb_name} 中"}
        
        # 更新文件重要性系数
        success = rag_service.update_file_importance(
            kb_name=request.kb_name,
            file_name=request.file_name,
            importance_factor=request.importance_factor
        )
        
        if success:
            return {"status": "success", "message": f"成功设置文件 {request.file_name} 的重要性系数为 {request.importance_factor}"}
        else:
            return {"status": "error", "message": "更新重要性系数失败"}
    except Exception as e:
        error_msg = f"设置文件重要性系数失败: {str(e)}"
        error_trace = traceback.format_exc()
        print(f"{error_msg}\n{error_trace}")
        return {"status": "error", "message": error_msg}

def update_processing_task(task_id: str, progress: int, message: str):
    """更新任务处理状态"""
    if task_id in processing_tasks:
        processing_tasks[task_id] = {
            "status": "processing", 
            "progress": progress, 
            "message": message
        }

def start_api_server(host: str = "0.0.0.0", port: int = 8028):
    """启动API服务器"""
    import uvicorn
    print(f"启动API服务器: {host}:{port}")
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        print(f"API服务器启动失败: {e}")
        traceback.print_exc()
        # 防止直接退出
        input("按Enter键退出...")

@app.post("/kb/fix_dimension/{kb_name}")
async def fix_dimension_mismatch(kb_name: str):
    """修复知识库的维度不匹配问题"""
    try:
        global rag_service
        if not rag_service:
            rag_service = RAGService()
            
        result = rag_service.fix_dimension_mismatch(kb_name)
        
        if result.get("status") == "success":
            return {"status": "success", "message": result["message"], "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "修复失败"))
    except Exception as e:
        error_trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"修复维度不匹配问题失败: {str(e)}\n{error_trace}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='启动API服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8028, help='服务器端口')
    args = parser.parse_args()
    
    start_api_server(host=args.host, port=args.port)