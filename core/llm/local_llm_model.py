import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict, Any, Optional, Callable, Generator
from modelscope import AutoTokenizer, AutoModelForCausalLM
import torch

class DeepSeekLLM:
    """DeepSeek 1.5B 模型的包装类"""
    
    def __init__(self, model_id: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", device: str = None):
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
            
        # 直接从本地models_file文件夹加载模型
        # 项目路径
        project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(project_path, "models_file", "models", 'deepseek-ai', os.path.basename(model_id))
        print(f"正在从本地加载DeepSeek LLM模型 {model_path} 到 {self.device}...")
        if os.path.exists(model_path):
            print(f"正在从本地加载DeepSeek LLM模型 {model_path} 到 {self.device}...")
            model_location = model_path
        else:
            print(f"警告：本地模型路径 {model_path} 不存在，请确保已下载模型")
            model_location = model_id
            
        # 加载模型和分词器
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_location, use_fast=False, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_location,
                device_map=self.device,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            print(f"DeepSeek LLM模型加载完成")
        except Exception as e:
            print(f"模型加载失败: {str(e)}")
            raise
    
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
    
    def generate_stream(self, 
                      query: str, 
                      context: List[str] = None, 
                      history: List[List[str]] = None, 
                      temperature: float = 0.1,
                      max_length: int = 2048) -> Generator[str, None, None]:
        """
        流式生成回复
        
        参数:
            query: 用户查询
            context: 检索到的上下文列表
            history: 聊天历史 [user, assistant, user, assistant, ...]
            temperature: 温度参数，控制回答的随机性
            max_length: 生成的最大长度
            
        返回:
            生成的回答流
        """
        try:
            # 构建提示文本
            prompt = self._build_prompt(query, context, history)
            
            # 准备输入
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            input_length = inputs["input_ids"].shape[1]
            
            # 流式生成
            generated_text = ""
            for outputs in self.model.generate(
                inputs["input_ids"],
                max_new_tokens=max_length,
                temperature=temperature,
                repetition_penalty=1.1,
                do_sample=True if temperature > 0 else False,
                streamer=True,
                return_dict_in_generate=True,
                output_scores=False
            ):
                # 解码新生成的token
                new_tokens = outputs.sequences[0][input_length:]
                new_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
                
                # 只返回新增的文本部分
                if len(new_text) > len(generated_text):
                    delta_text = new_text[len(generated_text):]
                    generated_text = new_text
                    yield delta_text
        except Exception as e:
            print(f"流式生成回答时出错: {str(e)}")
            yield f"抱歉，生成回答时出错: {str(e)}"
    
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

def get_llm_model(model_id: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", device: str = None) -> DeepSeekLLM:
    """获取LLM模型实例（单例模式）"""
    global _model_instance
    if _model_instance is None:
        _model_instance = DeepSeekLLM(model_id, device)
    return _model_instance

if __name__ == "__main__":
    model = get_llm_model()
    # 测试普通生成
    response = model.generate_response("你好，世界！")
    print(response)
    
    # 测试流式生成
    print("\n流式输出测试:")
    for chunk in model.generate_stream("介绍一下中国的四大发明"):
        print(chunk, end="", flush=True)
