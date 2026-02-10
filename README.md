# 印忆 (YinYi) - 照片记忆打印助手

一个自托管的 AI 照片精选工具，智能分析照片库，生成温馨感性的回忆卡片，专为米家照片打印机 1S 优化。

![版本](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## ✨ 特性

- 🤖 **AI 智能分析**：使用本地 Qwen3-VL-4B 视觉大模型分析照片内容
- 💭 **温馨文案**：自动生成感性、温暖的一句话描述
- 📸 **拍立得风格**：针对米家 6 寸相纸（100×148mm, 2:3）优化的经典留白设计
- 🔍 **智能去重**：基于 SHA-256 文件哈希自动检测重复照片
- 🏠 **NAS 集成**：支持 SMB/NFS 挂载，照片存 NAS，运行在本机
- 💻 **跨平台**：支持 Windows、macOS、Linux
- 🚀 **原生部署**：无需 Docker，Windows 原生运行性能最佳

## 🖨️ 支持的打印机

- **米家照片打印机 1S**
  - 6 寸相纸：100 × 148 mm
  - 长宽比：2:3
  - 打印质量：300 DPI

## 🚀 快速开始

### 支持的平台

| 平台 | 部署方式 | 推荐度 | 性能 |
|------|----------|--------|------|
| **Windows 11** | 原生 | ⭐⭐⭐⭐⭐ | 最佳 |
| Windows 10 | 原生 | ⭐⭐⭐⭐ | 优秀 |
| macOS (M1/M2/M3) | Docker / 原生 | ⭐⭐⭐⭐ | 良好 |
| Linux | Docker / 原生 | ⭐⭐⭐⭐⭐ | 最佳 |

### Windows 11 原生部署（推荐）

**系统要求：**
- Windows 10/11 64-bit
- 16GB+ 内存（推荐 32GB）
- AMD Ryzen 5800H 或同级别 CPU
- NAS 照片通过 SMB 访问

**安装步骤：**

1. **安装依赖**
   - Python 3.11+ (勾选 "Add to PATH")
   - Node.js 18+
   - Git for Windows
   - Ollama for Windows

2. **下载模型**
   ```powershell
   ollama serve        # 保持运行
   ollama pull qwen3-vl:4b  # 另一个窗口
   ```

3. **映射 NAS 照片**
   ```powershell
   net use Z: \\<NAS_IP>\homes\jiangle\Photos /persistent:yes
   ```

4. **启动服务**
   ```powershell
   git clone https://github.com/your-username/yinyi.git
   cd yinyi
   .\start-windows.bat
   ```

5. **访问应用**
   - Web 界面：http://localhost:8080
   - API 文档：http://localhost:8765/docs

**详细文档**：见 [docs/WINDOWS-DEPLOY.md](docs/WINDOWS-DEPLOY.md)

### macOS 部署

见 [docs/macOS-DEPLOY.md](docs/macOS-DEPLOY.md)

### Docker 部署

```bash
# 通用方案（支持 Linux/macOS/Windows with WSL2）
docker-compose up -d
```

## 📁 项目结构

```
yinyi/
├── backend/              # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── config.py        # 配置（通用）
│   ├── config_windows.py # Windows 配置
│   ├── database.py      # SQLite 模型
│   ├── scanner.py       # 照片扫描 + SHA-256 去重
│   ├── ai_analyzer.py   # AI 分析（支持 Ollama/vLLM）
│   ├── renderer.py      # 拍立得模板渲染
│   └── routers/         # API 路由
├── frontend/            # Vue3 前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── stores/      # Pinia 状态管理
│   │   └── api/         # API 封装
│   └── package.json
├── docs/                # 文档
│   ├── WINDOWS-DEPLOY.md
│   ├── macOS-DEPLOY.md
│   └── MIGRATION-CHECKLIST.md
├── fonts/               # 字体文件
├── photos/              # 照片目录（或映射到 NAS）
├── exports/             # 导出文件
├── data/                # 数据库
├── start-windows.bat   # Windows 启动脚本
├── start-mac.sh        # macOS 启动脚本
└── docker-compose.yml  # Docker 配置
```

## 🎨 打印模板

### 拍立得经典（默认）

- **尺寸**: 100 × 148 mm（米家 6 寸）
- **分辨率**: 300 DPI（1181 × 1748 像素）
- **布局**:
  - 上白边：40px
  - 照片区域：1000 × 1333 px（居中，3:4 比例）
  - 下白边：375px（文案 + 日期）
  - 左右白边：90px
- **字体**: 霞鹜文楷 / 微软雅黑
- **样式**: 纯白色背景，温馨感性文案

## 🔧 配置说明

### 环境变量 (.env)

```env
# 照片目录（Windows 示例）
PHOTOS_DIR=Z:\Photos

# 导出目录
EXPORTS_DIR=.\exports

# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:4b

# AI 后端选择（ollama/vllm）
AI_BACKEND=ollama
```

### NAS 照片访问

**Windows (SMB):**
```powershell
net use Z: \\192.168.1.100\homes\jiangle\Photos /persistent:yes
```

**Linux/macOS (SMB):**
```bash
sudo mount -t cifs //192.168.1.100/homes/jiangle/Photos /mnt/nas/photos -o username=jiangle
```

**Docker:**
```yaml
volumes:
  - /mnt/nas/photos:/app/photos:ro
```

## 📊 性能对比

### Ryzen 5800H (32GB) 实测

| 部署方式 | 模型 | 分析速度 | 备注 |
|----------|------|----------|------|
| **Windows 原生** ⭐ | Qwen3-VL-4B | 2-4 秒/张 | 推荐，无 Docker 开销 |
| WSL2 + Docker | Qwen3-VL-4B | 3-6 秒/张 | 有虚拟化开销 |
| Docker (纯 CPU) | Qwen3-VL-4B | 5-10 秒/张 | 适合无 GPU 环境 |

### M2 Mac (16GB) 实测

| 部署方式 | 分析速度 | 备注 |
|----------|----------|------|
| **Ollama 原生** ⭐ | 1-3 秒/张 | Metal 加速 |
| Docker | 3-5 秒/张 | 无 GPU 加速 |

## 🛠️ 开发计划

### Phase 1: 核心功能 ✅
- [x] 照片扫描（SHA-256 去重）
- [x] EXIF 信息提取
- [x] AI 分析（Qwen3-VL-4B）
- [x] 拍立得模板渲染
- [x] Web 管理界面
- [x] Windows 原生支持

### Phase 2: 增强功能 🚧
- [ ] 感知哈希去重（检测相似图片）
- [ ] PDF 批量导出
- [ ] 多种打印模板
- [ ] 照片评分筛选
- [ ] 导出历史管理

### Phase 3: 高级功能 📋
- [ ] WebDAV 支持
- [ ] 云端同步（可选）
- [ ] 智能相册推荐
- [ ] 手机 App（PWA）

## 🐛 常见问题

### Q: 模型下载太慢/失败？

**A:** 设置镜像源：
```powershell
# Windows
$env:OLLAMA_MODELS = "https://ollama.com/library"

# 或使用代理
$env:HTTP_PROXY = "http://proxy:port"
```

### Q: Windows 上字体显示不正确？

**A:** 下载霞鹜文楷字体到 `fonts/` 目录，或修改 `renderer.py` 使用系统字体：
```python
font_path = "C:\\Windows\\Fonts\\msyh.ttc"  # 微软雅黑
```

### Q: 如何更新项目？

```bash
git pull
# 重新安装依赖（如果有更新）
pip install -r requirements.txt --upgrade
npm install
```

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) - 阿里通义千问视觉语言模型
- [Ollama](https://ollama.com) - 本地大模型运行框架
- [FastAPI](https://fastapi.tiangolo.com) - 现代 Web 框架
- [Vue3](https://vuejs.org) - 前端框架
- [霞鹜文楷](https://github.com/lxgw/LxgwWenKai) - 开源中文字体

---

**印忆** - 让每一张照片都有温度 ❤️

**适用于**：家庭照片管理、旅行回忆整理、年度照片精选、礼物制作
