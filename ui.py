import os
import gradio as gr
import pandas as pd
import traceback
from typing import List, Dict, Any
from main import RAGService
from core.file_handle import FileHandler

class RAGServiceUI:
    """知识库管理界面类，提供基于Gradio的Web界面"""
    
    def __init__(self, rag_service: RAGService = None, file_handler: FileHandler = None):
        """
        初始化知识库管理界面
        
        参数:
            rag_service: RAG服务实例，如果为None则创建新实例
            file_handler: 文件处理器实例，如果为None则创建新实例
        """
        self.rag_service = rag_service if rag_service else RAGService()
        self.file_handler = file_handler if file_handler else FileHandler()
        
    def create_kb(self, kb_name: str, dimension: int, index_type: str) -> str:
        """创建知识库"""
        if not kb_name:
            return "错误：知识库名称不能为空"
        
        try:    
            if self.rag_service.create_knowledge_base(kb_name, dimension, index_type):
                return f"成功创建知识库：{kb_name}"
            else:
                return f"创建知识库失败，可能已存在同名知识库：{kb_name}"
        except Exception as e:
            error_msg = f"创建知识库 {kb_name} 失败: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"{error_msg}\n{error_trace}")
            return f"{error_msg}\n详细错误信息:\n{error_trace}"
    
    def list_kbs(self) -> List[str]:
        """获取知识库列表"""
        try:
            kb_list = self.rag_service.list_knowledge_bases()
            # 确保返回的是字符串列表而不是嵌套列表
            if kb_list and isinstance(kb_list[0], list):
                return kb_list[0]
            return kb_list
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
                kb_name = kb_name[0]
                
            print(f"获取知识库信息: {kb_name}, 类型: {type(kb_name)}")
            info = self.rag_service.get_knowledge_base_info(kb_name)
            if not info:
                return pd.DataFrame()
                
            # 转换为DataFrame以便在UI中显示
            df = pd.DataFrame([{
                "知识库名称": kb_name,
                "向量维度": info.get("dimension", "未知"),
                "索引类型": info.get("index_type", "未知"),
                "文档数量": info.get("vector_count", 0)
            }])
            return df
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"获取知识库信息失败: {str(e)}\n{error_trace}")
            return pd.DataFrame([{"错误": f"获取知识库信息失败: {str(e)}\n{error_trace}"}])
    
    def delete_kb(self, kb_name: str) -> str:
        """删除知识库"""
        if not kb_name:
            return "错误：请选择要删除的知识库"
        
        try:
            # 确保kb_name是字符串而不是列表
            if isinstance(kb_name, list):
                if not kb_name:
                    return "错误：请选择要删除的知识库"
                kb_name = kb_name[0]
                
            if self.rag_service.delete_knowledge_base(kb_name):
                return f"成功删除知识库：{kb_name}"
            else:
                return f"删除知识库失败：{kb_name}"
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"删除知识库失败: {str(e)}\n{error_trace}")
            return f"删除知识库失败: {str(e)}\n详细错误信息:\n{error_trace}"
    
    def upload_files(self, kb_name: str, files: List[str], chunk_size: int, chunk_overlap: int) -> str:
        """上传文件到知识库"""
        if not kb_name:
            return "错误：请选择知识库"
            
        if not files:
            return "错误：请上传文件"
        
        try:
            # 确保kb_name是字符串而不是列表
            if isinstance(kb_name, list):
                if not kb_name:
                    return "错误：请选择知识库"
                kb_name = kb_name[0]
                
            # 设置文件处理器参数
            self.file_handler.chunk_size = chunk_size
            self.file_handler.chunk_overlap = chunk_overlap
            
            total_docs = 0
            failed_files = []
            
            for file_path in files:
                try:
                    # 处理文件
                    documents = self.file_handler.process_file(file_path)
                    if documents:
                        # 添加到知识库
                        if self.rag_service.add_documents(kb_name, documents):
                            total_docs += len(documents)
                        else:
                            failed_files.append(os.path.basename(file_path))
                    else:
                        failed_files.append(os.path.basename(file_path))
                except Exception as e:
                    error_trace = traceback.format_exc()
                    failed_files.append(f"{os.path.basename(file_path)} (错误: {str(e)})\n{error_trace}")
            
            if failed_files:
                return f"成功添加 {total_docs} 个文档块，但以下文件处理失败：\n" + "\n".join(failed_files)
            else:
                return f"成功添加 {total_docs} 个文档块到知识库 {kb_name}"
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"上传文件失败: {str(e)}\n{error_trace}")
            return f"上传文件失败: {str(e)}\n详细错误信息:\n{error_trace}"
    
    def search_kb(self, kb_name: str, query: str, top_k: int, use_rerank: bool) -> pd.DataFrame:
        """搜索知识库"""
        if not kb_name or not query:
            return pd.DataFrame()
        
        try:
            # 确保kb_name是字符串而不是列表
            if isinstance(kb_name, list):
                if not kb_name:
                    return pd.DataFrame()
                kb_name = kb_name[0]
                
            results = self.rag_service.search(kb_name, query, top_k, use_rerank)
            if not results:
                return pd.DataFrame([{"文档内容": "未找到相关内容", "相关度": 0, "来源": ""}])
                
            # 转换为DataFrame以便在UI中显示
            data = []
            for i, result in enumerate(results):
                data.append({
                    "序号": i + 1,
                    "文档内容": result.get("text", ""),
                    "相关度": f"{result.get('score', 0):.2f}%",
                    "来源": result.get("metadata", {}).get("source", "未知")
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"搜索知识库失败: {str(e)}\n{error_trace}")
            return pd.DataFrame([{"错误": f"搜索失败: {str(e)}\n详细错误信息:\n{error_trace}"}])
    
    def launch(self, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
        """启动Gradio界面"""
        with gr.Blocks(title="知识库管理系统", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 📚 知识库管理系统")
            
            with gr.Tabs():
                # 知识库管理标签页
                with gr.TabItem("知识库管理"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("## 创建知识库")
                            kb_name_input = gr.Textbox(label="知识库名称")
                            dimension_input = gr.Number(label="向量维度", value=512, minimum=1, step=1)
                            index_type_input = gr.Dropdown(
                                label="索引类型", 
                                choices=["Flat", "IVF", "HNSW"], 
                                value="Flat"
                            )
                            create_btn = gr.Button("创建知识库", variant="primary")
                            create_output = gr.Textbox(label="创建结果")
                            
                            gr.Markdown("## 删除知识库")
                            kb_to_delete = gr.Dropdown(label="选择要删除的知识库")
                            delete_btn = gr.Button("删除知识库", variant="stop")
                            delete_output = gr.Textbox(label="删除结果")
                            
                        with gr.Column(scale=1):
                            gr.Markdown("## 知识库列表")
                            refresh_btn = gr.Button("刷新列表")
                            kb_list = gr.Dropdown(label="选择知识库")
                            kb_info = gr.DataFrame(label="知识库信息")
                
                # 文档管理标签页
                with gr.TabItem("文档管理"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            doc_kb_list = gr.Dropdown(label="选择知识库")
                            file_upload = gr.File(label="上传文件", file_count="multiple")
                            chunk_size = gr.Slider(
                                label="文本块大小", 
                                minimum=100, 
                                maximum=2000, 
                                value=500, 
                                step=50
                            )
                            chunk_overlap = gr.Slider(
                                label="块重叠大小", 
                                minimum=0, 
                                maximum=200, 
                                value=50, 
                                step=10
                            )
                            upload_btn = gr.Button("上传文件到知识库", variant="primary")
                            upload_output = gr.Textbox(label="上传结果")
                
                # 知识库搜索标签页
                with gr.TabItem("知识库搜索"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            search_kb_list = gr.Dropdown(label="选择知识库")
                            query_input = gr.Textbox(label="搜索内容")
                            with gr.Row():
                                top_k = gr.Slider(
                                    label="返回结果数量", 
                                    minimum=1, 
                                    maximum=20, 
                                    value=5, 
                                    step=1
                                )
                                use_rerank = gr.Checkbox(label="使用重排序", value=True)
                            search_btn = gr.Button("搜索", variant="primary")
                            search_results = gr.DataFrame(label="搜索结果")
            
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
def launch_ui(share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    """启动知识库管理界面"""
    ui = RAGServiceUI()
    ui.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    launch_ui()
