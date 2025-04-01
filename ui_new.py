import os
import gradio as gr
import pandas as pd
import traceback
import requests
import json
import time
import sys
import locale
from typing import List, Dict, Any
import subprocess
import socket

# 设置默认编码为UTF-8
if sys.platform.startswith('win'):
    # 在Windows下设置控制台编码
    os.system('chcp 65001 > nul')

# 输出当前系统编码信息
print(f"UI服务器 - 系统默认编码: {locale.getpreferredencoding()}")
print(f"UI服务器 - Python默认编码: {sys.getdefaultencoding()}")

class RAGServiceWebUI:
    """知识库管理界面类，提供基于Gradio的Web界面，通过API与后端交互"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        初始化知识库管理界面
        
        参数:
            api_base_url: API服务器的基础URL
        """
        self.api_base_url = api_base_url
        
        # 检查API服务器连接
        try:
            print(f"正在检查API服务器连接: {api_base_url}")
            response = requests.get(f"{api_base_url}/kb/list", timeout=5)
            if response.status_code == 200:
                print("API服务器连接正常")
            else:
                print(f"警告: API服务器返回非200状态码: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"警告: 无法连接到API服务器 {api_base_url}，请确保API服务器已启动")
        except Exception as e:
            print(f"警告: 检查API服务器时出错: {str(e)}")
        
    def create_kb(self, kb_name: str, dimension: int, index_type: str) -> str:
        """创建知识库"""
        if not kb_name:
            return "错误：知识库名称不能为空"
        
        try:    
            response = requests.post(
                f"{self.api_base_url}/kb/create",
                json={"kb_name": kb_name, "dimension": dimension, "index_type": index_type}
            )
            
            if response.status_code == 200:
                return f"成功创建知识库：{kb_name}"
            else:
                error_data = response.json()
                return f"创建知识库失败: {error_data.get('detail', '未知错误')}"
        except Exception as e:
            error_msg = f"创建知识库 {kb_name} 失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            return f"{error_msg}\n详细错误信息:\n{error_trace}"
    
    def list_kbs(self) -> List[str]:
        """获取知识库列表"""
        try:
            response = requests.get(f"{self.api_base_url}/kb/list")
            if response.status_code == 200:
                data = response.json()
                kb_list = data.get("data", [])
                print(f"获取到的知识库列表: {kb_list}")
                return kb_list
            else:
                print(f"获取知识库列表失败: {response.text}")
                return []
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"获取知识库列表失败: {str(e)}\n{error_trace}")
            return []
    
    def get_kb_info(self, kb_name: str) -> pd.DataFrame:
        """获取知识库信息"""
        if not kb_name:
            return pd.DataFrame()
            
        try:
            # 确保kb_name是字符串而不是列表
            if isinstance(kb_name, list):
                if not kb_name:
                    return pd.DataFrame()
                # 不只取第一个，而是处理所有知识库
                kb_names = kb_name
            else:
                kb_names = [kb_name]
                
            result_data = []
            for name in kb_names:
                print(f"获取知识库信息: {name}, 类型: {type(name)}")
                response = requests.get(f"{self.api_base_url}/kb/info/{name}")
                
                if response.status_code == 200:
                    info = response.json().get("data", {})
                    # 添加到结果列表
                    result_data.append({
                        "知识库名称": name,
                        "向量维度": info.get("dimension", "未知"),
                        "索引类型": info.get("index_type", "未知"),
                        "文档数量": info.get("vector_count", 0)
                    })
            
            # 转换为DataFrame以便在UI中显示
            if result_data:
                df = pd.DataFrame(result_data)
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"获取知识库信息失败: {str(e)}\n{error_trace}")
            return pd.DataFrame([{"错误": f"获取知识库信息失败: {str(e)}"}])
    
    def delete_kb(self, kb_name: str) -> str:
        """删除知识库"""
        if not kb_name:
            return "错误：请选择要删除的知识库"
            
        try:
            response = requests.delete(f"{self.api_base_url}/kb/delete/{kb_name}")
            
            if response.status_code == 200:
                return f"成功删除知识库：{kb_name}"
            else:
                error_data = response.json()
                return f"删除知识库失败: {error_data.get('detail', '未知错误')}"
        except Exception as e:
            error_msg = f"删除知识库 {kb_name} 失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            return f"{error_msg}"
    
    def list_files(self, kb_name: str) -> pd.DataFrame:
        """获取知识库中的文件列表"""
        if not kb_name:
            return pd.DataFrame([{"提示": "请选择知识库"}])
            
        try:
            response = requests.get(f"{self.api_base_url}/kb/files/{kb_name}")
            if response.status_code == 200:
                result = response.json()
                print(result)
                if result["status"] == "success":
                    files = result.get("data", [])
                    if not files:
                        return pd.DataFrame([{"提示": "当前知识库没有文件"}])
                    
                    # 过滤掉元数据字段
                    metadata_fields = ['_created_at', '_last_updated', '_file_count', '_vector_count']
                    filtered_files = []
                    for file in files:
                        if isinstance(file, dict) and 'file_name' in file:
                            if file.get('file_name') not in metadata_fields:
                                filtered_files.append(file)
                    
                    if not filtered_files:
                        return pd.DataFrame([{"提示": "当前知识库没有文件"}])
                    
                    # 整理文件数据
                    file_data = []
                    for i, file in enumerate(filtered_files):
                        file_name = file.get("file_name", "")
                        if not file_name and "file_path" in file:
                            file_name = os.path.basename(file.get("file_path", ""))
                            
                        file_data.append({
                            "序号": i + 1,
                            "文件名": file_name,
                            "文件路径": file.get("file_path", ""),
                            "文件大小": self._format_file_size(file.get("file_size", 0)),
                            "块数量": file.get("chunks_count", 0),
                            "重要性系数": file.get("importance_coefficient", 0),
                            "添加时间": file.get("add_time", "")
                        })
                    
                    df = pd.DataFrame(file_data)
                    return df
                else:
                    return pd.DataFrame([{"错误": result.get("message", "获取文件列表失败")}])
            else:
                return pd.DataFrame([{"错误": f"获取文件列表失败: HTTP {response.status_code}"} ])
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"获取文件列表失败: {str(e)}\n{error_trace}")
            return pd.DataFrame([{"错误": f"获取文件列表失败: {str(e)}"} ])
    
    def get_file_details(self, kb_name: str, file_path: str) -> pd.DataFrame:
        """获取文件详情信息"""
        if not kb_name or not file_path:
            return pd.DataFrame([{"提示": "请选择知识库和文件"}])
            
        try:
            # 提取文件名
            file_name = os.path.basename(file_path)
            
            response = requests.get(f"{self.api_base_url}/kb/file/{kb_name}/{file_name}")
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    file_info = result.get("data", {})
                    
                    # 整理文件信息
                    details = []
                    details.append({"属性": "文件名", "值": file_info.get("file_name", file_name)})
                    details.append({"属性": "文件路径", "值": file_info.get("file_path", file_path)})
                    details.append({"属性": "文件大小", "值": self._format_file_size(file_info.get("file_size", 0))})
                    details.append({"属性": "块数量", "值": str(file_info.get("chunks_count", 0))})
                    details.append({"属性": "添加时间", "值": file_info.get("add_time", "")})
                    
                    if "metadata" in file_info:
                        for key, value in file_info["metadata"].items():
                            details.append({"属性": key, "值": str(value)})
                    
                    return pd.DataFrame(details)
                else:
                    return pd.DataFrame([{"错误": result.get("message", "获取文件详情失败")}])
            else:
                return pd.DataFrame([{"错误": f"获取文件详情失败: HTTP {response.status_code}"} ])
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"获取文件详情失败: {str(e)}\n{error_trace}")
            return pd.DataFrame([{"错误": f"获取文件详情失败: {str(e)}"} ])
    
    def delete_file(self, kb_name: str, file_path: str) -> str:
        """从知识库中删除文件"""
        if not kb_name or not file_path:
            return "错误：请选择知识库和文件"
            
        try:
            # 提取文件名
            file_name = os.path.basename(file_path)
            
            response = requests.delete(f"{self.api_base_url}/kb/file/{kb_name}/{file_name}")
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    return f"成功从知识库 {kb_name} 中删除文件 {file_name}"
                else:
                    return f"删除文件失败: {result.get('message', '未知错误')}"
            else:
                error_data = response.json()
                return f"删除文件失败: {error_data.get('detail', f'HTTP {response.status_code}')}"
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"删除文件失败: {str(e)}\n{error_trace}")
            return f"删除文件失败: {str(e)}"
    
    def replace_file(self, kb_name: str, file_to_replace: str, file_path: str, chunk_method: str, chunk_size: int, chunk_overlap: int) -> str:
        """替换知识库中的文件"""
        if not kb_name or not file_to_replace or not file_path:
            return "错误：知识库、要替换的文件和新文件都不能为空"
            
        try:
            # 打开文件
            with open(file_path, "rb") as file:
                # 创建分块配置
                chunk_config = {
                    "method": chunk_method,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                }
                
                # 创建表单数据
                form_data = {
                    "kb_name": kb_name,
                    "file_to_replace": file_to_replace,
                    "chunk_config": json.dumps(chunk_config)
                }
                
                # 添加文件
                file_name = os.path.basename(file_path)
                form_files = [("file", (file_name, file, "application/octet-stream"))]
                
                # 发送请求
                response = requests.post(
                    f"{self.api_base_url}/kb/replace_file",
                    data=form_data,
                    files=form_files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["status"] == "success":
                        return f"成功替换文件: {result.get('message', '替换成功')}"
                    else:
                        return f"替换文件失败: {result.get('message', '未知错误')}"
                else:
                    error_data = response.json()
                    return f"替换文件失败: {error_data.get('detail', f'HTTP {response.status_code}')}"
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"替换文件失败: {str(e)}\n{error_trace}")
            return f"替换文件失败: {str(e)}"
    
    def set_importance_coefficient(self, kb_name: str, file_path: str, importance_factor: float) -> str:
        """设置文件的重要性系数"""
        if not kb_name or not file_path:
            return "错误：知识库名称和文件路径不能为空"
        
        try:
            # 提取文件名
            file_name = os.path.basename(file_path)
            
            # 发送请求
            response = requests.post(
                f"{self.api_base_url}/kb/set_importance",
                json={
                    "kb_name": kb_name,
                    "file_name": file_name,
                    "importance_factor": importance_factor
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    return f"成功设置文件 {file_name} 的重要性系数为 {importance_factor}"
                else:
                    return f"设置重要性系数失败: {result.get('message', '未知错误')}"
            else:
                error_data = response.json()
                return f"设置重要性系数失败: {error_data.get('detail', f'HTTP {response.status_code}')}"
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"设置重要性系数失败: {str(e)}\n{error_trace}")
            return f"设置重要性系数失败: {str(e)}"
    
    def _format_file_size(self, bytes: int) -> str:
        """格式化文件大小"""
        if bytes == 0:
            return "0 Bytes"
            
        sizes = ["Bytes", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes >= 1024 and i < len(sizes) - 1:
            bytes /= 1024
            i += 1
            
        return f"{bytes:.2f} {sizes[i]}"

    def upload_files(self, kb_name: str, files, chunk_size: int, chunk_overlap: int):
        """上传文件到知识库"""
        if not kb_name or not files:
            return "", "知识库名称和文件不能为空"
            
        try:
            # 创建表单数据
            form_data = {
                "kb_name": kb_name
            }
            
            # 创建分块配置
            chunk_method = "text_semantic"
            
            chunk_config = {
                "method": chunk_method,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
            
            # 添加分块配置
            form_data["chunk_config"] = json.dumps(chunk_config)
            
            # 添加文件
            form_files = []
            for file in files:
                # 确保文件对象是打开的并且指针在开始位置
                if hasattr(file, 'seek'):
                    file.seek(0)
                # 使用文件名和文件对象创建元组
                form_files.append(("files", (file.name, open(file.name, "rb"), "application/octet-stream")))
            
            # 发送API请求
            response = requests.post(
                f"{self.api_base_url}/kb/upload",
                data=form_data,
                files=form_files
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 如果返回了任务ID，则创建进度监控
                if "task_id" in result:
                    task_id = result["task_id"]
                    
                    # 创建进度条组件
                    progress_html = f"""
                    <div class="progress-container">
                        <div class="progress-bar" style="width: 0%" id="progress-bar">0%</div>
                    </div>
                    <div id="progress-message">初始化中...</div>
                    
                    <script>
                    // 更新进度条函数
                    function updateProgress(percent, message) {{
                        document.getElementById('progress-bar').style.width = percent + '%';
                        document.getElementById('progress-bar').innerText = percent + '%';
                        document.getElementById('progress-message').innerText = message;
                    }}
                    
                    // 轮询进度API
                    async function pollProgress() {{
                        try {{
                            const response = await fetch('{self.api_base_url}/kb/progress/{task_id}');
                            if (response.ok) {{
                                const data = await response.json();
                                const progressData = data.data;
                                
                                // 更新进度条
                                updateProgress(progressData.progress, progressData.message);
                                
                                // 判断是否完成或出错
                                if (progressData.status === 'completed') {{
                                    clearInterval(pollInterval);
                                    updateProgress(100, '处理完成!');
                                    document.getElementById('progress-message').style.color = '#4CAF50';
                                }} else if (progressData.status === 'failed') {{
                                    clearInterval(pollInterval);
                                    document.getElementById('progress-message').style.color = '#F44336';
                                }}
                            }}
                        }} catch (error) {{
                            console.error('轮询进度出错:', error);
                        }}
                    }}
                    
                    // 开始轮询
                    const pollInterval = setInterval(pollProgress, 1000);
                    pollProgress(); // 立即执行一次
                    </script>
                    """
                    
                    # 处理结果
                    result_message = ""
                    if result["status"] == "success":
                        result_message = result["message"]
                    elif result["status"] == "partial_success":
                        failed_files = "\n".join(result["failed_files"])
                        result_message = f"{result['message']}\n失败文件:\n{failed_files}"
                    else:
                        result_message = f"上传失败: {result.get('message', '未知错误')}"
                    
                    return progress_html, result_message
                
                # 如果没有任务ID，直接显示结果
                if result["status"] == "success":
                    return "", result["message"]
                elif result["status"] == "partial_success":
                    failed_files = "\n".join(result["failed_files"])
                    return "", f"{result['message']}\n失败文件:\n{failed_files}"
                else:
                    return "", f"上传失败: {result.get('message', '未知错误')}"
            else:
                return "", f"上传失败: HTTP {response.status_code} - {response.text}"
                
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"上传时出错: {str(e)}\n{error_trace}")
            return "", f"上传时出错: {str(e)}"
    
    def search_kb(self, kb_name: str, query: str, top_k: int, use_rerank: bool) -> pd.DataFrame:
        """搜索知识库"""
        if not kb_name:
            return pd.DataFrame([{"错误": "请选择知识库"}])
        if not query:
            return pd.DataFrame([{"错误": "请输入搜索内容"}])
            
        try:
            # 构建搜索请求
            search_params = {
                    "kb_name": kb_name,
                    "query": query,
                    "top_k": top_k,
                    "use_rerank": use_rerank
                }
            
            print(f"发起搜索请求: {search_params}")
            
            # 先尝试使用请求的参数
            response = requests.post(
                f"{self.api_base_url}/kb/search",
                json=search_params,
                timeout=30  # 增加超时时间
            )
            
            # 检查是否为rerank相关错误
            rerank_failed = False
            if response.status_code != 200:
                error_data = response.json() if response.content else {"detail": f"HTTP错误: {response.status_code}"}
                error_msg = error_data.get("detail", "未知错误")
                
                # 检查是否为rerank相关错误
                if "rerank" in error_msg.lower() or (use_rerank and "failed" in error_msg.lower()):
                    print(f"检测到重排序相关错误: {error_msg}，尝试关闭重排序")
                    rerank_failed = True
                    
                    # 重试请求，但关闭rerank
                    search_params["use_rerank"] = False
                    response = requests.post(
                        f"{self.api_base_url}/kb/search",
                        json=search_params,
                        timeout=30
                    )
                else:
                    # 其他类型的错误，直接返回错误信息
                    return pd.DataFrame([{"错误": f"搜索失败: {error_msg}"}])
            
            if response.status_code == 200:
                result = response.json()
                print(f"搜索结果: {result}")
                
                # 检查是否有消息提示未找到内容
                if "message" in result and "未找到相关内容" in result["message"]:
                    if rerank_failed:
                        return pd.DataFrame([{"提示": "重排序失败且未找到相关内容。已自动关闭重排序功能。"}])
                    else:
                        return pd.DataFrame([{"提示": "未找到相关内容"}])
                
                data = result.get("data", [])
                if not data:
                    if rerank_failed:
                        return pd.DataFrame([{"提示": "重排序失败，已关闭重排序功能，但仍未找到相关内容。"}])
                    elif use_rerank:
                        return pd.DataFrame([{"提示": "重排序后未找到相关内容，请尝试关闭重排序或修改搜索条件"}])
                    else:
                        return pd.DataFrame([{"提示": "未找到相关内容"}])
                
                # 打印每个结果项的详细内容，帮助调试
                for i, item in enumerate(data):
                    print(f"结果项 #{i+1}:")
                    for key, value in item.items():
                        if key != "metadata":
                            print(f"  {key}: {value[:100] if isinstance(value, str) else value}")
                        else:
                            print(f"  metadata: {value}")
                
                # 转换为DataFrame，并处理内容格式
                df_data = []
                for i, item in enumerate(data):
                    # 查找内容字段 (优先尝试content，然后text)
                    content = ""
                    if "content" in item:
                        content = item["content"]
                    elif "text" in item:
                        content = item["text"]
                    
                    if not content and isinstance(item, str):
                        # 如果整个项是字符串，就把它当作内容
                        content = item
                    
                    # 每70个字符左右添加换行符，使显示更清晰
                    formatted_text = '\n'.join([content[j:j+70] for j in range(0, len(content), 70)]) if content else ""
                    
                    # 如果重排序失败但普通搜索成功，添加提示
                    note = ""
                    if rerank_failed and i == 0:
                        note = "（注意：重排序失败，已关闭重排序）"
                    
                    # 尝试获取元数据中的来源信息
                    metadata = item.get("metadata", {})
                    source = "未知"
                    if isinstance(metadata, dict):
                        # 尝试多种可能的来源字段
                        if "source" in metadata:
                            source = metadata["source"]
                        elif "file_name" in metadata:
                            source = metadata["file_name"]
                        elif "document_id" in metadata:
                            source = metadata["document_id"]
                    
                    df_data.append({
                        "序号": i + 1,
                        "内容": formatted_text + note,
                        "相关度": round(item.get("score", 0), 3),
                        "来源": source
                    })
                
                # 设置DataFrame的样式
                df = pd.DataFrame(df_data)
                return df
            else:
                error_data = response.json()
                return pd.DataFrame([{"错误": f"搜索失败: {error_data.get('detail', '未知错误')}"}])
        except Exception as e:
            error_msg = f"搜索知识库失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            
            # 如果是因为重排序失败，提供更明确的提示
            if "rerank" in str(e).lower():
                return pd.DataFrame([{"错误": f"重排序失败: {str(e)}，请尝试关闭重排序选项"}])
            else:
                return pd.DataFrame([{"错误": error_msg}])
    
    def chat_with_kb(self, kb_name: str, query: str, history: List[List[str]], top_k: int, temperature: float) -> tuple:
        """与知识库对话"""
        if not kb_name:
            return "请选择知识库", history
        if not query:
            return "请输入问题", history
            
        try:
            # 构建历史记录格式
            formatted_history = []
            for h in history:
                if len(h) == 2:  # 确保历史记录格式正确
                    formatted_history.append({"role": "user", "content": h[0]})
                    formatted_history.append({"role": "assistant", "content": h[1]})
            
            # 发送请求
            response = requests.post(
                f"{self.api_base_url}/kb/chat",
                json={
                    "kb_name": kb_name,
                    "query": query,
                    "history": formatted_history,
                    "top_k": top_k,
                    "temperature": temperature
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "未能获取回答")
                # 更新对话历史
                history.append([query, answer])
                return answer, history
            else:
                error_data = response.json()
                error_msg = f"对话失败: {error_data.get('detail', '未知错误')}"
                history.append([query, error_msg])
                return error_msg, history
        except Exception as e:
            error_msg = f"与知识库对话失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            history.append([query, error_msg])
            return error_msg, history
    
    def launch(self, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
        """启动Web UI"""
        # 自定义CSS
        custom_css = """
        /* 全局样式 */
        body {
            font-family: 'Source Sans Pro', 'Helvetica Neue', Arial, sans-serif;
            background-color: #f9f9f9;
        }
        
        /* 修复Gradio下拉框不可选择的问题 */
        .gradio-dropdown {
            pointer-events: auto !important;
            z-index: 200 !important;
        }
        
        select.gr-box {
            pointer-events: auto !important;
            opacity: 1 !important;
            z-index: 200 !important;
        }
        
        /* 确保下拉菜单显示在上层 */
        .gr-form > div[data-testid="dropdown"] {
            z-index: 100 !important;
        }
        
        /* 确保按钮可点击 */
        button, .gr-button {
            pointer-events: auto !important;
            cursor: pointer !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 50 !important;
        }
        
        /* 上传按钮特别修复 */
        button[aria-label="上传文件"] {
            pointer-events: auto !important;
            cursor: pointer !important;
            z-index: 100 !important;
        }
        
        /* 修复Radio按钮组无法选择的问题 - 强化版 */
        .gr-radio-group {
            pointer-events: auto !important;
            z-index: 100 !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 8px !important;
        }
        
        /* 特别强调单选按钮的交互性 */
        input[type="radio"] {
            pointer-events: auto !important;
            opacity: 1 !important;
            cursor: pointer !important;
            margin-right: 5px !important;
            position: static !important;
            width: auto !important;
            height: auto !important;
            min-width: 16px !important;
            min-height: 16px !important;
            appearance: auto !important;
            -webkit-appearance: radio !important;
            display: inline-block !important;
            z-index: 300 !important;
        }
        
        /* 确保标签可以正确点击 */
        .gr-radio-group label {
            pointer-events: auto !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            margin: 5px 0 !important;
            padding: 8px !important;
            border-radius: 4px !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid #ddd !important;
            position: relative !important;
            z-index: 200 !important;
        }
        
        .gr-radio-group label:hover {
            background-color: rgba(74, 111, 165, 0.1) !important;
            border-color: #4a6fa5 !important;
        }
        
        /* 强制垂直布局 */
        .gr-radio-group[orientation="vertical"] {
            flex-direction: column !important;
        }
        
        /* 标题样式 */
        h1, h2, h3 {
            font-weight: 600;
            color: #333;
        }
        
        /* 主容器样式 */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        /* 选项卡样式 */
        .tab-nav {
            background-color: #4a6fa5;
            border-radius: 8px 8px 0 0;
            padding: 5px;
        }
        
        .tab-nav button {
            color: #fff;
            background-color: transparent;
            border: none;
            border-radius: 5px;
            margin: 5px;
            padding: 10px 15px;
            transition: background-color 0.3s;
        }
        
        .tab-nav button.selected {
            background-color: #2c4c7c;
            font-weight: bold;
        }
        
        /* 按钮样式 */
        button.primary {
            background-color: #4a6fa5;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
            font-weight: 600;
            transition: background-color 0.3s;
        }
        
        button.primary:hover {
            background-color: #2c4c7c;
        }
        
        /* 输入框样式 */
        input, select, textarea {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 8px 12px;
            background-color: #f9f9f9;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            border-color: #4a6fa5;
            box-shadow: 0 0 0 2px rgba(74, 111, 165, 0.2);
            outline: none;
        }
        
        /* 卡片样式 */
        .gr-box {
            border-radius: 8px;
            border: 1px solid #e6e6e6;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            background-color: white;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        /* 聊天容器 */
        .chat-container {
            height: 500px;
            overflow-y: auto;
            border: 1px solid #e6e6e6;
            border-radius: 8px;
            padding: 10px;
            background-color: #f9f9f9;
        }
        
        /* 进度条样式 */
        .progress-container {
            width: 100%;
            background-color: #f1f1f1;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .progress-bar {
            height: 20px;
            background-color: #4a6fa5;
            border-radius: 5px;
            text-align: center;
            color: white;
            font-weight: bold;
            line-height: 20px;
            transition: width 0.3s;
        }
        
        /* 表格样式 */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background-color: white;
        }
        
        table th {
            background-color: #4a6fa5;
            color: white !important;  /* 强制白色文本 */
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #3a5a8a;
        }
        
        table td {
            padding: 8px 10px;
            border-bottom: 1px solid #ddd;
            color: #333;  /* 深色文本 */
            background-color: #f9f9f9;
        }
        
        table tr:nth-child(even) td {
            background-color: #f2f2f2;
        }
        
        /* 颜色主题 */
        .theme-primary { color: #4a6fa5; }
        .theme-secondary { color: #2c4c7c; }
        .theme-accent { color: #66bb6a; }
        .theme-warning { color: #ffa726; }
        .theme-error { color: #ef5350; }
        
        /* 强制表格样式 - 确保标题可见 */
        .gr-dataframe table th,
        .gradio-container table th,
        table.gr-table th,
        div.gradio-table th,
        div.gr-table-container th {
            background-color: #4a6fa5 !important;
            color: white !important;
            font-weight: bold !important;
            text-shadow: none !important;
            border: 1px solid #3a5a8a !important;
            opacity: 1 !important;
            padding: 10px !important;
        }
        
        /* 确保表格单元格内容可见 */
        .gr-dataframe table td,
        .gradio-container table td,
        table.gr-table td,
        div.gradio-table td,
        div.gr-table-container td {
            color: #333 !important;
            background-color: #f9f9f9 !important;
            padding: 8px 10px !important;
            border: 1px solid #ddd !important;
            text-align: left !important;
        }
        
        /* 隔行变色以提高可读性 */
        .gr-dataframe table tr:nth-child(2n) td,
        .gradio-container table tr:nth-child(2n) td,
        table.gr-table tr:nth-child(2n) td,
        div.gradio-table tr:nth-child(2n) td,
        div.gr-table-container tr:nth-child(2n) td {
            background-color: #f0f0f0 !important;
        }
        
        /* 确保表格内所有文本元素可见 */
        .gr-dataframe th span, 
        .gr-dataframe td span,
        .gradio-container th span,
        .gradio-container td span,
        table.gr-table th span,
        table.gr-table td span {
            color: inherit !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        """
        
        # 添加修复下拉框问题的CSS和JS
        custom_css += """
        /* 修复下拉框显示问题 */
        .gr-dropdown {
            position: relative;
            z-index: 100;
        }
        
        .gr-dropdown-container {
            position: relative;
            z-index: 101;
        }
        
        /* 确保下拉框可点击 */
        select.gr-box {
            pointer-events: auto !important;
            opacity: 1 !important;
            cursor: pointer !important;
        }
        """
        
        # 添加自定义JS以确保下拉框正常工作
        custom_js = """
        function fixDropdowns() {
            // 查找所有下拉框元素
            const dropdowns = document.querySelectorAll('select.gr-box');
            
            // 确保它们可以交互
            dropdowns.forEach(dropdown => {
                dropdown.style.pointerEvents = 'auto';
                dropdown.style.opacity = '1';
                dropdown.style.cursor = 'pointer';
                
                // 移除可能阻止交互的属性
                dropdown.removeAttribute('disabled');
                dropdown.removeAttribute('readonly');
            });
            
            console.log('已修复下拉框交互问题');
        }
        
        function fixRadioButtons() {
            // 查找所有单选按钮和它们的标签
            const radioInputs = document.querySelectorAll('input[type="radio"]');
            const radioLabels = document.querySelectorAll('.gr-radio-group label');
            
            console.log('找到 ' + radioInputs.length + ' 个Radio按钮');
            
            // 确保单选按钮可以交互
            radioInputs.forEach((radio, index) => {
                // 强制设置样式和属性
                radio.style.pointerEvents = 'auto';
                radio.style.opacity = '1';
                radio.style.cursor = 'pointer';
                radio.style.position = 'relative';
                radio.style.zIndex = '200';
                radio.style.display = 'inline-block';
                
                // 移除可能阻止交互的属性
                radio.disabled = false;
                radio.readOnly = false;
            });
            
            // 确保标签可以交互
            radioLabels.forEach((label, index) => {
                // 强制设置样式
                label.style.pointerEvents = 'auto';
                label.style.cursor = 'pointer';
                label.style.position = 'relative';
                label.style.zIndex = '150';
            });
            
            // 确保不会干扰上传按钮和其他功能按钮
            document.querySelectorAll('button').forEach(button => {
                if (!(button.onclick && button.onclick.toString().includes('setChunkMethod') ||
                    button.onclick && button.onclick.toString().includes('setLoadKbChunkMethod') ||
                    button.onclick && button.onclick.toString().includes('setReplaceChunkMethod'))) {
                    // 为非备用按钮恢复正常样式和功能
                    button.style.pointerEvents = 'auto';
                    button.style.cursor = 'pointer';
                    button.style.zIndex = 'auto';
                }
            });
            
            console.log('已修复单选按钮交互问题，并保留其他按钮功能');
        }
        
        // 延迟一点时间执行修复，避免与Gradio初始化冲突
        setTimeout(function() {
            console.log('开始执行UI修复');
            fixDropdowns();
            fixRadioButtons();
        }, 1000);
        """
        
        # 添加控制列宽比例的CSS
        custom_css += """
        /* 控制表格列宽比例 */
        .gr-dataframe table col:nth-child(1),
        table.gr-table col:nth-child(1) {
            width: 10% !important; /* 序号列 */
        }

        .gr-dataframe table col:nth-child(2),
        table.gr-table col:nth-child(2) {
            width: 60% !important; /* 内容列 - 给最大宽度 */
        }

        .gr-dataframe table col:nth-child(3),
        table.gr-table col:nth-child(3) {
            width: 15% !important; /* 相关度列 */
        }

        .gr-dataframe table col:nth-child(4),
        table.gr-table col:nth-child(4) {
            width: 15% !important; /* 来源列 */
        }

        /* 确保内容列有足够的行高 */
        .gr-dataframe td:nth-child(2),
        table.gr-table td:nth-child(2) {
            min-height: 100px !important;
            height: auto !important;
            white-space: pre-wrap !important;
            word-break: break-word !important;
            vertical-align: top !important;
        }

        /* 让其他列靠上对齐并控制行高 */
        .gr-dataframe td,
        table.gr-table td {
            vertical-align: top !important;
            padding-top: 8px !important;
            line-height: 1.4 !important;
        }

        /* 强制应用表格布局算法，防止自动调整 */
        .gr-dataframe table,
        table.gr-table {
            table-layout: fixed !important;
            width: 100% !important;
        }
        """
        
        with gr.Blocks(css=custom_css, js=custom_js, title="知识库检索增强生成(RAG)服务") as demo:
            gr.Markdown(
                """
                # 📚 知识库检索增强生成(RAG)服务
                
                这是一个基于向量数据库的知识库检索系统，支持多种文件格式的导入、分块和检索。
                """
            )
            
            with gr.Tabs() as tabs:
                with gr.TabItem("💾 知识库管理", id="kb_management"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 创建知识库")
                                kb_name = gr.Textbox(label="知识库名称", placeholder="输入新知识库名称...", lines=1)
                                dimension = gr.Slider(label="向量维度", minimum=128, maximum=1024, step=128, value=512)
                                index_type = gr.Dropdown(label="索引类型", choices=["Flat", "IVF", "HNSW"], value="Flat")
                                with gr.Row():
                                    create_kb_btn = gr.Button("创建知识库", variant="primary")
                                    refresh_kb_btn = gr.Button("刷新列表", variant="secondary")
                                
                                create_kb_result = gr.Textbox(label="创建结果", lines=1, interactive=False)
                            
                            with gr.Box():
                                gr.Markdown("### 删除知识库")
                                kb_to_delete = gr.Dropdown(label="选择要删除的知识库", choices=[])
                                delete_kb_btn = gr.Button("删除知识库", variant="stop")
                                delete_kb_result = gr.Textbox(label="删除结果", lines=1, interactive=False)
                        
                        with gr.Column(scale=2):
                            with gr.Box():
                                gr.Markdown("### 知识库列表")
                                kb_list = gr.Dataframe(
                                    headers=["知识库名称", "向量维度", "索引类型", "文档数量"],
                                    datatype=["str", "number", "str", "number"],
                                    row_count=10
                                )
                                
                                # 新增：添加选择知识库下拉菜单
                                kb_info_dropdown = gr.Dropdown(label="选择知识库查看详情", choices=[])
                                
                                kb_info_result = gr.Dataframe(
                                    headers=["属性", "值"],
                                    datatype=["str", "str"],
                                    row_count=5,
                                    label="知识库详细信息"
                                )
                    
                    with gr.Box():
                        gr.Markdown("### 上传文件")
                        with gr.Tabs() as upload_tabs:
                            with gr.TabItem("单文件上传", id="single_upload"):
                                with gr.Row():
                                    upload_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                    upload_files = gr.File(label="选择文件", file_count="multiple")
                                
                                with gr.Row():
                                    chunk_method = gr.Radio(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic",
                                        interactive=True,
                                        elem_id="chunk_method_radio",
                                        container=True,
                                        orientation="vertical"
                                    )
                                chunk_method_info = gr.HTML("""
                                <div style="font-size: 0.8em; color: #666; margin-top: 0.5em;">
                                    <b>分块方法说明：</b><br>
                                    • <b>text_semantic</b>: 结合语义和文本特征的分块，适用于大多数文本文档<br>
                                    • <b>semantic</b>: 纯语义分块，基于内容相似性，适合连贯性强的文本<br>
                                    • <b>hierarchical</b>: 层次化分块，适用于有章节结构的文档<br>
                                    • <b>markdown_header</b>: 基于Markdown标题的分块，适用于Markdown文档<br>
                                    • <b>recursive_character</b>: 递归字符分块，适用于无明显结构的纯文本<br>
                                    • <b>bm25</b>: 基于BM25算法的分块，适合信息检索场景
                                </div>
                                """)
                                
                                with gr.Row():
                                    chunk_size = gr.Slider(label="分块大小", minimum=200, maximum=2000, step=100, value=1000)
                                    chunk_overlap = gr.Slider(label="分块重叠", minimum=0, maximum=500, step=50, value=200)
                                
                                upload_btn = gr.Button("上传文件", variant="primary", elem_id="upload_file_button")
                                # 添加上传按钮特别处理的JavaScript
                                gr.HTML("""
                                <script>
                                // 确保上传按钮功能正常
                                document.addEventListener('DOMContentLoaded', function() {
                                    // 等待Gradio完全加载
                                    setTimeout(function() {
                                        const uploadBtn = document.getElementById('upload_file_button');
                                        if (uploadBtn) {
                                            console.log('找到上传按钮，确保其可点击');
                                            // 移除可能阻止点击的样式
                                            uploadBtn.style.pointerEvents = 'auto';
                                            uploadBtn.style.cursor = 'pointer';
                                            uploadBtn.style.opacity = '1';
                                            uploadBtn.style.zIndex = '500';
                                            
                                            // 添加visual feedback
                                            uploadBtn.addEventListener('mouseover', function() {
                                                this.style.backgroundColor = '#3a5c8b';
                                            });
                                            uploadBtn.addEventListener('mouseout', function() {
                                                this.style.backgroundColor = '';
                                            });
                                            
                                            console.log('上传按钮已设置为可点击状态');
                                        } else {
                                            console.log('未找到上传按钮');
                                        }
                                    }, 1500);
                                });
                                </script>
                                """)
                                # 添加进度显示区域
                                upload_progress = gr.HTML("", label="上传进度")
                                upload_result = gr.Textbox(label="上传结果", lines=5, interactive=False)
                                
                            with gr.TabItem("导入知识库", id="load_knowledge_base"):
                                with gr.Row():
                                    load_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                    load_kb_file = gr.File(label="选择数据文件", file_count="single")
                                
                                gr.Markdown("### 分块设置")
                                with gr.Row():
                                    load_kb_chunk_method = gr.Radio(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic",
                                        interactive=True,
                                        elem_id="load_kb_chunk_method_radio",
                                        container=True,
                                        orientation="vertical"
                                    )
                                load_kb_chunk_method_info = gr.HTML("""
                                <div style="font-size: 0.8em; color: #666; margin-top: 0.5em;">
                                    <b>分块方法说明：</b><br>
                                    • <b>text_semantic</b>: 结合语义和文本特征的分块，适用于大多数文本文档<br>
                                    • <b>semantic</b>: 纯语义分块，基于内容相似性，适合连贯性强的文本<br>
                                    • <b>hierarchical</b>: 层次化分块，适用于有章节结构的文档<br>
                                    • <b>markdown_header</b>: 基于Markdown标题的分块，适用于Markdown文档<br>
                                    • <b>recursive_character</b>: 递归字符分块，适用于无明显结构的纯文本<br>
                                    • <b>bm25</b>: 基于BM25算法的分块，适合信息检索场景
                                </div>
                                
                                <div style="margin-top: 10px; border: 1px dashed #ccc; padding: 8px; border-radius: 5px;">
                                    <p><b>如果上方的分块方法无法选择，请使用下面的备用按钮：</b></p>
                                    <div style="display: flex; flex-direction: column; gap: 5px;">
                                        <button onclick="setChunkMethod('text_semantic')" style="padding: 5px; background: #e6f7ff; border: 1px solid #91d5ff; border-radius: 4px; cursor: pointer;">选择: text_semantic</button>
                                        <button onclick="setChunkMethod('semantic')" style="padding: 5px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">选择: semantic</button>
                                        <button onclick="setChunkMethod('hierarchical')" style="padding: 5px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">选择: hierarchical</button>
                                        <button onclick="setChunkMethod('markdown_header')" style="padding: 5px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">选择: markdown_header</button>
                                        <button onclick="setChunkMethod('recursive_character')" style="padding: 5px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">选择: recursive_character</button>
                                        <button onclick="setChunkMethod('bm25')" style="padding: 5px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">选择: bm25</button>
                                    </div>
                                </div>
                                
                                <script>
                                function setChunkMethod(method) {
                                    // 找到目标Radio组件的所有Radio按钮
                                    const radioButtons = document.querySelectorAll('#chunk_method_radio input[type="radio"]');
                                    
                                    // 遍历并设置对应值的按钮为选中状态
                                    radioButtons.forEach(radio => {
                                        if (radio.value === method) {
                                            radio.checked = true;
                                            // 触发change事件
                                            const event = new Event('change', {bubbles: true});
                                            radio.dispatchEvent(event);
                                            
                                            // 更新按钮样式
                                            document.querySelectorAll('button[onclick^="setChunkMethod"]').forEach(btn => {
                                                btn.style.background = '#fff';
                                                btn.style.borderColor = '#d9d9d9';
                                            });
                                            
                                            // 高亮选中的按钮
                                            document.querySelector(`button[onclick="setChunkMethod('${method}')"]`).style.background = '#e6f7ff';
                                            document.querySelector(`button[onclick="setChunkMethod('${method}')"]`).style.borderColor = '#91d5ff';
                                        }
                                    });
                                    
                                    console.log('通过备用按钮设置分块方法为: ' + method);
                                }
                                </script>
                                """)
                                
                                with gr.Row():
                                    load_kb_chunk_size = gr.Slider(label="分块大小", minimum=200, maximum=2000, step=100, value=1000)
                                    load_kb_chunk_overlap = gr.Slider(label="分块重叠", minimum=0, maximum=500, step=50, value=200)
                                
                                with gr.Row():
                                    load_kb_btn = gr.Button("导入知识库", variant="primary", elem_id="load_kb_button")
                                    load_kb_format_info = gr.HTML("""
                                    <div style="font-size: 0.8em; color: #666; margin-top: 0.5em;">
                                        <b>支持的数据格式：</b><br>
                                        • <b>JSON文件</b>: 包含文档数组，每个文档需要有text字段<br>
                                        • <b>CSV/TSV文件</b>: 包含文本列，可选包含元数据列<br>
                                        • <b>XML文件</b>: 包含文档标签的结构化XML<br>
                                        • <b>文本文件(.txt)</b>: 将按段落自动分割<br>
                                    </div>
                                    
                                    <script>
                                    // 确保导入知识库按钮功能正常
                                    document.addEventListener('DOMContentLoaded', function() {
                                        // 等待Gradio完全加载
                                        setTimeout(function() {
                                            const loadKbBtn = document.getElementById('load_kb_button');
                                            if (loadKbBtn) {
                                                console.log('找到导入知识库按钮，确保其可点击');
                                                // 移除可能阻止点击的样式
                                                loadKbBtn.style.pointerEvents = 'auto';
                                                loadKbBtn.style.cursor = 'pointer';
                                                loadKbBtn.style.opacity = '1';
                                                loadKbBtn.style.zIndex = '500';
                                                
                                                console.log('导入知识库按钮已设置为可点击状态');
                                            }
                                        }, 1500);
                                    });
                                    </script>
                                    """)
                                
                                load_kb_progress = gr.HTML("", label="导入进度")
                                load_kb_result = gr.Textbox(label="导入结果", lines=5, interactive=False)
                
                # 新增：文件管理标签页
                with gr.TabItem("📁 文件管理", id="file_management"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 选择知识库")
                                file_mgr_kb_name = gr.Dropdown(label="知识库", choices=[])
                                refresh_files_btn = gr.Button("加载文件列表", variant="primary")
                            
                            with gr.Box():
                                gr.Markdown("### 删除文件")
                                delete_file_btn = gr.Button("删除选中文件", variant="stop")
                                delete_file_result = gr.Textbox(label="删除结果", interactive=False)
                        
                        with gr.Column(scale=2):
                            with gr.Box():
                                gr.Markdown("### 文件列表")
                                file_list = gr.Dataframe(
                                    headers=["序号", "文件名", "文件路径", "文件大小", "块数量", "重要性系数", "添加时间"],
                                    datatype=["number", "str", "str", "str", "number", "number", "str"],
                                    row_count=10,
                                    interactive=False
                                )
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 替换文件")
                                replace_file_path = gr.Textbox(label="选中的文件路径", interactive=False)
                                new_file = gr.File(label="选择新文件")
                                
                                with gr.Row():
                                    replace_chunk_method = gr.Radio(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic",
                                        interactive=True,
                                        elem_id="replace_chunk_method_radio",
                                        container=True,
                                        orientation="vertical"
                                    )
                                    
                                with gr.Row():
                                    replace_chunk_size = gr.Slider(label="块大小", minimum=200, maximum=2000, step=100, value=1000)
                                    replace_chunk_overlap = gr.Slider(label="重叠大小", minimum=0, maximum=500, step=50, value=200)
                                
                                replace_file_btn = gr.Button("替换文件", variant="primary", elem_id="replace_file_button")
                                # 添加替换按钮特别处理
                                gr.HTML("""
                                <script>
                                // 确保替换文件按钮功能正常
                                document.addEventListener('DOMContentLoaded', function() {
                                    // 等待Gradio完全加载
                                    setTimeout(function() {
                                        const replaceBtn = document.getElementById('replace_file_button');
                                        if (replaceBtn) {
                                            console.log('找到替换文件按钮，确保其可点击');
                                            // 移除可能阻止点击的样式
                                            replaceBtn.style.pointerEvents = 'auto';
                                            replaceBtn.style.cursor = 'pointer';
                                            replaceBtn.style.opacity = '1';
                                            replaceBtn.style.zIndex = '500';
                                            
                                            console.log('替换文件按钮已设置为可点击状态');
                                        }
                                    }, 1500);
                                });
                                </script>
                                """)
                                replace_result = gr.Textbox(label="替换结果", interactive=False)
                        
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 文件详情")
                                file_details = gr.Dataframe(
                                    headers=["属性", "值"],
                                    datatype=["str", "str"],
                                    row_count=8,
                                    interactive=False
                                )
                            
                            # 添加重要性系数设置区域
                            with gr.Box():
                                gr.Markdown("### 设置重要性系数")
                                with gr.Row():
                                    importance_file_path = gr.Textbox(label="选中的文件路径", interactive=False)
                                    importance_factor = gr.Slider(label="重要性系数", minimum=0.1, maximum=5.0, step=0.1, value=1.0)
                                set_importance_btn = gr.Button("设置重要性系数", variant="primary")
                                importance_result = gr.Textbox(label="设置结果", interactive=False)
                
                with gr.TabItem("🔎 知识库检索", id="kb_search"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 检索设置")
                                search_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                search_query = gr.Textbox(label="检索问题", placeholder="输入问题...", lines=3)
                                with gr.Row():
                                    top_k = gr.Slider(label="返回结果数量", minimum=1, maximum=10, step=1, value=5)
                                    use_rerank = gr.Checkbox(
                                        label="使用重排序", 
                                        value=False,  # 默认关闭重排序
                                        info="开启可提高相关性，但可能偶尔失败。如遇问题请关闭。"
                                    )
                                
                                search_btn = gr.Button("检索", variant="primary")
                        
                        with gr.Column(scale=2):
                            with gr.Box():
                                gr.Markdown("### 检索结果")
                                search_results = gr.Dataframe(
                                    headers=["序号", "内容", "相关度", "来源"],
                                    datatype=["number", "html", "number", "str"],  # 注意这里"str"改为"html"
                                    row_count=10,
                                    wrap=True,  # 启用文本换行
                                    height=400,  # 增加高度
                                    max_cols=4   # 限制最大列数
                                )
                
                with gr.TabItem("💬 知识库对话", id="kb_chat"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 对话设置")
                                chat_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                with gr.Row():
                                    chat_top_k = gr.Slider(label="检索结果数量", minimum=1, maximum=10, step=1, value=3)
                                    temperature = gr.Slider(label="生成多样性", minimum=0.1, maximum=1.0, step=0.1, value=0.7)
                                
                                clear_btn = gr.Button("清空对话", variant="secondary")
                        
                        with gr.Column(scale=2):
                            with gr.Box():
                                gr.Markdown("### 对话")
                                chatbot = gr.Chatbot(height=400, label="知识库对话")
                                chat_input = gr.Textbox(label="问题", placeholder="输入问题...", lines=2)
                                chat_btn = gr.Button("发送", variant="primary")
            
            # 添加分块方法的事件处理函数
            def on_chunk_method_change(value):
                print(f"分块方法已更改为: {value}")
                # 添加一些交互性反馈
                return gr.update(value=value, interactive=True)
                
            # 绑定事件
            create_kb_btn.click(
                fn=self.create_kb,
                inputs=[kb_name, dimension, index_type],
                outputs=create_kb_result
            ).then(
                fn=self._refresh_kb_lists,
                outputs=[kb_list, kb_to_delete, upload_kb_name, search_kb_name, chat_kb_name, kb_info_dropdown, file_mgr_kb_name, load_kb_name]
            )
            
            refresh_kb_btn.click(
                fn=self._refresh_kb_lists,
                outputs=[kb_list, kb_to_delete, upload_kb_name, search_kb_name, chat_kb_name, kb_info_dropdown, file_mgr_kb_name, load_kb_name]
            )
            
            # 修改事件绑定方式，改用详细的change方法而非之前的简单绑定
            chunk_method.change(
                fn=on_chunk_method_change,
                inputs=[chunk_method],
                outputs=[chunk_method]
            )
            
            load_kb_chunk_method.change(
                fn=on_chunk_method_change,
                inputs=[load_kb_chunk_method],
                outputs=[load_kb_chunk_method]
            )
            
            replace_chunk_method.change(
                fn=on_chunk_method_change,
                inputs=[replace_chunk_method],
                outputs=[replace_chunk_method]
            )
            
            # 导入知识库按钮事件
            load_kb_btn.click(
                fn=self.load_knowledge_base,
                inputs=[load_kb_name, load_kb_file, load_kb_chunk_method, load_kb_chunk_size, load_kb_chunk_overlap],
                outputs=load_kb_result
            ).then(
                fn=lambda kb_name: kb_name,  # 先将选择的导入知识库名称传递给文件管理的知识库选择器
                inputs=load_kb_name,
                outputs=file_mgr_kb_name
            ).then(
                fn=self.list_files,  # 然后刷新文件列表
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 使用下拉菜单change事件替代DataFrame的select事件
            kb_info_dropdown.change(
                fn=self.get_kb_info,
                inputs=kb_info_dropdown,
                outputs=kb_info_result
            )
            
            delete_kb_btn.click(
                fn=self.delete_kb,
                inputs=kb_to_delete,
                outputs=delete_kb_result
            ).then(
                fn=self._refresh_kb_lists,
                outputs=[kb_list, kb_to_delete, upload_kb_name, search_kb_name, chat_kb_name, kb_info_dropdown, file_mgr_kb_name, load_kb_name]
            )
            
            upload_btn.click(
                fn=self.upload_files,
                inputs=[upload_kb_name, upload_files, chunk_size, chunk_overlap],
                outputs=[upload_progress, upload_result]
            ).then(
                fn=lambda kb_name: kb_name,  # 先将选择的上传知识库名称传递给文件管理的知识库选择器
                inputs=upload_kb_name,
                outputs=file_mgr_kb_name
            ).then(
                fn=self.list_files,  # 然后刷新文件列表
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 文件管理相关事件
            refresh_files_btn.click(
                fn=self.list_files,
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 知识库选择变更时自动刷新文件列表
            file_mgr_kb_name.change(
                fn=self.list_files,
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 添加上传知识库选择变更时自动关联到文件管理选项
            upload_kb_name.change(
                fn=lambda kb_name: kb_name,
                inputs=upload_kb_name,
                outputs=file_mgr_kb_name
            ).then(
                fn=self.list_files,
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 添加导入知识库选择变更时自动关联到文件管理选项
            load_kb_name.change(
                fn=lambda kb_name: kb_name,
                inputs=load_kb_name,
                outputs=file_mgr_kb_name
            ).then(
                fn=self.list_files,
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            # 绑定文件选择事件到替换文件和设置重要性区域
            file_list.select(
                fn=self.on_file_select,
                inputs=[file_list],
                outputs=[replace_file_path, file_details, importance_file_path]
            )
            
            # 绑定设置重要性系数按钮
            set_importance_btn.click(
                fn=self.set_importance_coefficient,
                inputs=[file_mgr_kb_name, importance_file_path, importance_factor],
                outputs=importance_result
            ).then(
                fn=self.list_files,  # 刷新文件列表以显示更新后的重要性系数
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            search_btn.click(
                fn=self.search_kb,
                inputs=[search_kb_name, search_query, top_k, use_rerank],
                outputs=search_results
            )
            
            chat_history = gr.State([])
            
            chat_btn.click(
                fn=self.chat_with_kb,
                inputs=[chat_kb_name, chat_input, chat_history, chat_top_k, temperature],
                outputs=[chatbot, chat_history]
            ).then(
                fn=lambda: "",
                outputs=chat_input
            )
            
            clear_btn.click(
                fn=lambda: ([], []),
                outputs=[chatbot, chat_history]
            )
            
            # 导入知识库文件选择事件
            def on_load_kb_file_change(file_info):
                """导入知识库文件变更时的处理函数"""
                if file_info is None:
                    return gr.update(visible=False), ""
                try:
                    if hasattr(file_info, 'name'):
                        file_path = file_info.name
                    elif isinstance(file_info, dict) and 'name' in file_info:
                        file_path = file_info['name']
                    else:
                        return gr.update(visible=True), "警告：无法识别上传的文件格式"
                    
                    print(f"导入知识库选择文件路径: {file_path}")
                    return gr.update(visible=True), f"已选择文件: {os.path.basename(file_path)}"
                except Exception as e:
                    return gr.update(visible=True), f"文件选择错误: {str(e)}"
  
            load_kb_file.change(
                fn=on_load_kb_file_change,
                inputs=load_kb_file,
                outputs=[load_kb_progress, load_kb_result]
            )
            
            # 添加界面初始化代码
            # 初始化
            demo.load(
                fn=self._refresh_kb_lists,
                outputs=[kb_list, kb_to_delete, upload_kb_name, search_kb_name, chat_kb_name, kb_info_dropdown, file_mgr_kb_name, load_kb_name]
            )
        
        demo.launch(server_name=server_name, server_port=server_port, share=share)

    def _refresh_kb_lists(self):
        """获取知识库列表数据，用于更新UI"""
        kb_names = self.list_kbs()
        kb_data = self._get_kb_list_data()
        df = pd.DataFrame(kb_data) if kb_data else pd.DataFrame()
        return (
            df,  # kb_list
            gr.Dropdown.update(choices=kb_names),  # kb_to_delete
            gr.Dropdown.update(choices=kb_names),  # upload_kb_name
            gr.Dropdown.update(choices=kb_names),  # search_kb_name
            gr.Dropdown.update(choices=kb_names),  # chat_kb_name
            gr.Dropdown.update(choices=kb_names),  # kb_info_dropdown
            gr.Dropdown.update(choices=kb_names),  # file_mgr_kb_name
            gr.Dropdown.update(choices=kb_names)   # load_kb_name
        )

    def _get_kb_list_data(self):
        """获取知识库列表数据，用于显示在DataFrame中"""
        kb_names = self.list_kbs()
        if not kb_names:
            return []
            
        result_data = []
        for name in kb_names:
            try:
                response = requests.get(f"{self.api_base_url}/kb/info/{name}")
                if response.status_code == 200:
                    info = response.json().get("data", {})
                    result_data.append({
                        "知识库名称": name,
                        "向量维度": info.get("dimension", "未知"),
                        "索引类型": info.get("index_type", "未知"),
                        "文档数量": info.get("vector_count", 0)
                    })
            except Exception as e:
                print(f"获取知识库 {name} 信息失败: {str(e)}")
                result_data.append({
                    "知识库名称": name,
                    "向量维度": "获取失败",
                    "索引类型": "获取失败",
                    "文档数量": 0
                })
                
        return result_data

    def load_knowledge_base(self, kb_name: str, file_path: str, chunk_method: str, chunk_size: int, chunk_overlap: int) -> str:
        """从文件导入知识库"""
        if not kb_name:
            return "请先选择知识库"
            
        if not file_path:
            return "请选择要导入的数据文件"
        
        print(f"准备从文件导入知识库: {kb_name}")
        print(f"文件路径: {file_path}")
        print(f"分块配置: 方法={chunk_method}, 大小={chunk_size}, 重叠={chunk_overlap}")
        
        try:
            # 判断文件类型
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                # 处理JSON文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        
                        # 判断JSON格式
                        if isinstance(data, list):
                            documents = data
                            print(f"解析JSON数组，包含 {len(documents)} 个文档")
                        elif isinstance(data, dict) and 'documents' in data:
                            documents = data['documents']
                            print(f"解析JSON对象，包含 {len(documents)} 个文档")
                        else:
                            return f"JSON格式不支持，必须是文档数组或者包含documents字段的对象"
                        
                        # 检查文档格式
                        for i, doc in enumerate(documents):
                            if 'text' not in doc:
                                return f"文档 #{i+1} 缺少必须的text字段"
                    except json.JSONDecodeError:
                        return "JSON格式无效，无法解析"
                    
                    # 准备分块配置
                    chunk_config = {
                        "method": chunk_method,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                    
                    # 调用API处理文档
                    response = requests.post(
                        f"{self.api_base_url}/kb/load_documents",
                        json={
                            "kb_name": kb_name,
                            "documents": documents,
                            "chunk_config": chunk_config
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            return f"成功导入 {len(documents)} 个文档到知识库 {kb_name}"
                        else:
                            return f"导入失败: {result.get('message', '未知错误')}"
                    else:
                        return f"导入失败 (HTTP {response.status_code}): {response.text}"
            
            elif file_ext in ['.csv', '.tsv']:
                # 处理CSV/TSV文件
                import pandas as pd
                
                try:
                    delimiter = ',' if file_ext == '.csv' else '\t'
                    df = pd.read_csv(file_path, delimiter=delimiter)
                    
                    # 检查是否包含text列
                    if 'text' not in df.columns:
                        return "CSV/TSV文件必须包含text列"
                    
                    # 转换为文档列表
                    documents = []
                    for _, row in df.iterrows():
                        doc = {"text": row['text']}
                        
                        # 添加其他列作为元数据
                        for col in df.columns:
                            if col != 'text':
                                doc[col] = row[col]
                        
                        documents.append(doc)
                    
                    print(f"从CSV/TSV文件中解析出 {len(documents)} 个文档")
                    
                    # 准备分块配置
                    chunk_config = {
                        "method": chunk_method,
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                    
                    # 调用API处理文档
                    response = requests.post(
                        f"{self.api_base_url}/kb/load_documents",
                        json={
                            "kb_name": kb_name,
                            "documents": documents,
                            "chunk_config": chunk_config
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            return f"成功导入 {len(documents)} 个文档到知识库 {kb_name}"
                        else:
                            return f"导入失败: {result.get('message', '未知错误')}"
                    else:
                        return f"导入失败 (HTTP {response.status_code}): {response.text}"
                except Exception as e:
                    return f"处理CSV/TSV文件时出错: {str(e)}"
            
            elif file_ext == '.txt':
                # 处理纯文本文件，按段落分割
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 按空行分段
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                
                # 创建文档
                documents = [{"text": para} for para in paragraphs]
                
                print(f"从文本文件中解析出 {len(documents)} 个段落")
                
                # 准备分块配置
                chunk_config = {
                    "method": chunk_method,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap
                }
                
                # 调用API处理文档
                response = requests.post(
                    f"{self.api_base_url}/kb/load_documents",
                    json={
                        "kb_name": kb_name,
                        "documents": documents,
                        "chunk_config": chunk_config
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        return f"成功导入 {len(documents)} 个段落到知识库 {kb_name}"
                    else:
                        return f"导入失败: {result.get('message', '未知错误')}"
                else:
                    return f"导入失败 (HTTP {response.status_code}): {response.text}"
            
            else:
                # 对于其他类型文件，使用上传接口处理
                return f"不支持的文件类型: {file_ext}，请使用上传文件功能处理"
        
        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = f"导入知识库过程中出错: {str(e)}"
            print(f"{error_msg}\n{error_trace}")
            return f"{error_msg}"

    def on_file_select(self, evt: gr.SelectData, file_data):
        """处理文件选择事件"""
        try:
            if evt is not None and hasattr(evt, 'index') and file_data is not None:
                # 获取选中行的索引
                if isinstance(evt.index, tuple):
                    row_idx = evt.index[0]
                elif isinstance(evt.index, list):
                    row_idx = evt.index[0] if evt.index else 0
                else:
                    row_idx = evt.index
                
                # 确认选中的行在有效范围内
                if isinstance(file_data, pd.DataFrame) and len(file_data) > row_idx:
                    selected_row = file_data.iloc[row_idx]
                    
                    # 判断是否包含错误提示
                    if "错误" in selected_row or "提示" in selected_row:
                        return "", {}
                        
                    # 提取文件路径和重要性系数
                    if "文件路径" in selected_row:
                        file_path = selected_row["文件路径"]
                        importance_coef = selected_row.get("重要性系数", 1.0)
                        return file_path, {}, file_path
                
                return "", {}
        except Exception as e:
            print(f"处理文件选择事件时出错: {str(e)}")
            return "", {}

# 便捷启动函数
def launch_ui(api_base_url: str = "http://localhost:8000", share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7861):
    """启动知识库管理界面"""
    print("="*60)
    print("正在启动知识库管理界面...")
    print(f"API服务器地址: {api_base_url}")
    print(f"UI服务端口: {server_port}")
    print("="*60)
    
    try:
        ui = RAGServiceWebUI(api_base_url=api_base_url)
        ui.launch(share=share, server_name=server_name, server_port=server_port)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"启动UI界面失败: {str(e)}")
        print(f"错误详情:\n{error_trace}")
        print("请检查API服务器是否已启动，地址是否正确")


if __name__ == "__main__":
    print("RAG知识库管理系统 - UI服务启动中...")
    try:
        launch_ui()
    except KeyboardInterrupt:
        print("\n用户中断，UI服务已停止")
    except Exception as e:
        print(f"启动失败: {str(e)}")
        traceback.print_exc()
