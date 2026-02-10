# Ollama 安装指南（宿主机方案 - Qwen3-VL-4B）

## macOS 安装

### 方法 1：命令行安装（推荐）
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 方法 2：下载安装包
1. 访问 https://ollama.com/download
2. 下载 macOS 版本
3. 双击安装包，按提示安装

### 验证安装
```bash
ollama --version
# 需要 0.12.7+ 版本才支持 Qwen3-VL
```

## 拉取 Qwen3-VL-4B 模型

```bash
# 下载 Qwen3-VL-4B 模型（约 3.3GB）
ollama pull qwen3-vl:4b

# 验证模型
ollama list
```

### 模型信息
- **名称**: qwen3-vl:4b
- **大小**: 3.3GB
- **参数量**: 4B
- **上下文**: 256K
- **支持**: 文本 + 图片理解

## 启动 Ollama 服务

```bash
# 前台运行（可以看到日志）
ollama serve

# 或后台运行
ollama serve &
```

服务默认在 http://localhost:11434 运行

## 测试模型

```bash
# 交互式测试
ollama run qwen3-vl:4b

# 分析照片
>>> 分析这张照片：/path/to/your/photo.jpg
>>> 写一句温暖的文案

# 退出
/bye
```

## 性能对比

| 方案 | M2 Mac 速度 | 加速方式 | 模型 |
|------|------------|----------|------|
| Ollama 宿主机 + Qwen3-VL | 1-3 秒/张 | Metal GPU | Qwen3-VL-4B ✅ |
| Ollama Docker | 3-5 秒/张 | CPU | Qwen2.5-VL |
| vLLM Docker | 10-20 秒/张 | CPU | Qwen3-VL-4B |

## 为什么选择 Qwen3-VL-4B？

1. **最新最强**: Qwen 系列最强视觉语言模型
2. **中文优化**: 对中文场景理解更好
3. **生成质量**: 文案更温馨、感性
4. **Metal 加速**: 在 Mac 上运行流畅

## 下一步

安装完成后，运行：
```bash
cd yinyi
./start-host.sh
```

服务启动后：
1. 打开 http://localhost:8080
2. 导入照片
3. 享受 AI 生成的温馨文案！
