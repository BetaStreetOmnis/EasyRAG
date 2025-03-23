import os
import gradio as gr
import pandas as pd
import traceback
import requests
import json
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
    
    def upload_files(self, kb_name: str, files, chunk_size: int, chunk_overlap: int) -> str:
        """上传文件到知识库"""
        if not kb_name:
            return "错误：请选择知识库"
        if not files:
            return "错误：请选择要上传的文件"
            
        try:
            # 准备表单数据
            form_data = {
                "kb_name": kb_name,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
            
            # 准备文件
            files_data = []
            for file in files:
                files_data.append(("files", (os.path.basename(file.name), open(file.name, "rb"))))
            
            # 发送请求
            response = requests.post(
                f"{self.api_base_url}/kb/upload",
                data=form_data,
                files=files_data
            )
            
            # 关闭文件
            for _, (_, f) in files_data:
                f.close()
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "partial_success":
                    failed_files = result.get("failed_files", [])
                    failed_str = "\n".join(failed_files)
                    return f"{result.get('message')}\n失败文件列表:\n{failed_str}"
                else:
                    return result.get("message", "文件上传成功")
            else:
                error_data = response.json()
                return f"上传文件失败: {error_data.get('detail', '未知错误')}"
        except Exception as e:
            error_msg = f"上传文件失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            return f"{error_msg}"
    
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
                    return pd.DataFrame([{"提示": "未找到相关内容"}])
                
                # 转换为DataFrame
                df_data = []
                for i, item in enumerate(data):
                    df_data.append({
                        "序号": i + 1,
                        "内容": item.get("text", ""),
                        "相关度": round(item.get("score", 0), 3),
                        "来源": item.get("metadata", {}).get("source", "未知")
                    })
                return pd.DataFrame(df_data)
            else:
                error_data = response.json()
                return pd.DataFrame([{"错误": f"搜索失败: {error_data.get('detail', '未知错误')}"}])
        except Exception as e:
            error_msg = f"搜索知识库失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            return pd.DataFrame([{"错误": error_msg}])
    
    def launch(self, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
        """启动Gradio界面"""
        # 自定义主题
        custom_theme = gr.themes.Soft(
            primary_hue="teal",
            secondary_hue="indigo",
            neutral_hue="slate",
            radius_size=gr.themes.sizes.radius_lg,
            text_size=gr.themes.sizes.text_md
        )
        
        with gr.Blocks(title="智能知识库管理系统", theme=custom_theme, css="""
            .gradio-container {max-width: 1300px; margin: auto;}
            .header-text {text-align: center; margin-bottom: 30px; color: #008080; font-size: 2.5em; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);}
            .header-subtitle {text-align: center; margin-bottom: 20px; color: #555; font-size: 1.2em;}
            .tab-header {font-size: 1.3em; font-weight: bold; margin-bottom: 15px; color: #008080; border-bottom: 2px solid #e0f2f1; padding-bottom: 8px;}
            .action-btn {min-width: 140px; height: 45px; font-size: 1.05em; font-weight: 500; transition: all 0.3s ease;}
            .action-btn:hover {transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1);}
            .info-box {padding: 15px; border-radius: 10px; background-color: #e0f7fa; margin: 15px 0; border-left: 5px solid #00897b; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
            .footer {text-align: center; margin-top: 40px; padding: 20px; font-size: 0.95em; color: #666; border-top: 1px solid #eee;}
            .gr-form {border: 1px solid #e0e0e0; padding: 20px; border-radius: 12px; background-color: #fafafa; box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 20px; transition: all 0.3s ease;}
            .gr-form:hover {box-shadow: 0 5px 15px rgba(0,0,0,0.08);}
            .gr-box {border-radius: 10px; overflow: hidden;}
            .gr-accordion {border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;}
            .gr-button {transition: all 0.3s ease;}
            .gr-button:hover {transform: translateY(-2px);}
            .gr-input {border-radius: 8px;}
            .gr-panel {border-radius: 10px; overflow: hidden;}
            .gr-slider {margin-top: 10px;}
            .gr-checkbox {margin-top: 10px;}
            .icon-text {display: flex; align-items: center; gap: 8px;}
            .icon-text i {font-size: 1.2em; color: #00897b;}
            .status-success {color: #2e7d32; background-color: #e8f5e9; padding: 10px; border-radius: 8px; margin-top: 10px;}
            .status-error {color: #c62828; background-color: #ffebee; padding: 10px; border-radius: 8px; margin-top: 10px;}
            .highlight-box {background-color: #e1f5fe; border-left: 4px solid #0288d1; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0;}
            .stat-box {background-color: #f5f5f5; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
            .stat-number {font-size: 2em; font-weight: bold; color: #00897b; margin: 10px 0;}
            .stat-label {color: #555; font-size: 0.9em;}
            .tab-container {padding: 20px; background-color: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);}
            .search-result-row:nth-child(even) {background-color: #f9f9f9;}
            .search-result-row:hover {background-color: #f0f7fa;}
            .animate-pulse {animation: pulse 2s infinite;}
            @keyframes pulse {0% {opacity: 1;} 50% {opacity: 0.7;} 100% {opacity: 1;}}
        """) as demo:
            gr.Markdown("# 🌟 智能知识库管理系统", elem_classes=["header-text"])
            gr.Markdown("高效管理和检索您的知识资源，提升信息获取效率", elem_classes=["header-subtitle"])
            
            with gr.Tabs(elem_classes=["tab-container"]):
                # 知识库管理标签页
                with gr.TabItem("📋 知识库管理", icon="database"):
                    gr.Markdown("""
                    <div class="info-box">
                        <div class="icon-text">
                            <i class="fas fa-info-circle"></i>
                            <span>在此页面创建、查看和管理您的知识库。每个知识库可以包含多个文档，并支持不同的索引类型。</span>
                        </div>
                    </div>
                    """)
                    
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            with gr.Box(elem_classes=["gr-form"]):
                                gr.Markdown("## 📝 创建知识库", elem_classes=["tab-header"])
                                kb_name_input = gr.Textbox(
                                    label="知识库名称", 
                                    placeholder="输入新知识库名称...",
                                    elem_classes=["gr-input"]
                                )
                                dimension_input = gr.Number(
                                    label="向量维度", 
                                    value=512, 
                                    minimum=1, 
                                    step=1,
                                    elem_classes=["gr-input"],
                                    info="向量维度决定了特征表示的丰富程度"
                                )
                                index_type_input = gr.Dropdown(
                                    label="索引类型", 
                                    choices=[
                                        {"label": "Flat (精确但较慢)", "value": "Flat"},
                                        {"label": "IVF (快速但近似)", "value": "IVF"},
                                        {"label": "HNSW (高性能图索引)", "value": "HNSW"}
                                    ], 
                                    value="Flat",
                                    info="选择适合您需求的索引类型",
                                    elem_classes=["gr-input"]
                                )
                                create_btn = gr.Button(
                                    "✨ 创建知识库", 
                                    variant="primary", 
                                    elem_classes=["action-btn"]
                                )
                                create_output = gr.Textbox(
                                    label="创建结果", 
                                    lines=2,
                                    elem_classes=["gr-input"]
                                )
                        
                        with gr.Column(scale=1):
                            with gr.Box(elem_classes=["gr-form"]):
                                gr.Markdown("## 🗑️ 删除知识库", elem_classes=["tab-header"])
                                kb_to_delete = gr.Dropdown(
                                    label="选择要删除的知识库", 
                                    info="请谨慎操作，删除后无法恢复",
                                    elem_classes=["gr-input"],
                                    allow_custom_value=True
                                )
                                delete_btn = gr.Button(
                                    "❌ 删除知识库", 
                                    variant="stop", 
                                    elem_classes=["action-btn"]
                                )
                                delete_output = gr.Textbox(
                                    label="删除结果", 
                                    lines=2,
                                    elem_classes=["gr-input"]
                                )
                            
                    with gr.Row():
                        with gr.Column():
                            with gr.Box(elem_classes=["gr-form"]):
                                gr.Markdown("## 📊 知识库信息", elem_classes=["tab-header"])
                                with gr.Row():
                                    refresh_btn = gr.Button(
                                        "🔄 刷新列表", 
                                        elem_classes=["action-btn"]
                                    )
                                    kb_list = gr.Dropdown(
                                        label="选择知识库", 
                                        info="查看知识库详细信息",
                                        elem_classes=["gr-input"],
                                        scale=3,
                                        allow_custom_value=True
                                    )
                                kb_info = gr.DataFrame(
                                    label="知识库详细信息",
                                    elem_classes=["gr-input"]
                                )
                
                # 文档管理标签页
                with gr.TabItem("📄 文档管理", icon="file-text"):
                    gr.Markdown("""
                    <div class="info-box">
                        <div class="icon-text">
                            <i class="fas fa-lightbulb"></i>
                            <span>在此页面上传和管理知识库中的文档。系统会自动处理文档并将其分块存储，以便高效检索。</span>
                        </div>
                    </div>
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            with gr.Box(elem_classes=["gr-form"]):
                                gr.Markdown("## 📤 文档上传", elem_classes=["tab-header"])
                                doc_kb_list = gr.Dropdown(
                                    label="选择知识库", 
                                    info="选择要上传文档的目标知识库",
                                    elem_classes=["gr-input"],
                                    allow_custom_value=True
                                )
                                file_upload = gr.File(
                                    label="上传文件", 
                                    file_count="multiple", 
                                    info="支持PDF、TXT、DOCX、PPTX、XLSX等格式",
                                    elem_classes=["gr-input"],
                                    file_types=[".pdf", ".txt", ".docx", ".pptx", ".xlsx", ".md", ".csv"]
                                )
                                
                                with gr.Accordion("⚙️ 高级设置", open=False, elem_classes=["gr-accordion"]):
                                    with gr.Row():
                                        with gr.Column():
                                            chunk_size = gr.Slider(
                                                label="文本块大小", 
                                                minimum=100, 
                                                maximum=2000, 
                                                value=500, 
                                                step=50,
                                                info="较大的块包含更多上下文，较小的块提高精确度",
                                                elem_classes=["gr-slider"]
                                            )
                                        with gr.Column():
                                            chunk_overlap = gr.Slider(
                                                label="块重叠大小", 
                                                minimum=0, 
                                                maximum=200, 
                                                value=50, 
                                                step=10,
                                                info="块之间的重叠字符数，有助于保持上下文连贯性",
                                                elem_classes=["gr-slider"]
                                            )
                                    
                                    gr.Markdown("""
                                    <div class="highlight-box">
                                        <b>提示:</b> 文本块大小影响检索质量。较大的块包含更多上下文但可能降低精确度，
                                        较小的块提高精确度但可能缺少上下文。推荐值为400-600。
                                    </div>
                                    """)
                                
                                upload_btn = gr.Button(
                                    "📤 上传文件到知识库", 
                                    variant="primary", 
                                    elem_classes=["action-btn"]
                                )
                                upload_output = gr.Textbox(
                                    label="上传结果", 
                                    lines=5,
                                    elem_classes=["gr-input"]
                                )
                
                # 知识库搜索标签页
                with gr.TabItem("🔍 知识库搜索", icon="search"):
                    gr.Markdown("""
                    <div class="info-box">
                        <div class="icon-text">
                            <i class="fas fa-search"></i>
                            <span>在此页面搜索知识库中的内容。系统会返回与您的查询最相关的文档片段。</span>
                        </div>
                    </div>
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            with gr.Box(elem_classes=["gr-form"]):
                                gr.Markdown("## 🔎 语义搜索", elem_classes=["tab-header"])
                                search_kb_list = gr.Dropdown(
                                    label="选择知识库", 
                                    info="选择要搜索的知识库",
                                    elem_classes=["gr-input"],
                                    allow_custom_value=True
                                )
                                query_input = gr.Textbox(
                                    label="搜索内容", 
                                    placeholder="输入您的问题或关键词...", 
                                    lines=3,
                                    elem_classes=["gr-input"],
                                    allow_custom_value=True
                                )
                                
                                with gr.Row():
                                    with gr.Column():
                                        top_k = gr.Slider(
                                            label="返回结果数量", 
                                            minimum=1, 
                                            maximum=20, 
                                            value=5, 
                                            step=1,
                                            info="返回的最大结果数量",
                                            elem_classes=["gr-slider"]
                                        )
                                    with gr.Column():
                                        use_rerank = gr.Checkbox(
                                            label="使用重排序", 
                                            value=False, 
                                            info="对结果进行语义重排序以提高相关性",
                                            elem_classes=["gr-checkbox"]
                                        )
                                
                                search_btn = gr.Button(
                                    "🔎 搜索", 
                                    variant="primary", 
                                    elem_classes=["action-btn"]
                                )
                                
                                gr.Markdown("""
                                <div class="highlight-box">
                                    <b>搜索技巧:</b> 尝试使用具体、明确的问题来获得最佳结果。
                                    您可以使用自然语言提问，而不仅仅是关键词。
                                </div>
                                """)
                                
                                search_results = gr.DataFrame(
                                    label="搜索结果",
                                    elem_classes=["gr-input", "search-result-row"]
                                )
            
            gr.Markdown("""
            <div class="footer">
                <p>© 2023 智能知识库管理系统 | 基于先进的向量检索技术构建</p>
                <p>支持多种文档格式 · 高效语义搜索 · 智能文档分块</p>
            </div>
            """)
            
            # 事件绑定
            create_btn.click(
                fn=self.create_kb,
                inputs=[kb_name_input, dimension_input, index_type_input],
                outputs=create_output
            )
            
            def refresh_kb_lists():
                kb_list = self.list_kbs()
                return kb_list, kb_list, kb_list, kb_list
            
            refresh_btn.click(
                fn=refresh_kb_lists,
                inputs=[],
                outputs=[kb_list, kb_to_delete, doc_kb_list, search_kb_list]
            )
            
            kb_list.change(
                fn=self.get_kb_info,
                inputs=kb_list,
                outputs=kb_info
            )
            
            delete_btn.click(
                fn=self.delete_kb,
                inputs=kb_to_delete,
                outputs=delete_output
            ).then(
                fn=refresh_kb_lists,
                inputs=[],
                outputs=[kb_list, kb_to_delete, doc_kb_list, search_kb_list]
            )
            
            upload_btn.click(
                fn=self.upload_files,
                inputs=[doc_kb_list, file_upload, chunk_size, chunk_overlap],
                outputs=upload_output
            )
            
            search_btn.click(
                fn=self.search_kb,
                inputs=[search_kb_list, query_input, top_k, use_rerank],
                outputs=search_results
            )
            
            # 初始加载知识库列表
            demo.load(
                fn=refresh_kb_lists,
                inputs=[],
                outputs=[kb_list, kb_to_delete, doc_kb_list, search_kb_list]
            )
        
        # 启动Gradio服务器
        demo.launch(share=share, server_name=server_name, server_port=server_port)

# 便捷启动函数
def launch_ui(api_base_url: str = "http://localhost:8000", share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    """启动知识库管理界面"""
    ui = RAGServiceWebUI(api_base_url=api_base_url)
    ui.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_ui()
