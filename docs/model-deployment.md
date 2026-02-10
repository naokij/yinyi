# 本地模型部署指南

## 方案一：使用 vLLM（推荐，已集成）

项目已集成 vLLM，启动 Docker 时会自动下载和运行模型。

### 启动命令

```bash
cd yinyi

# 使用默认照片目录 (./photos)
./start.sh

# 或使用自定义照片目录
PHOTOS_DIR=/Users/yourname/Pictures ./start.sh

# 后台启动（不显示日志）
docker compose up -d
```

### 首次启动流程

1. **下载 Docker 镜像**（约 2GB）
   - vllm/vllm-openai:latest
   - Python 后端镜像
   - Nginx 前端镜像

2. **下载 AI 模型**（约 4GB）
   - Qwen/Qwen3-VL-4B-Instruct
   - 自动下载到 `./data/models`
   - 下载时间：10-30 分钟（取决于网速）

3. **查看下载进度**
   ```bash
   docker logs -f yinyi-vllm
   ```
   
   看到以下日志表示启动成功：
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

### 手动管理模型

```bash
# 查看已下载的模型
docker exec yinyi-vllm ls -la /root/.cache/huggingface/

# 手动下载模型（如需提前下载）
docker exec yinyi-vllm python -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen3-VL-4B-Instruct', local_dir='/root/.cache/huggingface/hub')
"

# 删除模型重新下载
docker compose down
rm -rf ./data/models/*
docker compose up -d
```

## 方案二：使用 Ollama（备选）

如果 vLLM 在你的机器上运行有问题，可以使用 Ollama。

### 修改 docker-compose.yml

```yaml
services:
  # 替换 vllm 服务为 ollama
  ollama:
    image: ollama/ollama:latest
    container_name: yinyi-ollama
    volumes:
      - ./data/ollama:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped

  backend:
    environment:
      - OLLAMA_HOST=http://ollama:11434  # 修改这里
      # - VLLM_HOST=http://vllm:8000     # 注释掉
```

### 启动后手动拉取模型

```bash
docker exec yinyi-ollama ollama pull qwen2.5-vl:7b
```

### 修改后端配置

编辑 `backend/ai_analyzer.py`：

```python
# 将 VLLM 调用改为 Ollama
response = httpx.post(
    f"{settings.OLLAMA_HOST}/api/generate",
    json={
        "model": "qwen2.5-vl:7b",
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
)
```

## 方案三：手动运行模型（高级用户）

### 使用 transformers 直接运行

```bash
# 创建 Python 环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install torch transformers pillow accelerate

# 下载模型
python -c "
from transformers import AutoModelForVision2Seq, AutoTokenizer
model = AutoModelForVision2Seq.from_pretrained('Qwen/Qwen3-VL-4B-Instruct')
"
```

### 使用 LM Studio（GUI 工具）

1. 下载 [LM Studio](https://lmstudio.ai/)
2. 搜索并下载 Qwen3-VL-4B
3. 启动本地服务器（默认端口 1234）
4. 修改 `backend/config.py`：
   ```python
   VLLM_HOST = "http://host.docker.internal:1234/v1"
   ```

## 硬件要求对比

| 方案 | 内存需求 | 显存需求 | 速度 | 适用场景 |
|------|---------|---------|------|---------|
| vLLM | 16GB+ | 8GB+ | 快 | 有 NVIDIA GPU |
| vLLM (CPU) | 32GB+ | 无 | 慢 | 无独显，大内存 |
| Ollama | 12GB+ | 可选 | 中等 | 简单部署 |
| LM Studio | 16GB+ | 可选 | 中等 | 图形界面偏好 |

## 常见问题

### Q: 模型下载太慢/失败？

**A:** 设置 HuggingFace 镜像：

```bash
# Linux/Mac
export HF_ENDPOINT=https://hf-mirror.com

# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"

# 然后重新启动
docker compose down
docker compose up -d
```

### Q: Mac M1/M2/M3 能运行吗？

**A:** 可以，但性能受限：

```bash
# Mac 使用 CPU 模式（统一内存可用，但 vLLM 不支持 MPS）
docker compose up -d

# 或使用更小的模型
docker exec yinyi-vllm python -c "
# 修改模型为 2B 版本
"
```

### Q: 内存不足怎么办？

**A:** 使用量化版本或更小模型：

```yaml
# docker-compose.yml
command: >
  --model Qwen/Qwen3-VL-2B-Instruct  # 改为 2B 版本
  --dtype float16                     # 降低精度
  --gpu-memory-utilization 0.6       # 限制显存使用
```

### Q: 如何验证模型是否正常工作？

**A:** 

```bash
# 测试 API 是否响应
curl http://localhost:8000/v1/models

# 测试生成
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-VL-4B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 性能优化建议

1. **使用 SSD**: 模型文件较大，SSD 能显著提升加载速度
2. **预留内存**: 确保系统有 4GB+ 空闲内存
3. **首次预热**: 首次生成会比较慢，后续会快很多
4. **批量处理**: 一次分析多张照片比单张更高效

## 下一步

模型部署完成后：
1. 访问 http://localhost:8080 打开 Web 界面
2. 配置照片目录（如果不使用默认路径）
3. 点击"开始扫描"导入照片
4. 等待 AI 分析完成
5. 选择照片生成拍立得打印图
