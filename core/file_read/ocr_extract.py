# 安装
# pip install easyocr
import os
import logging
import cv2
from modelscope import snapshot_download
import easyocr
import torch
import traceback
import gc
import subprocess
import tempfile
import json
import sys

os.environ['MODELSCOPE_CACHE'] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models_file')
os.environ["OMP_NUM_THREADS"] = "4"  # 限制OpenMP线程数
os.environ["MKL_NUM_THREADS"] = "4"  # 限制MKL线程数

logger = logging.getLogger(__name__)
# 确保日志配置正确
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def extract_text_with_easyocr(image_path):
    """使用EasyOCR提取图片中的文字"""
    try:
        logger.info(f"开始处理图片: {image_path}")
        # 下载EasyOCR模型到指定目录
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models_file', 'easyocr')
        logger.info(f"模型目录: {model_dir}")
        if not os.path.exists(model_dir):
            logger.info(f"模型目录不存在，创建目录并下载模型")
            os.makedirs(model_dir, exist_ok=True)
            try:
                snapshot_download('Ceceliachenen/easyocr', cache_dir=model_dir)
                logger.info("模型下载完成")
            except Exception as e:
                logger.error(f"模型下载失败: {str(e)}")
                logger.error(traceback.format_exc())
        
        # 检查图片是否存在且可读
        logger.info(f"读取图片: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"无法读取图片: {image_path}")
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 图像尺寸限制 - 保持纵横比的情况下缩小图像
        max_dimension = 1600  # 设置最大尺寸
        height, width = img.shape[:2]
        
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
            logger.info(f"图像已缩放至 {new_width}x{new_height} 以减少内存使用")
        
        # 如果是CPU环境，限制内存使用
        gpu = torch.cuda.is_available()
        logger.info(f"GPU可用: {gpu}")
        if not gpu:
            logger.info("在CPU环境下运行EasyOCR，使用限制内存的配置")
            torch.set_num_threads(4)  # 限制PyTorch线程数
            
            reader = easyocr.Reader(
                ['ch_sim', 'en'], 
                model_storage_directory=model_dir,
                gpu=False,
                download_enabled=False,
                quantize=True,  # 模型量化
                # 移除不支持的参数
                # recognizer_network='small',  # 使用小型识别网络
                detector=True,  # 启用检测器
                cudnn_benchmark=False
            )
            logger.info("CPU模式下EasyOCR初始化成功")
        else:
            try:
                logger.info("GPU模式下初始化EasyOCR")
                reader = easyocr.Reader(['ch_sim', 'en'], model_storage_directory=model_dir)
                logger.info("GPU模式下EasyOCR初始化成功")
            except Exception as e:
                logger.error(f"GPU模式下EasyOCR初始化失败: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        # 执行OCR识别
        logger.info("开始执行OCR识别")
        try:
            result = reader.readtext(img)  # 直接传递图像对象而不是路径
            logger.info(f"OCR识别完成，识别到{len(result)}个文本区域")
        except Exception as e:
            logger.error(f"OCR识别过程失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
        # 处理后主动清理内存
        del img
        gc.collect()
        
        # 处理结果
        text = ""
        for detection in result:
            text += detection[1] + "\n"
        
        logger.info(f"OCR提取完成，提取文本长度: {len(text)}")
        return text
    except Exception as e:
        logger.error(f"OCR提取文本失败: {str(e)}")
        logger.error(traceback.format_exc())
        return f"OCR提取失败: {str(e)}"

def extract_text_with_subprocess(image_path):
    """使用子进程处理OCR，避免主进程内存溢出"""
    # 创建临时脚本
    script_content = """
import sys
import os
import traceback
import json

def process_image(image_path):
    try:
        # 检查图片是否存在
        if not os.path.exists(image_path):
            return {"success": False, "error": f"图片文件不存在: {image_path}"}
            
        # 确保图片有效
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": f"无法读取图片: {image_path}"}
        
        # 图像尺寸限制
        max_dimension = 1600
        height, width = img.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
            
        # 存储调整后的图片到临时文件
        temp_img_path = image_path + ".resized.png"
        cv2.imwrite(temp_img_path, img)
        
        # 导入OCR库
        try:
            import easyocr
        except ImportError as e:
            return {"success": False, "error": f"导入easyocr失败: {str(e)}"}
            
        # 使用简化参数初始化OCR
        try:
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        except Exception as e:
            return {"success": False, "error": f"初始化OCR失败: {str(e)}\\n{traceback.format_exc()}"}
            
        # 执行OCR
        try:
            result = reader.readtext(temp_img_path)
            
            # 清理临时文件
            try:
                os.remove(temp_img_path)
            except:
                pass
                
            text = "\\n".join([r[1] for r in result if len(r) >= 2])
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": f"OCR处理失败: {str(e)}\\n{traceback.format_exc()}"}
    except Exception as e:
        error_trace = traceback.format_exc()
        return {"success": False, "error": f"{str(e)}\\n{error_trace}"}

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"success": False, "error": "未提供图片路径参数"}))
            sys.exit(1)
            
        image_path = sys.argv[1]
        print(f"处理图片: {image_path}", file=sys.stderr)
        result = process_image(image_path)
        print(json.dumps(result))
    except Exception as e:
        error_trace = traceback.format_exc()
        print(json.dumps({
            "success": False, 
            "error": f"脚本执行错误: {str(e)}\\n{error_trace}"
        }))
        sys.exit(1)
"""
    
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as f:
        f.write(script_content)
        temp_script = f.name
    
    try:
        # 确保图片路径存在
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return f"OCR处理失败: 图片文件不存在 {image_path}"
            
        # 在子进程中运行OCR
        logger.info(f"启动OCR子进程处理图片: {image_path}")
        
        # 使用更详细的错误捕获
        try:
            result = subprocess.check_output(
                [sys.executable, temp_script, image_path],
                stderr=subprocess.PIPE,
                timeout=180  # 增加超时时间到3分钟
            )
            
            # 打印stderr输出以便调试
            # stderr_output = result[1].decode('utf-8', errors='replace')
            # if stderr_output:
            #     logger.info(f"OCR子进程stderr输出: {stderr_output}")
                
            # 解析结果
            result_text = result.decode('utf-8', errors='replace').strip()
            try:
                result_json = json.loads(result_text)
            except json.JSONDecodeError:
                logger.error(f"无法解析OCR子进程输出为JSON: {result_text}")
                return f"OCR处理失败: 无法解析子进程输出"
                
            if result_json.get("success"):
                text = result_json.get("text", "")
                logger.info(f"OCR处理完成，提取文本长度: {len(text)}")
                return text
            else:
                error = result_json.get("error", "未知错误")
                logger.error(f"子进程OCR处理失败: {error}")
                return f"OCR处理失败: {error}"
                
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
            logger.error(f"OCR子进程返回错误码 {e.returncode}: {stderr}")
            return f"OCR处理失败: 子进程返回错误码 {e.returncode}"
            
        except subprocess.TimeoutExpired:
            logger.error("OCR处理超时")
            return "OCR处理超时"
            
    except Exception as e:
        logger.error(f"子进程OCR异常: {e}")
        logger.error(traceback.format_exc())
        return f"OCR处理异常: {str(e)}"
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_script):
                os.unlink(temp_script)
        except Exception as e:
            logger.error(f"删除临时脚本文件失败: {e}")

if __name__ == "__main__":
    image_path = r"C:\Users\Administrator\Pictures\6f5e8e856931b71c6f6ec842dc08ea7.png"
    logger.info(f"测试OCR功能，处理图片: {image_path}")
    text2 = extract_text_with_subprocess(image_path)
    print("\n子进程OCR结果:")
    print(text2)
