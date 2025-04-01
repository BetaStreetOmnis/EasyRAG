from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
import os
import logging
from modelscope import AutoTokenizer, AutoModelForCausalLM

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 定义请求模型
class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    model: Optional[str] = "deepseek-r1-1.5b"
    model_path: Optional[str] = None  # 允许用户指定模型路径

# 定义响应模型
class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    message: str = ""

# 全局变量存储模型和分词器
MODELS = {}
TOKENIZERS = {}
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_file")

def load_model(model_name="deepseek-r1-1.5b", model_path=None):
    """加载模型和分词器"""
    if model_name in MODELS:
        return MODELS[model_name], TOKENIZERS[model_name]
    
    try:
        logger.info(f"加载模型: {model_name}")
        
        # 如果没有指定路径，尝试使用本地路径或从ModelScope下载
        if not model_path:
            # 设置模型路径为本地models_file文件夹
            model_path = os.path.join(MODELS_DIR, model_name)
            if os.path.exists(model_path):
                logger.info(f"正在从本地加载模型: {model_path}")
            else:
                logger.info(f"本地模型不存在，将从ModelScope下载模型到: {model_path}")
                # 确保目录存在
                os.makedirs(model_path, exist_ok=True)
                
                # ModelScope模型ID映射
                if model_name == "deepseek-r1-1.5b":
                    model_id = "deepseek-ai/deepseek-coder-1.5b-instruct"
                else:
                    model_id = model_name
                
                # 使用模型ID作为下载源
                model_path = model_id
        
        logger.info(f"使用模型路径: {model_path}")
        
        # 加载分词器和模型
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )
        
        MODELS[model_name] = model
        TOKENIZERS[model_name] = tokenizer
        
        logger.info(f"成功加载模型: {model_name}")
        return model, tokenizer
    
    except Exception as e:
        logger.error(f"加载模型 {model_name} 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加载模型失败: {str(e)}")

@router.post("/deepseek_chat", response_model=ChatResponse)
async def deepseek_chat(request: ChatRequest = Body(...)):
    """与Deepseek模型进行聊天"""
    try:
        query = request.query
        history = request.history
        temperature = request.temperature
        max_tokens = request.max_tokens
        model_name = request.model
        model_path = request.model_path
        
        logger.info(f"收到聊天请求: {query[:100]}...")
        
        # 加载模型
        model, tokenizer = load_model(model_name, model_path)
        
        # 格式化历史记录
        formatted_history = []
        for i in range(0, len(history), 2):
            if i+1 < len(history):
                formatted_history.append({
                    "role": "user", 
                    "content": history[i]["content"]
                })
                formatted_history.append({
                    "role": "assistant", 
                    "content": history[i+1]["content"]
                })
        
        # 添加当前查询
        messages = formatted_history + [{"role": "user", "content": query}]
        
        # 生成回复
        inputs = tokenizer.apply_chat_template(
            messages, 
            tokenize=True, 
            return_tensors="pt"
        ).to(model.device)
        
        # 设置生成参数
        gen_kwargs = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "do_sample": temperature > 0,
        }
        
        # 生成回复
        with torch.no_grad():
            outputs = model.generate(inputs, **gen_kwargs)
            response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        logger.info(f"生成回复: {response[:100]}...")
        
        return ChatResponse(
            response=response,
            status="success"
        )
    
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        return ChatResponse(
            response="",
            status="error",
            message=f"处理请求时出错: {str(e)}"
        )

# 自动预加载模型
@router.on_event("startup")
async def startup_event():
    """应用启动时预加载模型"""
    try:
        logger.info("预加载Deepseek模型...")
        load_model("deepseek-r1-1.5b")
    except Exception as e:
        logger.error(f"预加载模型失败: {str(e)}")

# 资源释放
@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时释放模型资源"""
    global MODELS, TOKENIZERS
    logger.info("释放模型资源...")
    MODELS.clear()
    TOKENIZERS.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache() 