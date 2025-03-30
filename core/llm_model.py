import os
from typing import List, Dict, Any, Optional
from modelscope import AutoTokenizer, AutoModelForCausalLM
import torch

class DeepSeekLLM:
    """DeepSeek 1.5B 模型的包装类"""
    
    def __init__(self, model_id: str = "deepseek-ai/deepseek-chat-1.5b-base", device: str = None):
        """
        初始化DeepSeek LLM模型
        
        参数:
            model_id: ModelScope上的模型ID
            device: 运行设备，为None时自动选择
        """
        self.model_id = model_id
        
        # 确定设备
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"正在加载DeepSeek LLM模型 {model_id} 到 {self.device}...")
        
        # 加载模型和分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=False, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=self.device,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        )
        
        print(f"DeepSeek LLM模型加载完成")
    
    def generate_response(self, 
                        query: str, 
                        context: List[str] = None, 
                        history: List[List[str]] = None, 
                        temperature: float = 0.1,
                        max_length: int = 2048) -> str:
        """
        生成回复
        
        参数:
            query: 用户查询
            context: 检索到的上下文列表
            history: 聊天历史 [user, assistant, user, assistant, ...]
            temperature: 温度参数，控制回答的随机性
            max_length: 生成的最大长度
            
        返回:
            生成的回答
        """
        try:
            # 构建提示文本
            prompt = self._build_prompt(query, context, history)
            
            # 生成回答
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs["input_ids"],
                    max_new_tokens=max_length,
                    temperature=temperature,
                    repetition_penalty=1.1,
                    do_sample=True if temperature > 0 else False
                )
            
            response = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            print(f"生成回答时出错: {str(e)}")
            return f"抱歉，生成回答时出错: {str(e)}"
    
    def _build_prompt(self, query: str, context: List[str] = None, history: List[List[str]] = None) -> str:
        """构建提示文本"""
        # 初始化系统提示
        system_prompt = "你是一个专业的助手，你可以根据提供的上下文信息来回答用户的问题。回答应该准确、有帮助且基于事实。"
        
        # 构建上下文信息
        knowledge_text = ""
        if context and len(context) > 0:
            knowledge_text = "\n\n参考信息：\n" + "\n".join([f"{i+1}. {ctx}" for i, ctx in enumerate(context)])
        
        # 构建历史对话
        chat_history = ""
        if history and len(history) > 0:
            for user_query, assistant_response in history:
                chat_history += f"用户: {user_query}\n助手: {assistant_response}\n"
        
        # 构建最终提示
        prompt = f"{system_prompt}\n\n"
        
        if knowledge_text:
            prompt += f"{knowledge_text}\n\n"
            
        if chat_history:
            prompt += f"{chat_history}\n"
            
        prompt += f"用户: {query}\n助手: "
        
        return prompt

# 单例模式的实例
_model_instance = None

def get_llm_model(model_id: str = "deepseek-ai/deepseek-chat-1.5b-base", device: str = None) -> DeepSeekLLM:
    """获取LLM模型实例（单例模式）"""
    global _model_instance
    if _model_instance is None:
        _model_instance = DeepSeekLLM(model_id, device)
    return _model_instance 