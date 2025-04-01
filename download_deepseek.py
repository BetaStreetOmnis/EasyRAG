#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
从ModelScope下载Deepseek模型的辅助脚本
使用方法: python download_deepseek.py [--model_id MODEL_ID] [--save_path SAVE_PATH]
"""

import os
import sys
import argparse

def download_model(model_id, save_path=None):
    """
    从ModelScope下载模型

    参数:
        model_id: ModelScope上的模型ID
        save_path: 本地保存路径
    """
    try:
        from modelscope import snapshot_download
        
        print(f"开始从ModelScope下载模型: {model_id}")

        if save_path is None:
            # 默认保存到models_file/models目录
            model_name = os.path.basename(model_id)
            save_path = os.path.join("models_file", "models", model_name)

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        print(f"模型将被保存到: {save_path}")
        print("下载过程可能需要一些时间，请耐心等待...")

        try:
            # 使用snapshot_download下载模型
            model_dir = snapshot_download(model_id, 
                                         cache_dir=os.path.dirname(save_path))
            print(f"模型成功下载到: {model_dir}")
            return True
        except Exception as e:
            print(f"下载模型时出错: {str(e)}")
            return False
            
    except ImportError:
        print("未安装modelscope，正在安装...")
        os.system(f"{sys.executable} -m pip install modelscope -i https://mirrors.aliyun.com/pypi/simple/")
        print("安装完成，重新尝试下载")
        return download_model(model_id, save_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从ModelScope下载模型")
    parser.add_argument("--model_id", type=str, default="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                        help="ModelScope模型ID")
    parser.add_argument("--save_path", type=str, default="models_file\models\DeepSeek-R1-Distill-Qwen-1.5B",
                        help="保存路径")
    
    args = parser.parse_args()
    
    # 下载模型
    success = download_model(args.model_id, args.save_path)
    
    if success:
        print("模型下载完成!")
    else:
        print("模型下载失败，请检查网络连接和参数后重试")
        sys.exit(1) 