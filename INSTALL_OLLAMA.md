# Ollama 安装指南（宿主机方案）

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
```

## 拉取模型

```bash
# 下载 Qwen2.5-VL 模型（约 4GB）
ollama pull qwen2.5-vl:7b

# 验证模型
ollama list
```

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
ollama run qwen2.5-vl:7b
>>> 描述这张照片：/path/to/photo.jpg
```

## 性能对比

| 方案 | M2 Mac 速度 | 加速方式 |
|------|------------|----------|
| Ollama 宿主机 | 1-2 秒/张 | Metal GPU |
| Ollama Docker | 3-5 秒/张 | CPU |
| vLLM Docker | 10-20 秒/张 | CPU |

## 下一步

安装完成后，运行：
```bash
./start-host.sh
```
