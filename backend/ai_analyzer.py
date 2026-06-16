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

# API 并发控制：agnes 限速 20 RPM，3 并发相对安全（且单 worker 满载时仍有 5s/req 余量）
# 由 batch 路由层用 ThreadPoolExecutor 限制总 worker 数，本处额外限 mimo/agnes 调用并发
MAX_CONCURRENT_API_CALLS = int(os.getenv("MAX_CONCURRENT_API_CALLS", "3"))
iflow_call_semaphore = threading.Semaphore(MAX_CONCURRENT_API_CALLS)

# 是否生成感性文案 caption（默认关闭，避免双倍 API 调用；用户需要时在 .env 开启）
ENABLE_CAPTION = os.getenv("ENABLE_CAPTION", "false").lower() in ("1", "true", "yes", "on")
# caption 阶段是否启用 thinking（默认关闭，开放式任务易触发死循环，content 为空）
ENABLE_CAPTION_THINKING = os.getenv("ENABLE_CAPTION_THINKING", "false").lower() in ("1", "true", "yes", "on")
# caption 记忆分阈值（默认 70，仅对真正有价值的照片才生成文案）
CAPTION_MIN_MEMORY = float(os.getenv("CAPTION_MIN_MEMORY", "70"))

# 评分调用是否启用 thinking
ENABLE_THINKING = os.getenv("ENABLE_THINKING", "true").lower() in ("1", "true", "yes", "on")

# 全局分析器状态
_analyzer_state = {
    "status": "idle",  # idle, analyzing
    "started_at": None,
    "lock": threading.Lock()
}


def set_analyzer_status(status: str):
    """设置分析器状态"""
    with _analyzer_state["lock"]:
        _analyzer_state["status"] = status
        from datetime import datetime
        if status == "analyzing":
            _analyzer_state["started_at"] = datetime.now()


def get_analyzer_status() -> dict:
    """获取分析器状态"""
    with _analyzer_state["lock"]:
        return {
            "status": _analyzer_state["status"],
            "started_at": _analyzer_state["started_at"]
        }


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


def encode_image_to_base64(image_path: str) -> str:
    """
    将图片转为 base64，压缩到 1024 边长以控制内存和 API token 消耗。
    Agnes 图片 token：h_bar/16 * w_bar/16 / 4，1024 边约 1024 tokens。
    """
    from PIL import Image
    import io

    img = Image.open(image_path)

    # 转换为 RGB（去除透明通道）
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # 强制压到 1024 边长（内存节省 ~75%，token 节省 ~67%）
    MAX_DIM = 1024
    if max(img.size) > MAX_DIM:
        ratio = MAX_DIM / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)
    compressed = buffer.read()
    img.close()

    print(f"  [编码] 压缩后: {len(compressed)/1024/1024:.2f}MB ({img.size[0]}x{img.size[1]})")
    return base64.b64encode(compressed).decode("utf-8")


# caption 校验：thinking model 偶尔会把 prompt+推理过程回显到 content
# 正常文案应短（< 50 字符）、不包含 prompt 关键词
CAPTION_PROMPT_KEYWORDS = [
    "首先", "其次", "用户", "创作原则", "画外之意", "电子相框",
    "请生成", "请输出", "格式要求", "如下", "要求", "指令", "思考",
    "分析", "判断", "应该", "根据", "原则", "风格", "避免使用",
    "严禁", "照片描述：", "不能", "基于图片",
]


def validate_caption(raw: str) -> str:
    """校验并清洗 caption：
    - 长度 > 50 字符 → 丢弃（正常文案 8-24 字）
    - 包含 prompt 关键词 → 丢弃（说明模型回显了 prompt 或思考过程）
    - 末尾省略号/逗号 → 截断标志，丢弃
    - markdown code block → 尝试提取最后一行
    返回清洗后的 caption；不合格返回空字符串
    """
    if not raw:
        return ""
    text = raw.strip()

    # 1. markdown code block: 提取 ``` ... ``` 内的内容
    if text.startswith("```") and text.endswith("```"):
        # 拿掉首尾 ``` 后，剥掉 language tag（如 ```json），剩下的 body
        body = text.strip("`").strip()
        if body.startswith(("json", "JSON")):
            body = body[4:].strip()
        # 优先提取 "caption": "..." 字段
        import re
        m = re.search(r'"caption"\s*:\s*"([^"]+)"', body)
        if m and 4 <= len(m.group(1)) <= 50:
            text = m.group(1)
        else:
            # 否则按行找最短的非空行
            lines = [l.strip() for l in body.split("\n") if l.strip() and not l.strip().startswith(("{", "}"))]
            candidates = [l for l in lines if 4 <= len(l) <= 50]
            if candidates:
                text = min(candidates, key=len)

    # 2. 截断标志
    if text.endswith(("...", "，", "、", " ", ";")):
        print(f"  [caption] 丢弃（截断标志）: {text[:60]!r}")
        return ""

    # 3. prompt 回显检测
    for kw in CAPTION_PROMPT_KEYWORDS:
        if kw in text:
            print(f"  [caption] 丢弃（含 prompt 关键词 {kw!r}）: {text[:60]!r}")
            return ""

    # 4. 长度检查
    if len(text) > 50:
        print(f"  [caption] 丢弃（过长 {len(text)} 字符）: {text[:60]!r}")
        return ""

    # 5. 至少 4 字符
    if len(text) < 4:
        return ""

    return text


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


def call_iflow(image_base64: str, prompt: str, api_key: str, base_url: str, model: str, enable_thinking: bool = True) -> dict:
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
        "max_tokens": 4000,
        "temperature": 0.7
    }
    # mimo thinking 是默认开启的（用 thinking.type=disabled 关掉）；agnes 用 chat_template_kwargs 显式开启
    if not enable_thinking:
        if "xiaomimimo" in base_url:
            request_body["thinking"] = {"type": "disabled"}
    else:
        if "agnes" in base_url:
            request_body["chat_template_kwargs"] = {"enable_thinking": True}

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

        if response.status_code == 400:
            print(f"  [ERROR] HTTP 400 Bad Request")
            print(f"  [ERROR] Response body: {response.text}")
            raise ValueError(f"API 400 Error: {response.text}")

        response.raise_for_status()

        resp_json = response.json()
        if "choices" not in resp_json:
            print(f"  [DEBUG] Full response: {resp_json}")
            raise ValueError(f"API response missing 'choices' key. Keys: {list(resp_json.keys())}")

        message = resp_json["choices"][0]["message"]
        content = message.get("content") or ""
        if not content and message.get("reasoning_content"):
            content = message["reasoning_content"]

        usage = resp_json.get("usage", {})
        details = usage.get("completion_tokens_details", {})
        reasoning_tokens = details.get("reasoning_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        if reasoning_tokens:
            print(f"  [DEBUG] Thinking model: {reasoning_tokens} reasoning + {completion_tokens - reasoning_tokens} content tokens")

        return parse_result(content)

    except httpx.HTTPStatusError as e:
        print(f"  [ERROR] HTTP Error: {e.response.status_code}")
        print(f"  [ERROR] Response: {e.response.text}")
        raise


def generate_caption(image_base64: str, description: str, api_key: str, base_url: str, model: str) -> str:
    prompt = f"{CAPTION_PROMPT}\n\n照片描述：{description}\n请生成一句文案。"
    # caption 是否启用 thinking 由 ENABLE_CAPTION_THINKING 控制（默认 false，因开放式任务易死循环）
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
        "max_tokens": 1000,
        "temperature": 0.7
    }
    if not ENABLE_CAPTION_THINKING:
        if "xiaomimimo" in base_url:
            request_body["thinking"] = {"type": "disabled"}
        # agnes 默认 thinking=off，不加 chat_template_kwargs
    else:
        if "agnes" in base_url:
            request_body["chat_template_kwargs"] = {"enable_thinking": True}
        # mimo thinking 默认开启，无需额外参数
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=request_body,
            timeout=120.0
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]
        content = message.get("content") or ""
        if not content and message.get("reasoning_content"):
            content = message["reasoning_content"]
        return content.strip() if content else ""
    except Exception as e:
        print(f"  [警告] 文案生成失败: {e}")
        return ""


def analyze_photo_task(photo_id: int):
    # 设置分析器状态为进行中
    set_analyzer_status("analyzing")
    
    db = SessionLocal()
    try:
        photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
        if not photo:
            print(f"[错误] 照片不存在: {photo_id}")
            set_analyzer_status("idle")
            return
        if photo.status == "analyzed":
            print(f"[跳过] 照片已分析，跳过: {photo.filename}")
            set_analyzer_status("idle")
            return

        # 防御性 zombie 检测
        # 情况 A：status=analyzing + 分析完整 → 上次崩溃，直接跳过
        if photo.status == "analyzing" and photo.analysis and photo.analysis.model and photo.analysis.memory_score is not None:
            print(f"[zombie 修复] analysis 完整但 status 卡住，重置为 analyzed: {photo.filename}")
            photo.status = "analyzed"
            db.commit()
            set_analyzer_status("idle")
            return

        # 情况 B：有残缺 analysis 行（model/mem 为 None）→ 上次崩溃+回写失败，删除旧行重新分析
        if photo.analysis and (photo.analysis.model is None or photo.analysis.memory_score is None):
            print(f"[zombie 修复] 残缺 analysis 行，删除后重试: {photo.filename}")
            db.delete(photo.analysis)
            db.commit()
            photo.status = "pending"

        print(f"[AI] 开始分析: {photo.filename}")
        photo.status = "analyzing"
        # 不单独 commit，等分析完成统一提交（避免异常时 status 卡在 analyzing）
        
        # 记录开始时间
        start_time = time.time()

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
            if ai_backend == "iflow":
                # 用 semaphore 控制 mimo/agnes API 并发（agnes 限速 20 RPM，3 并发相对安全）
                print(f"  [iflow] 等待信号量 (max={MAX_CONCURRENT_API_CALLS} 并发)...")
                with iflow_call_semaphore:
                    print(f"  [iflow] 获取信号量，开始分析...")
                    # 第一次调用：打分（受 ENABLE_THINKING 控制）
                    score_result = call_iflow(image_base64, ANALYSIS_PROMPT, api_key, base_url, model, enable_thinking=ENABLE_THINKING)

                    memory_score = float(score_result.get("memory_score", 50.0))
                    aesthetic_score = float(score_result.get("beauty_score", 50.0))
                    photo_type = score_result.get("type", "")
                    description = score_result.get("description", "")
                    reason = score_result.get("reason", "")

                    print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")

                    # 第二次调用：生成文案（受 ENABLE_CAPTION 和 CAPTION_MIN_MEMORY 控制）
                    caption = ""
                    if not ENABLE_CAPTION:
                        print(f"  [skip] caption 已禁用 (ENABLE_CAPTION=false)")
                    elif memory_score < CAPTION_MIN_MEMORY:
                        print(f"  [skip] 回忆分 {memory_score:.1f} < {CAPTION_MIN_MEMORY}，跳过文案")
                    else:
                        print(f"  正在生成文案...")
                        raw_caption = generate_caption(image_base64, description, api_key, base_url, model)
                        caption = validate_caption(raw_caption)
                        if not caption:
                            print(f"  [caption] 校验丢弃（疑似推理截断或 prompt 回显）")
                        else:
                            print(f"  文案: {caption!r}")
            elif ai_backend == "ollama":
                score_result = call_ollama(image_base64, ANALYSIS_PROMPT, "http://localhost:11434", model)
                
                memory_score = float(score_result.get("memory_score", 50.0))
                aesthetic_score = float(score_result.get("beauty_score", 50.0))
                photo_type = score_result.get("type", "")
                description = score_result.get("description", "")
                reason = score_result.get("reason", "")
                
                print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")
                
                caption = ""
                if not ENABLE_CAPTION:
                    print(f"  [skip] caption 已禁用 (ENABLE_CAPTION=false)")
                elif memory_score < CAPTION_MIN_MEMORY:
                    print(f"  [skip] 回忆分 {memory_score:.1f} < {CAPTION_MIN_MEMORY}，跳过文案")
                else:
                    print(f"  正在生成文案...")
                    raw_caption = generate_caption(image_base64, description, "", "http://localhost:11434", model)
                    caption = validate_caption(raw_caption)
                    if not caption:
                        print(f"  [caption] 校验丢弃（疑似推理截断或 prompt 回显）")
                    else:
                        print(f"  文案: {caption!r}")
            else:
                score_result = call_vllm(image_base64, ANALYSIS_PROMPT, os.getenv("VLLM_HOST"), model)
                
                memory_score = float(score_result.get("memory_score", 50.0))
                aesthetic_score = float(score_result.get("beauty_score", 50.0))
                photo_type = score_result.get("type", "")
                description = score_result.get("description", "")
                reason = score_result.get("reason", "")
                
                print(f"  评分完成: 回忆分={memory_score:.1f}, 美观分={aesthetic_score:.1f}")
                
                caption = ""
                if not ENABLE_CAPTION:
                    print(f"  [skip] caption 已禁用 (ENABLE_CAPTION=false)")
                elif memory_score < CAPTION_MIN_MEMORY:
                    print(f"  [skip] 回忆分 {memory_score:.1f} < {CAPTION_MIN_MEMORY}，跳过文案")
                else:
                    print(f"  正在生成文案...")
                    raw_caption = generate_caption(image_base64, description, "", os.getenv("VLLM_HOST"), model)
                    caption = validate_caption(raw_caption)
                    if not caption:
                        print(f"  [caption] 校验丢弃（疑似推理截断或 prompt 回显）")
                    else:
                        print(f"  文案: {caption!r}")

            analysis = AnalysisModel(
                photo_id=photo.id,
                description=description,
                caption=caption,
                tags=json.dumps(photo_type if isinstance(photo_type, list) else [t.strip() for t in photo_type.split("/") if t.strip()], ensure_ascii=False),
                memory_score=memory_score,
                aesthetic_score=aesthetic_score,
                sentiment=photo_type[0].strip() if isinstance(photo_type, list) and photo_type else (photo_type.split("/")[0].strip() if photo_type else "其他"),
                photo_type=photo_type if isinstance(photo_type, str) else "/".join(photo_type) if isinstance(photo_type, list) else str(photo_type),
                reason=reason,
                model=f"iflow/{model}" if ai_backend == "iflow" else (model if ai_backend == "ollama" else "vllm")
            )

            db.add(analysis)
            photo.status = "analyzed"
            db.commit()

            # 记录分析时间（用于估算剩余时间）
            elapsed = time.time() - start_time
            from routers.scanner import record_analyze_time
            record_analyze_time(elapsed)

            print(f"[完成] {photo.filename} ({elapsed:.1f}秒)")
            print(f"  类型: {photo_type}")
            print(f"  回忆分: {memory_score:.1f}/100")

        except httpx.TimeoutException:
            print(f"[超时] {photo.filename}")
            db.rollback()
            photo.status = "pending"
            db.commit()
        except Exception as e:
            print(f"[错误] AI 分析失败: {e}")
            db.rollback()
            photo.status = "error"
            db.commit()

    except Exception as e:
        print(f"[错误] 分析任务异常: {e}")
        db.rollback()
    finally:
        # 分析完成，重置分析器状态
        set_analyzer_status("idle")
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
