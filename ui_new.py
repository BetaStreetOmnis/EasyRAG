import os
import gradio as gr
import pandas as pd
import traceback
import requests
import json
import time
from typing import List, Dict, Any


class RAGServiceWebUI:
    """知识库管理界面类，提供基于Gradio的Web界面，通过API与后端交互"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        初始化知识库管理界面
        
        参数:
            api_base_url: API服务器的基础URL
        """
        self.api_base_url = api_base_url
        
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
            response = requests.post(
                f"{self.api_base_url}/kb/search",
                json={
                    "kb_name": kb_name,
                    "query": query,
                    "top_k": top_k,
                    "use_rerank": use_rerank
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(result)
                if "message" in result and "未找到相关内容" in result["message"]:
                    return pd.DataFrame([{"提示": "未找到相关内容"}])
                
                data = result.get("data", [])
                if not data:
                    if use_rerank:
                        return pd.DataFrame([{"提示": "重排序后未找到相关内容，请尝试关闭重排序或修改搜索条件"}])
                    else:
                        return pd.DataFrame([{"提示": "未找到相关内容"}])
                
                # 转换为DataFrame，并处理内容格式
                df_data = []
                for i, item in enumerate(data):
                    # 处理文本内容，添加换行以提高可读性
                    text_content = item.get("text", "")
                    # 每70个字符左右添加换行符，使显示更清晰
                    formatted_text = '\n'.join([text_content[j:j+70] for j in range(0, len(text_content), 70)])
                    
                    df_data.append({
                        "序号": i + 1,
                        "内容": formatted_text,
                        "相关度": round(item.get("score", 0), 3),
                        "来源": item.get("metadata", {}).get("source", "未知")
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
        }
        
        table th {
            background-color: #4a6fa5;
            color: white;
            padding: 10px;
            text-align: left;
        }
        
        table td {
            padding: 8px 10px;
            border-bottom: 1px solid #ddd;
        }
        
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        /* 颜色主题 */
        .theme-primary { color: #4a6fa5; }
        .theme-secondary { color: #2c4c7c; }
        .theme-accent { color: #66bb6a; }
        .theme-warning { color: #ffa726; }
        .theme-error { color: #ef5350; }
        """
        
        with gr.Blocks(css=custom_css, title="知识库检索增强生成(RAG)服务") as demo:
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
                                    chunk_method = gr.Dropdown(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic"
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
                                
                                upload_btn = gr.Button("上传文件", variant="primary")
                                # 添加进度显示区域
                                upload_progress = gr.HTML("", label="上传进度")
                                upload_result = gr.Textbox(label="上传结果", lines=5, interactive=False)
                                
                            with gr.TabItem("导入知识库", id="load_knowledge_base"):
                                with gr.Row():
                                    load_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                    load_kb_file = gr.File(label="选择数据文件", file_count="single")
                                
                                gr.Markdown("### 分块设置")
                                with gr.Row():
                                    load_kb_chunk_method = gr.Dropdown(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic"
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
                                """)
                                
                                with gr.Row():
                                    load_kb_chunk_size = gr.Slider(label="分块大小", minimum=200, maximum=2000, step=100, value=1000)
                                    load_kb_chunk_overlap = gr.Slider(label="分块重叠", minimum=0, maximum=500, step=50, value=200)
                                
                                with gr.Row():
                                    load_kb_btn = gr.Button("导入知识库", variant="primary")
                                    load_kb_format_info = gr.HTML("""
                                    <div style="font-size: 0.8em; color: #666; margin-top: 0.5em;">
                                        <b>支持的数据格式：</b><br>
                                        • <b>JSON文件</b>: 包含文档数组，每个文档需要有text字段<br>
                                        • <b>CSV/TSV文件</b>: 包含文本列，可选包含元数据列<br>
                                        • <b>XML文件</b>: 包含文档标签的结构化XML<br>
                                        • <b>文本文件(.txt)</b>: 将按段落自动分割<br>
                                    </div>
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
                                    headers=["序号", "文件名", "文件路径", "文件大小", "块数量", "添加时间"],
                                    datatype=["number", "str", "str", "str", "number", "str"],
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
                                    replace_chunk_method = gr.Dropdown(
                                        label="分块方法", 
                                        choices=[
                                            "text_semantic", 
                                            "semantic", 
                                            "hierarchical", 
                                            "markdown_header", 
                                            "recursive_character", 
                                            "bm25"
                                        ], 
                                        value="text_semantic"
                                    )
                                    
                                with gr.Row():
                                    replace_chunk_size = gr.Slider(label="块大小", minimum=200, maximum=2000, step=100, value=1000)
                                    replace_chunk_overlap = gr.Slider(label="重叠大小", minimum=0, maximum=500, step=50, value=200)
                                
                                replace_file_btn = gr.Button("替换文件", variant="primary")
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
                
                with gr.TabItem("🔎 知识库检索", id="kb_search"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            with gr.Box():
                                gr.Markdown("### 检索设置")
                                search_kb_name = gr.Dropdown(label="选择知识库", choices=[])
                                search_query = gr.Textbox(label="检索问题", placeholder="输入问题...", lines=3)
                                with gr.Row():
                                    top_k = gr.Slider(label="返回结果数量", minimum=1, maximum=10, step=1, value=5)
                                    use_rerank = gr.Checkbox(label="使用重排序", value=True)
                                
                                search_btn = gr.Button("检索", variant="primary")
                        
                        with gr.Column(scale=2):
                            with gr.Box():
                                gr.Markdown("### 检索结果")
                                search_results = gr.Dataframe(
                                    headers=["序号", "内容", "相关度", "来源"],
                                    datatype=["number", "str", "number", "str"],
                                    row_count=10
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
            
            # 文件列表选择事件
            selected_file_path = gr.State("")

            def on_file_select(evt: gr.SelectData, file_data):
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
                        
                        # 检查数据格式并获取文件路径
                        if isinstance(file_data, pd.DataFrame):
                            if row_idx < len(file_data):
                                try:
                                    file_path = file_data.iloc[row_idx]["文件路径"]
                                    print(f"已选择文件路径: {file_path}")
                                    return file_path
                                except:
                                    print(f"无法从DataFrame中获取文件路径，尝试从字典中获取")
                                    if isinstance(file_data.iloc[row_idx], dict):
                                        file_path = file_data.iloc[row_idx].get("文件路径", "")
                                        return file_path
                        elif isinstance(file_data, list) and len(file_data) > row_idx:
                            file_path = file_data[row_idx].get("文件路径", "")
                            print(f"已从列表中选择文件路径: {file_path}")
                            return file_path
                        else:
                            print(f"文件数据格式不支持: {type(file_data)}, row_idx={row_idx}")
                    else:
                        print(f"文件选择事件格式不正确: evt={evt}, file_data类型={type(file_data)}")
                except Exception as e:
                    print(f"文件选择处理出错: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                return ""

            def update_file_details(kb_name, file_path):
                """获取并更新文件详情"""
                if not kb_name or not file_path:
                    return pd.DataFrame([{"提示": "请选择知识库和文件"}])
                return self.get_file_details(kb_name, file_path)

            # 使用新的选择事件处理方式
            file_list.select(
                fn=on_file_select,
                inputs=[file_list],
                outputs=selected_file_path
            ).then(
                fn=lambda path: path,
                inputs=selected_file_path,
                outputs=replace_file_path
            ).then(
                fn=update_file_details,
                inputs=[file_mgr_kb_name, selected_file_path],
                outputs=file_details
            )
            
            delete_file_btn.click(
                fn=self.delete_file,
                inputs=[file_mgr_kb_name, selected_file_path],
                outputs=delete_file_result
            ).then(
                fn=self.list_files,
                inputs=file_mgr_kb_name,
                outputs=file_list
            )
            
            def process_replace_file(kb_name, file_to_replace, file_info):
                """处理文件替换请求"""
                try:
                    print(f"替换文件参数: kb_name={kb_name}, file_to_replace={file_to_replace}, file_info类型={type(file_info)}")
                    
                    if file_info is None:
                        return "错误：请选择替换文件"
                    if not kb_name or not file_to_replace:
                        return "错误：请选择知识库和要替换的文件"
                        
                    # 获取上传文件的路径
                    if hasattr(file_info, 'name'):
                        file_path = file_info.name
                    elif isinstance(file_info, dict) and 'name' in file_info:
                        file_path = file_info['name']
                    else:
                        return "错误：无法识别上传的文件格式"
                        
                    print(f"替换文件路径: {file_path}")
                    
                    # 执行替换操作
                    return self.replace_file(
                        kb_name, 
                        file_to_replace, 
                        file_path, 
                        replace_chunk_method.value, 
                        replace_chunk_size.value, 
                        replace_chunk_overlap.value
                    )
                except Exception as e:
                    print(f"替换文件处理出错: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                    return f"替换文件处理出错: {str(e)}"
                
            replace_file_btn.click(
                fn=process_replace_file,
                inputs=[file_mgr_kb_name, replace_file_path, new_file],
                outputs=replace_result
            ).then(
                fn=self.list_files,
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

# 便捷启动函数
def launch_ui(api_base_url: str = "http://localhost:8000", share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7861):
    """启动知识库管理界面"""
    ui = RAGServiceWebUI(api_base_url=api_base_url)
    ui.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_ui()
