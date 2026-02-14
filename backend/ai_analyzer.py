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

print("[AI模块] 已加载 - 支持图片自动压缩(10MB限制)")


ANALYSIS_PROMPT = """你是一个个人相册照片评估助手，擅长理解真实照片内容并从回忆价值和美观角度打分。

## 任务
1) 用中文详细描述照片内容（80-200字）
2) 判断照片类型（可选多个）：人物/孩子/猫咪/宠物/家庭/旅行/风景/美食/日常/文档/杂物/其他
3) 给出 0-100 的值得回忆度 memory_score（精确到1位小数）
4) 给出 0-100 的美观程度 beauty_score（精确到1位小数）
5) 用简短中文解释评分原因（不超过60字）

## 回忆分 memory_score 评分标准（参考InkTime项目标准）

### 【核心原则】
回忆分必须拉开差距，不要所有照片都集中在60-80分！

### 【得分区间定义】
1. **垃圾/随手拍/无意义记录：0-25分**（最多不超过39分）
   - 典型范围：0-25分
   - 勉强能辨认但无故事：25-39分
   - 必须压低的情况：屏幕截图、账单、收据、广告、随手拍杂物、测试图片、模糊到无法辨认的照片

2. **稍微有点可回忆价值：以65分为中心**（范围58.1-70.3）
   - 普通日常照片、一般风景、普通物品

3. **不错的回忆价值：以75分为中心**（范围68.7-82.4）
   - 有人物出镜、有意义的事件、较好的构图

4. **特别精彩、强烈值得珍藏：以85分为中心**（范围79.1-95.9）
   - 珍贵的合影、重要的人生时刻、完美构图的风景

### 【具体加分规则】
- **人物与关系**：画面中有较大面积的人脸、有人物互动、合影 → **大幅提高**（+10-20分）
- **事件性**：生日/聚会/仪式/舞台/明显事件 → **少许提高**（+5-10分）
- **稀缺性与不可复现**：明显"这一刻很难再来一次" → **大幅提高**（+10-20分）
- **情绪强度**：笑、哭、惊喜、拥抱、强烈的氛围 → **少许提高**（+5-10分）
- **信息密度**：画面能讲清楚发生了什么 → **微微提高**（+3-5分）
- **优美风景**：壮丽的自然风光、精美有秩序感的构图 → **少许提高**（+5-10分）
- **旅行意义**：异地、地标、旅途情景 → **少许提高**（+3-5分）
- **画质**：模糊、残影、虚焦 → **微微降低**（-3-5分）

### 【特殊题材处理】
- **孩子/猫咪/宠物题材**：这些主题天生容易产生高回忆值，**直接以75分为起点**，再根据具体内容调整
- **多人物合影**：根据人数和互动程度，可在基础分上额外加分

### 【必须压到0-25分的低价值图片】
- 屏幕截图（包含大量文字、UI界面、对话框等）
- 账单、收据、广告、随手拍的杂物
- 测试图片、完全模糊的废片
- 裸露、低俗、违反公序良俗的图片

## 美观分 beauty_score 评分标准
只评价视觉质量：构图、光线、清晰度、色彩、主体突出。
**不要被孩子/猫/旅行主题绑架美观分**，主题不等于好看。

## 输出格式
请严格只输出 JSON：
{"description": "详细描述照片内容", "type": "人物/家庭/旅行", "memory_score": 85.5, "beauty_score": 78.0, "reason": "简短解释"}
不要输出任何多余文字，不要加注释。"""


CAPTION_PROMPT = """你是一位为「电子相框」撰写旁白短句的中文文案助手。
你的目标不是描述画面，而是为画面补上一点"画外之意"。

## 创作原则（参考InkTime项目）
1. 避免使用以下词语：世界、梦、时光、岁月、温柔、治愈、刚刚好、悄悄、慢慢 等（但不是绝对禁止）
2. 严禁使用如下句式：
   - ……里……着整个世界
   - ……里……着整个夏天
   - ……得像……（简单的比喻）
   - ……比……还……
   - ……得比……更……
3. 只基于图片中能确定的信息进行联想，不要虚构时间、人物关系、事件背景
4. 文案应自然、有趣，带一点幽默或者诗意，但请避免煽情、鸡汤
5. 不要复述画面内容本身，而是写"看完画面后，心里多出来的一句话"
6. 可以偏向以下风格之一：
   - 日常中的微妙情绪
   - 轻微自嘲或冷幽默
   - 对时间、记忆、瞬间的含蓄感受
   - 看似平淡但有余味的一句判断
7. 避免小学生作文式的、套路式的模板化表达

## 格式要求
1. 只输出一句中文短句，不要换行，不要引号，不要任何解释
2. 建议长度 8～24 个汉字，最多不超过 30 个汉字
3. 不要出现"这张照片"、"这一刻"、"那天"等指代照片本身的词"""


def encode_image_to_base64(image_path: str, max_size_mb: float = 7.0) -> str:
    """
    将图片转为 base64，如果超过限制则压缩
    iflow API 限制: 10MB base64 (10485760 bytes)
    base64 编码会增加约 33% 大小，所以原始图片需要控制在 7MB 以内
    """
    from PIL import Image
    import io
    
    # base64 编码后增加约 33%，所以原始图片最大约 7MB
    max_bytes = int(max_size_mb * 1024 * 1024)  # 7MB = 7340032 bytes
    max_base64_bytes = int(9.5 * 1024 * 1024)  # base64 后最大 9.5MB
    
    # 先尝试直接读取
    with open(image_path, "rb") as f:
        data = f.read()
    
    # 预估 base64 编码后的大小
    estimated_base64_size = len(data) * 4 // 3
    
    print(f"  [DEBUG] 原始图片: {len(data)/1024/1024:.2f}MB, 预估base64: {estimated_base64_size/1024/1024:.2f}MB")
    
    # 如果预估 base64 小于 9.5MB，直接返回
    if estimated_base64_size <= max_base64_bytes:
        print(f"  [DEBUG] 无需压缩")
        return base64.b64encode(data).decode("utf-8")
    
    # 需要压缩
    print(f"  [压缩] 图片 {len(data)/1024/1024:.1f}MB 超过限制，开始压缩...")
    
    img = Image.open(image_path)
    
    # 转换为 RGB（去除透明通道）
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # 逐步降低质量和尺寸直到满足要求
    quality = 85
    max_dimension = 2048  # 最大边长
    
    while True:
        # 调整尺寸
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            img_resized = img
        
        # 保存到内存
        buffer = io.BytesIO()
        img_resized.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        compressed_data = buffer.read()
        
        if len(compressed_data) <= max_bytes:
            print(f"  [压缩] 完成: {len(compressed_data)/1024/1024:.1f}MB (尺寸: {img_resized.size}, 质量: {quality})")
            return base64.b64encode(compressed_data).decode("utf-8")
        
        # 还太大，继续压缩
        if quality > 50:
            quality -= 10
        elif max_dimension > 1024:
            max_dimension -= 256
        else:
            # 实在压不到 10MB，返回压缩后的版本（可能会报错，但尽力了）
            print(f"  [压缩] 警告: 无法压缩到 {max_size_mb}MB 以下，当前 {len(compressed_data)/1024/1024:.1f}MB")
            return base64.b64encode(compressed_data).decode("utf-8")


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
    
    # 构建请求体
    request_body = {
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
    }
    
    print(f"  [DEBUG] Request URL: {base_url}/chat/completions")
    print(f"  [DEBUG] Model: {model}")
    print(f"  [DEBUG] Image base64 length: {len(image_base64)} chars")
    
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=request_body,
            timeout=120.0
        )
        
        # 详细记录错误信息
        if response.status_code == 400:
            print(f"  [ERROR] HTTP 400 Bad Request")
            print(f"  [ERROR] Response body: {response.text}")
            print(f"  [ERROR] Request headers: {headers}")
            raise ValueError(f"API 400 Error: {response.text}")
        
        response.raise_for_status()
        
        # Debug: print response structure
        resp_json = response.json()
        print(f"  [DEBUG] Response keys: {list(resp_json.keys())}")
        
        if "choices" not in resp_json:
            print(f"  [DEBUG] Full response: {resp_json}")
            raise ValueError(f"API response missing 'choices' key. Keys: {list(resp_json.keys())}")
        
        return parse_result(resp_json["choices"][0]["message"]["content"])
        
    except httpx.HTTPStatusError as e:
        print(f"  [ERROR] HTTP Error: {e.response.status_code}")
        print(f"  [ERROR] Response: {e.response.text}")
        raise


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
