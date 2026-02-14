"""
AI 分析器 - 支持多种后端（vLLM / Ollama / 心流）
"""

import json
import base64
from pathlib import Path
import httpx
import os
import threading
import time

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path, override=True)

from database import SessionLocal, Photo as PhotoModel, Analysis as AnalysisModel
from config import settings

# iflow API 并发限制为 1，使用锁确保同时只分析一张照片
iflow_lock = threading.Lock()


ANALYSIS_PROMPT = """你是一个个人相册照片评估助手，擅长理解真实照片内容并从回忆价值和美观角度打分。

## 任务
1) 用中文详细描述照片内容（80-200字）
2) 判断照片类型（可选多个）：人物/孩子/猫咪/宠物/家庭/旅行/风景/美食/日常/文档/杂物/其他
3) 给出 0-100 的值得回忆度 memory_score（精确到1位小数）
4) 给出 0-100 的美观程度 beauty_score（精确到1位小数）
5) 用简短中文解释评分原因（不超过60字）

## 回忆分 memory_score 评分标准

### 得分区间：
- 垃圾/随手拍/无意义记录：40分以下
- 稍微有点可回忆价值：以65分为中心
- 不错的回忆价值：以75分为中心
- 特别精彩、强烈值得珍藏：以85分为中心

### 加分项：
- 人物与关系：画面有面积较大的人脸，有人互动或合影 -> 大幅提高
- 事件性：生日/聚会/仪式/舞台/明显事件 -> 少许提高
- 稀缺性与不可复现：这一刻很难再来一次 -> 大幅提高
- 情绪强度：笑、哭、惊喜、拥抱、互动 -> 少许提高
- 孩子/猫咪/宠物：这些主题更容易产生高回忆值，直接以75分为中心并大幅提高
- 优美风景：壮丽的自然风光或精美构图 -> 少许提高
- 旅行意义：异地、地标、旅途情景 -> 少许提高

### 减分项：
- 画质问题：模糊、残影、虚焦 -> 微微降低

### 必须压到 0-25 分的情况：
- 屏幕截图（包含大量文字、UI界面、对话框等）
- 账单/收据/广告/文档
- 测试图片/随手拍的杂物
- 裸露/低俗/违反公序良俗的图片

## 美观分 beauty_score 评分标准
只评价视觉质量：构图、光线、清晰度、色彩、主体突出。
不要被孩子/猫/旅行主题绑架。

## 输出格式
请严格只输出 JSON：
{"description": "详细描述照片内容", "type": "人物/家庭/旅行", "memory_score": 85.5, "beauty_score": 78.0, "reason": "简短解释"}
不要输出任何多余文字，不要加注释。"""


CAPTION_PROMPT = """你是一位为电子相框撰写旁白的中文文案助手。

## 创作原则
1. 避免使用：世界、梦、时光、岁月、温柔、治愈、刚刚好、悄悄、慢慢等词
2. 严禁句式：……里……着整个世界；……里……着整个夏天；得像……；比……还……
3. 只基于图片中能确定的信息联想，不要虚构时间、人物关系、事件背景
4. 不要复述画面内容本身，而是写"看完画面后，心里多出来的一句话"
5. 可以偏向：日常中的微妙情绪；轻微自嘲或冷幽默；对时间、记忆的瞬间感受
6. 避免小学生作文式的套路化表达

## 格式要求
- 只输出一句中文短句，不要换行，不要引号
- 建议长度 8-24 个汉字，最多不超过 30 个
- 不要出现"这张照片"、"这一刻"、"那天"等指代照片本身的词"""


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_result(content: str) -> dict:
    import re
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        raise ValueError(f"无法解析 AI 返回: {content}")


def call_vlm(image_base64: str, prompt: str, api_url: str, model: str) -> dict:
    response = httpx.post(
        f"{api_url}/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        },
        timeout=120.0
    )
    response.raise_for_status()
    return parse_result(response.json()["choices"][0]["message"]["content"])


def call_ollama(image_base64: str, prompt: str, api_url: str, model: str) -> dict:
    response = httpx.post(
        f"{api_url}/api/generate",
        json={"model": model, "prompt": prompt, "images": [image_base64], "stream": False, "format": "json"},
        timeout=180.0
    )
    response.raise_for_status()
    return parse_result(response.json()["response"])


def call_iflow(image_base64: str, prompt: str, api_key: str, base_url: str, model: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = httpx.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        },
        timeout=120.0
    )
    response.raise_for_status()
    
    # Debug: print response structure
    resp_json = response.json()
    print(f"  [DEBUG] Response keys: {list(resp_json.keys())}")
    
    if "choices" not in resp_json:
        print(f"  [DEBUG] Full response: {resp_json}")
        raise ValueError(f"API response missing 'choices' key. Keys: {list(resp_json.keys())}")
    
    return parse_result(resp_json["choices"][0]["message"]["content"])


def generate_caption(image_base64: str, description: str, api_key: str, base_url: str, model: str) -> str:
    prompt = f"{CAPTION_PROMPT}\n\n照片描述：{description}\n请生成一句文案。"
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 64,
                "temperature": 0.7
            },
            timeout=60.0
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        # 文案是直接返回的文本，不是 JSON
        return content.strip() if content else ""
    except Exception as e:
        print(f"  [警告] 文案生成失败: {e}")
        return ""


def analyze_photo_task(photo_id: int):
    db = SessionLocal()
    try:
        photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
        if not photo:
            print(f"[错误] 照片不存在: {photo_id}")
            return
        if photo.status == "analyzed":
            print(f"[跳过] 照片已分析，跳过: {photo.filename}")
            return

        print(f"[AI] 开始分析: {photo.filename}")
        photo.status = "analyzing"
        db.commit()

        if not Path(photo.path).exists():
            print(f"[错误] 文件不存在: {photo.path}")
            photo.status = "error"
            db.commit()
            return

        try:
            image_base64 = encode_image_to_base64(photo.path)
        except Exception as e:
            print(f"[错误] 图片编码失败: {e}")
            photo.status = "error"
            db.commit()
            return

        ai_backend = os.getenv("AI_BACKEND", "ollama")
        api_key = os.getenv("IFLOW_API_KEY") or ""
        base_url = os.getenv("IFLOW_BASE_URL", "https://apis.iflow.cn/v1")
        model = os.getenv("IFLOW_MODEL", "qwen3-vl-plus")
        print(f"  AI 后端: {ai_backend}")

        try:
            # iflow API 并发限制为 1，使用锁
            if ai_backend == "iflow":
                print(f"  [iflow] 等待锁，确保单并发...")
                with iflow_lock:
                    print(f"  [iflow] 获取锁，开始分析...")
                    # 第一次调用：打分
                    score_result = call_iflow(image_base64, ANALYSIS_PROMPT, api_key, base_url, model)
                    
                    memory_score = float(score_result.get("memory_score", 50.0))
                    aesthetic_score = float(score_result.get("beauty_score", 50.0))
                    photo_type = score_result.get("type", "")
                    description = score_result.get("description", "")
                    reason = score_result.get("reason", "")
                    
                    print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")
                    
                    # 第二次调用：生成文案（仅高分照片：回忆分 >= 60）
                    caption = ""
                    if memory_score >= 60:
                        print(f"  正在生成文案...")
                        caption = generate_caption(image_base64, description, api_key, base_url, model)
                        print(f"  文案: {caption[:30] if caption else '(无)'}...")
                    else:
                        print(f"  回忆分 < 60，跳过文案生成")
                    
                    print(f"  [iflow] 释放锁")
            elif ai_backend == "ollama":
                score_result = call_ollama(image_base64, ANALYSIS_PROMPT, "http://localhost:11434", model)
                
                memory_score = float(score_result.get("memory_score", 50.0))
                aesthetic_score = float(score_result.get("beauty_score", 50.0))
                photo_type = score_result.get("type", "")
                description = score_result.get("description", "")
                reason = score_result.get("reason", "")
                
                print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")
                
                caption = ""
                if memory_score >= 60:
                    print(f"  正在生成文案...")
                    caption = generate_caption(image_base64, description, "", "http://localhost:11434", model)
                    print(f"  文案: {caption[:30] if caption else '(无)'}...")
                else:
                    print(f"  回忆分 < 60，跳过文案生成")
            else:
                score_result = call_vllm(image_base64, ANALYSIS_PROMPT, os.getenv("VLLM_HOST"), model)
                
                memory_score = float(score_result.get("memory_score", 50.0))
                aesthetic_score = float(score_result.get("beauty_score", 50.0))
                photo_type = score_result.get("type", "")
                description = score_result.get("description", "")
                reason = score_result.get("reason", "")
                
                print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")
                
                caption = ""
                if memory_score >= 60:
                    print(f"  正在生成文案...")
                    caption = generate_caption(image_base64, description, "", os.getenv("VLLM_HOST"), model)
                    print(f"  文案: {caption[:30] if caption else '(无)'}...")
                else:
                    print(f"  回忆分 < 60，跳过文案生成")

            analysis = AnalysisModel(
                photo_id=photo.id,
                description=description,
                caption=caption,
                tags=json.dumps(photo_type.split(","), ensure_ascii=False),
                memory_score=memory_score,
                aesthetic_score=aesthetic_score,
                sentiment=photo_type.split(",")[0].strip() if photo_type else "其他",
                photo_type=photo_type,
                reason=reason,
                model=f"iflow/{model}" if ai_backend == "iflow" else (model if ai_backend == "ollama" else "vllm")
            )

            db.add(analysis)
            photo.status = "analyzed"
            db.commit()

            print(f"[完成] {photo.filename}")
            print(f"  类型: {photo_type}")
            print(f"  回忆分: {memory_score:.1f}/100")

        except httpx.TimeoutException:
            print(f"[超时] {photo.filename}")
            photo.status = "pending"
            db.commit()
        except Exception as e:
            print(f"[错误] AI 分析失败: {e}")
            photo.status = "error"
            db.commit()

    except Exception as e:
        print(f"[错误] 分析任务异常: {e}")
        db.rollback()
    finally:
        db.close()


def call_vllm(image_base64: str, prompt: str, api_url: str, model: str) -> dict:
    response = httpx.post(
        f"{api_url}/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2
        },
        timeout=120.0
    )
    response.raise_for_status()
    return parse_result(response.json()["choices"][0]["message"]["content"])
