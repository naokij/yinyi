"""
AI 分析器 - 支持多种后端（vLLM / Ollama）
"""

import json
import base64
from pathlib import Path
from typing import Optional
import httpx
import os

from database import SessionLocal
from models import Photo as PhotoModel, Analysis as AnalysisModel
from config import settings


ANALYSIS_PROMPT = """你是一位温暖细腻的影像叙事者。请分析这张照片，从以下角度给出你的理解：

1. **画面内容**：描述照片中的场景、人物、物品和氛围
2. **感性文案**：用30字以内，写一句温暖、感性的短句，唤起美好回忆。风格参考："那天的阳光正好，风也温柔"、"有些瞬间，值得被永远珍藏"
3. **回忆价值**：1-10分，这张照片有多值得被记住？
4. **美观度**：1-10分，画面的构图、光线、色彩如何？
5. **情感标签**：选择一个最贴切的标签：happy（欢乐）、warm（温馨）、nostalgic（怀旧）、peaceful（宁静）、romantic（浪漫）、energetic（活力）
6. **关键词**：3-5个描述照片内容的关键词

请以 JSON 格式返回，不要包含任何 markdown 标记：
{
    "description": "画面描述",
    "caption": "感性文案",
    "memory_score": 8.5,
    "aesthetic_score": 7.0,
    "sentiment": "warm",
    "tags": ["标签1", "标签2", "标签3"]
}"""


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_with_vllm(image_base64: str, api_url: str, model: str) -> dict:
    """使用 vLLM 分析"""
    response = httpx.post(
        f"{api_url}/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        },
        timeout=120.0
    )
    
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    
    # 解析 JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            raise ValueError(f"无法解析 AI 返回: {content}")


def analyze_with_ollama(image_base64: str, api_url: str, model: str) -> dict:
    """使用 Ollama 分析"""
    response = httpx.post(
        f"{api_url}/api/generate",
        json={
            "model": model,
            "prompt": ANALYSIS_PROMPT,
            "images": [image_base64],
            "stream": False,
            "format": "json"
        },
        timeout=120.0
    )
    
    response.raise_for_status()
    result = response.json()
    content = result['response']
    
    # Ollama 的返回已经是 JSON 格式（如果指定了 format: json）
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 如果不是标准 JSON，尝试解析
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            raise ValueError(f"无法解析 AI 返回: {content}")


def analyze_photo_task(photo_id: int):
    """分析单张照片（后台任务）"""
    db = SessionLocal()
    
    try:
        photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
        if not photo:
            print(f"❌ 照片不存在: {photo_id}")
            return
        
        if photo.status == "analyzed":
            print(f"⏭️ 照片已分析，跳过: {photo.filename}")
            return
        
        print(f"🤖 开始分析: {photo.filename}")
        photo.status = "analyzing"
        db.commit()
        
        # 检查文件是否存在
        if not Path(photo.path).exists():
            print(f"❌ 文件不存在: {photo.path}")
            photo.status = "error"
            db.commit()
            return
        
        # 编码图片
        try:
            image_base64 = encode_image_to_base64(photo.path)
        except Exception as e:
            print(f"❌ 图片编码失败: {e}")
            photo.status = "error"
            db.commit()
            return
        
        # 选择后端
        ai_backend = os.getenv('AI_BACKEND', 'vllm')
        
        try:
            if ai_backend == 'ollama':
                print(f"   使用 Ollama 后端")
                model = os.getenv('OLLAMA_MODEL', 'qwen2.5-vl:7b')
                api_url = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
                analysis_data = analyze_with_ollama(image_base64, api_url, model)
                model_name = model
            else:
                print(f"   使用 vLLM 后端")
                api_url = settings.VLLM_HOST
                model = settings.VLLM_MODEL
                analysis_data = analyze_with_vllm(image_base64, api_url, model)
                model_name = model
            
            # 保存分析结果
            analysis = AnalysisModel(
                photo_id=photo.id,
                description=analysis_data.get('description', ''),
                caption=analysis_data.get('caption', ''),
                tags=json.dumps(analysis_data.get('tags', []), ensure_ascii=False),
                memory_score=float(analysis_data.get('memory_score', 5.0)),
                aesthetic_score=float(analysis_data.get('aesthetic_score', 5.0)),
                sentiment=analysis_data.get('sentiment', 'warm'),
                model=model_name
            )
            
            db.add(analysis)
            photo.status = "analyzed"
            db.commit()
            
            print(f"✅ 分析完成: {photo.filename}")
            print(f"   文案: {analysis.caption}")
            print(f"   回忆度: {analysis.memory_score}/10")
            
        except httpx.TimeoutException:
            print(f"⏱️ 分析超时: {photo.filename}")
            photo.status = "pending"
            db.commit()
        except Exception as e:
            print(f"❌ AI 分析失败: {e}")
            photo.status = "error"
            db.commit()
    
    except Exception as e:
        print(f"❌ 分析任务异常: {e}")
        db.rollback()
    finally:
        db.close()
