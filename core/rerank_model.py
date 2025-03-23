import torch
import torch.nn.functional as F
import logging
import traceback
from modelscope import AutoModelForSequenceClassification, AutoTokenizer

# 配置日志
logger = logging.getLogger(__name__)

# 初始化变量
model = None
tokenizer = None

def load_rerank_model():
    """
    加载重排序模型，并处理可能的错误
    """
    global model, tokenizer
    
    try:
        if model is None or tokenizer is None:
            logger.info("正在加载重排序模型...")
            # 模型路径
            model_name_or_path = "iic/gte_passage-ranking_multilingual-base"
            
            # 加载分词器和模型
            tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_name_or_path, trust_remote_code=True)
            model.eval()
            
            logger.info("重排序模型加载成功")
            return True
    except Exception as e:
        logger.error(f"加载重排序模型失败: {str(e)}")
        logger.exception(e)
        model = None
        tokenizer = None
        return False

# 尝试预加载模型
load_rerank_model()

def reranker(query, documents):
    """
    对文档进行重排序
    
    Args:
        query: 查询文本
        documents: 文档列表
        
    Returns:
        List[Tuple]: 按相关性排序的(文档,分数)列表
    """
    global model, tokenizer
    
    # 检查输入
    if not query or not documents:
        logger.warning("查询或文档列表为空，无法进行重排序")
        return [(doc, 0.0) for doc in documents]
    
    # 确保模型已加载
    if model is None or tokenizer is None:
        success = load_rerank_model()
        if not success:
            logger.error("无法加载重排序模型，返回原始顺序")
            return [(doc, 50.0) for doc in documents]  # 返回默认分数
    
    try:
        with torch.no_grad():
            # 创建(查询,文档)对
            pairs = [[query, text] for text in documents]
            
            # 分词
            inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=8192)
            
            # 通过模型获取分数
            scores = model(**inputs, return_dict=True).logits.view(-1, ).float()
            
            # 转换为概率
            probabilities = F.softmax(scores, dim=0) * 100
            
            # 组合文档和概率
            ranked_results = list(zip(documents, probabilities.tolist()))
            
            # 按概率降序排序
            ranked_results.sort(key=lambda x: x[1], reverse=True)
            
            return ranked_results
    except Exception as e:
        logger.error(f"重排序过程中出错: {str(e)}")
        logger.exception(e)
        # 发生错误时返回原始顺序
        return [(doc, 50.0) for doc in documents]
    



    
