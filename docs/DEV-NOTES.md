# 印忆 (YinYi) 开发文档

## 项目概述

**印忆**是一个AI照片记忆打印助手，受 [InkTime](https://github.com/dai-hongtao/InkTime) 项目启发，但改为输出打印文件（PNG/PDF）供米家照片打印机1S打印，而不是数码相框展示。

### 核心功能
- AI分析照片内容（Qwen3-VL多模态模型）
- 自动生成温馨感性的一句话文案
- 拍立得风格模板（100×148mm，适配米家6寸相纸）
- SHA-256照片去重
- NAS照片库集成（SMB挂载）

---

## 技术架构决策

### 1. AI模型选择

**主要方案 A：心流 API（推荐）**
- **模型**：qwen3-vl-plus
- **选择原因**：
  - 无需本地 GPU，8GB 内存即可运行
  - 部署简单，仅需 API Key
  - 速度和稳定性优于本地 CPU 运行
  - 适合大多数用户场景
- **配置**：`AI_BACKEND=iflow`
- **文档**：https://platform.iflow.cn

**备选方案 B：本地 Ollama**
- **模型**：Qwen3-VL:4b
- **选择原因**：
  - 完全本地运行，隐私保护好
  - 无需网络依赖
  - 无 API 调用费用
- **要求**：16GB+ 内存（推荐 32GB）
- **配置**：`AI_BACKEND=ollama`
- **安装**：`ollama pull qwen3-vl:4b`

**备选方案 C：vLLM**
- **适用场景**：高性能本地部署，有充足 GPU 资源
- **配置**：`AI_BACKEND=vllm`

**为什么不使用双模型架构？**
- 曾考虑过：VL模型提取信息 → 纯文本模型润色文案
- 最终决定：单模型更简单，Qwen3-VL的文案质量已足够温馨
- 如果后续文案质量不满意，可再考虑增加文本模型

### 2. 后端技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| 框架 | FastAPI | 现代、异步、自动生成API文档 |
| ORM | SQLAlchemy 2.0 | 成熟稳定，支持Async |
| 数据库 | SQLite | 零配置，单文件便于备份 |
| 图像处理 | Pillow | Python生态标准 |
| 迁移工具 | Alembic | 数据库版本管理 |

### 3. 前端技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| 框架 | Vue3 | 响应式，Composition API |
| 构建工具 | Vite | 快速开发体验 |
| 状态管理 | Pinia | Vue官方推荐 |
| HTTP客户端 | Axios | 成熟稳定 |

### 4. 部署方案对比

| 方案 | 适用场景 | 性能 | 复杂度 |
|------|----------|------|--------|
| **Windows原生** ⭐ | 主力开发机 | 最佳 | 低 |
| macOS原生 | Mac用户 | 良好 | 低 |
| Docker | 服务器/NAS | 一般 | 中 |
| Docker+WSL2 | Windows备选 | 一般 | 中 |

**当前采用：Windows 11 原生部署**
- Ollama直接运行在Windows宿主机（非Docker）
- 后端Python虚拟环境
- 前端Node.js
- NAS照片通过SMB映射为Z:盘

---

## 项目结构

```
yinyi/
├── backend/              # FastAPI后端
│   ├── main.py          # 应用入口
│   ├── config.py        # 通用配置
│   ├── config_windows.py # Windows专用配置
│   ├── database.py      # SQLAlchemy模型
│   ├── scanner.py       # 照片扫描+SHA256去重
│   ├── ai_analyzer.py   # AI分析（支持iflow/ollama/vllm）
│   ├── cache_manager.py # HEIC缓存管理
│   ├── renderer.py      # 拍立得模板渲染
│   ├── models.py        # Pydantic schemas
│   ├── generate_captions.py  # 批量生成文案脚本
│   ├── data/            # 数据目录
│   │   ├── yinyi.db     # SQLite数据库
│   │   └── cache/       # 缓存目录
│   │       └── heic/    # HEIC转码缓存
│   └── routers/         # API路由
│       ├── photos.py    # 照片管理（含HEIC转码）
│       ├── analyze.py   # AI分析
│       ├── export.py    # 导出打印
│       └── scanner.py   # 扫描任务
├── frontend/            # Vue3前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   │   ├── Gallery.vue    # 照片库（排序、筛选）
│   │   │   └── PhotoDetail.vue # 照片详情
│   │   ├── stores/      # Pinia状态
│   │   └── api/         # API封装
│   └── package.json
├── fonts/               # 中文字体
│   └── LXGWWenKai-Regular.ttf
├── docs/                # 文档
│   ├── WINDOWS-DEPLOY.md
│   ├── MIGRATION-CHECKLIST.md
│   └── DEV-NOTES.md     # 本文件
├── scripts/             # 工具脚本
│   └── install-deps-winget.ps1
├── start-windows.bat   # Windows启动脚本
├── install.bat         # 依赖安装脚本
├── docker-compose.yml  # Docker配置（备用）
├── .env                # 环境变量配置
└── README.md
```

---

## 关键配置

### 环境变量 (.env)

```env
# 照片目录（Windows示例）
PHOTOS_DIR=Z:\Photos
EXPORTS_DIR=.\exports
FONTS_DIR=.\fonts

# AI 后端选择：ollama / iflow / vllm
AI_BACKEND=iflow

# 心流 API 配置（推荐）
IFLOW_API_KEY=your-api-key-here
IFLOW_MODEL=qwen3-vl-plus
IFLOW_API_URL=https://api.iflow.cn/v1/chat/completions

# Ollama 配置（本地运行）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:4b

# HEIC 缓存配置
HEIC_CACHE_MAX_GB=5.0
HEIC_CACHE_MAX_AGE_DAYS=30
HEIC_CACHE_CLEANUP_INTERVAL_HOURS=24
```

### 拍立得模板规格

**米家照片打印机1S 6寸相纸**
- 物理尺寸：100mm × 148mm
- 分辨率：300 DPI
- 像素尺寸：1181 × 1748 px
- 长宽比：2:3

**模板布局**
```
+----------------------------+
|      上白边 40px           |
|  +----------------------+  |
|  |                      |  |
|  |    照片区域          |  |
|  |    1000×1333px       |  |
|  |    (3:4比例)         |  |
|  |                      |  |
|  +----------------------+  |
|      下白边 375px          |
|  [感性文案]                |
|  [日期 · 地点]             |
+----------------------------+
```

---

## HEIC 缓存管理

### 背景
iPhone 拍摄的照片使用 HEIC 格式，浏览器无法直接显示。需要后端自动转码为 JPEG。

### 实现方案
**文件**: `backend/cache_manager.py`

**核心功能**:
1. **自动转码**: 首次访问 HEIC 照片时转码为 JPEG
2. **缓存管理**: 转码后的 JPEG 缓存到 `backend/data/cache/heic/`
3. **自动清理**: 
   - 按空间：超过 5GB 时删除最旧文件（LRU 策略）
   - 按时间：删除 30 天未访问的缓存
4. **异步触发**: 每次访问 HEIC 时异步检查，不阻塞响应

**配置参数**:
```python
max_size_gb = 5.0              # 缓存上限
target_size_gb = 4.0           # 清理后目标大小
max_age_days = 30              # 文件最大保留天数
cleanup_interval_hours = 24    # 清理检查间隔
```

**API 端点**:
```bash
# 查看缓存统计
GET /admin/cache/stats

# 手动触发清理
POST /admin/cache/cleanup?force=true
```

### 技术细节
- 使用 `Pillow + pillow-heif` 进行转码
- 转码质量：90% JPEG
- 缓存文件名：`{photo_id}.jpg`
- 线程安全：使用 `threading.Lock` 避免并发清理冲突

---

## 重启保护机制

### 问题背景
分析照片时，如果后端意外重启：
- 状态为 `analyzing` 的照片会卡住
- 再次点击分析会跳过这些照片

### 解决方案
**文件**: `backend/main.py`

启动时自动重置卡住的照片：
```python
# 启动时检查 analyzing 状态的照片
stuck_photos = db.query(Photo).filter(Photo.status == "analyzing").all()
for photo in stuck_photos:
    photo.status = "pending"
db.commit()
```

### 效果
- 重启后自动恢复中断的分析任务
- 用户无需手动干预
- 不会浪费已完成的进度

---

## 开发工作流程

### 1. 环境搭建（新机器）

**Windows 11 步骤：**

```powershell
# 1. 安装基础软件（用winget）
winget install Git.Git
winget install Python.Python.3.11
winget install OpenJS.NodeJS

# 2. 克隆项目
git clone https://github.com/naokij/yinyi.git
cd yinyi

# 3. 配置环境变量
# 复制 .env.example 为 .env，填入心流 API Key
notepad .env

# 4. 映射NAS照片
net use Z: \\<NAS_IP>\homes\jiangle\Photos /persistent:yes

# 5. 启动服务（自动安装依赖）
.\start-windows.bat
```

**可选：本地 Ollama（需要 16GB+ 内存）**
```powershell
# 安装 Ollama: https://ollama.com/download/windows
ollama serve
ollama pull qwen3-vl:4b
# 修改 .env: AI_BACKEND=ollama
```

### 2. 日常开发

**启动服务（使用启动脚本）：**
```powershell
cd yinyi
.\start-windows.bat    # 启动后端和前端
.\stop-windows.bat     # 停止所有服务
```

**或手动启动（2个终端）：**

终端1 - 后端:
```powershell
cd yinyi\backend
venv\Scripts\activate
python main.py
```

终端2 - 前端:
```powershell
cd yinyi\frontend
npm run dev -- --host 0.0.0.0  # 支持局域网访问
```

**访问：**
- 本地访问：http://localhost:3000
- 局域网访问：http://[你的IP]:3000
- API文档：http://localhost:8765/docs

**防火墙设置（局域网访问）：**
详见 [docs/FIREWALL-SETUP.md](FIREWALL-SETUP.md)

### 3. 代码提交

```bash
cd yinyi

# 检查状态
git status

# 添加修改
git add .

# 提交
git commit -m "描述修改内容"

# 推送
git push origin main
```

---

## 重要决策记录

### 决策1：使用单模型而非双模型
**时间：** 2025-02-10
**决策：** 仅使用Qwen3-VL:4b一个模型，同时处理视觉理解和文案生成
**理由：**
- 简化架构，减少维护复杂度
- Qwen3-VL的中文文案质量已足够温馨
- 如果需要更高质量，后续可再增加文本模型
**替代方案：** VL提取信息 → Qwen2.5:7b润色文案（保留作为未来选项）

### 决策2：Windows原生部署优先
**时间：** 2025-02-10
**决策：** 主力开发机使用Windows 11原生部署，而非Docker
**理由：**
- Ryzen 5800H + 32GB内存性能充足
- 避免Docker虚拟化开销
- SMB网络驱动器挂载更方便
- 开发调试更直接

### 决策3：SQLite而非PostgreSQL
**时间：** 2025-02-10
**决策：** 使用SQLite作为数据库
**理由：**
- 零配置，单文件便于备份和迁移
- 个人使用场景数据量不大
- 无需额外安装数据库服务

### 决策4：照片指纹去重策略
**时间：** 2025-02-09
**决策：** MVP阶段使用SHA-256文件哈希去重
**理由：**
- 实现简单，100%准确检测相同文件
- 速度快，秒级完成
**后续优化：** Phase 2增加感知哈希（pHash）检测相似图片

### 决策5：添加心流 API 作为默认 AI 后端
**时间：** 2026-02-13
**决策：** 将 心流 API 设为推荐方案，Ollama 作为备选
**理由：**
- 心流 API 无需本地 GPU，8GB 内存即可流畅运行
- 部署简单，仅需 API Key，降低用户使用门槛
- 本地 Ollama 在 CPU 上运行较慢（30秒-2分钟/张），不适合大量照片处理
- 支持多后端架构（iflow/ollama/vllm），用户可按需选择
**实现：**
- 新增 `backend/ai_analyzer.py` 支持多种后端
- 新增 `backend/cache_manager.py` 管理 HEIC 缓存
- 更新所有文档说明两种方案的差异

---

## 遇到的问题与解决方案

### 问题1：环境变量加载被系统变量覆盖
**现象：** 设置了 `.env` 文件中的 `OLLAMA_HOST`，但实际使用的是系统环境变量值
**原因：** `load_dotenv()` 默认不会覆盖已存在的环境变量
**解决：**
```python
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=True)  # 添加 override=True
```

### 问题2：HEIC 转码后浏览器下载而非显示
**现象：** FileResponse 默认添加 `content-disposition: attachment` 头
**解决：**
```python
from starlette.responses import FileResponse

response = FileResponse(path=file_path, media_type="image/jpeg")
if "content-disposition" in response.headers:
    del response.headers["content-disposition"]  # 移除该头
```

### 问题3：前端图片加载失败永久隐藏
**现象：** 图片加载失败后触发 error 事件，直接隐藏图片元素
**解决：** 添加重试机制，最多重试 2 次
```javascript
const retryCount = ref(0);
const maxRetries = 2;

const onImageError = () => {
  if (retryCount.value < maxRetries) {
    retryCount.value++;
    setTimeout(() => {
      imageSrc.value = `${originalSrc}?retry=${retryCount.value}`;
    }, 1000);
  } else {
    showImage.value = false;
  }
};
```

### 问题4：GitHub推送失败（公司账号混淆）
**现象：** 不小心推送到公司账号nimbuscom而非个人账号naokij
**解决：**
```bash
# 1. 删除错误的remote
git remote remove origin

# 2. 添加正确的remote
git remote add origin https://github.com/naokij/yinyi.git

# 3. 重新推送
git push -u origin main
```

### 问题5：Ollama模型命名
**现象：** 文档中模型名不一致（qwen3-vl:4b vs qwen3-vl-latest）
**确认：** Ollama官方确实支持`qwen3-vl:4b`（3.3GB，4.44B参数）
**修正：** 统一使用`qwen3-vl:4b`

### 问题6：前端构建后字体路径错误
**解决：** 在renderer.py中动态检测字体路径，优先使用项目fonts目录，回退到系统字体

### 问题7：Windows路径分隔符
**解决：** 使用pathlib.Path处理路径，自动适配Windows和Unix

---

## 性能基准

### Ryzen 5800H (32GB RAM) + Windows 11

| 操作 | 心流 API | Ollama (本地) | 备注 |
|------|----------|---------------|------|
| 扫描1000张照片 | ~1分钟 | ~1分钟 | SHA-256去重 |
| AI分析单张照片 | 3-5秒 | 2-4秒 | 心流 API 需要网络 |
| HEIC 转码 | 1-3秒 | 1-3秒 | 首次访问时转码 |
| 生成拍立得图片 | <1秒 | <1秒 | 100×148mm@300DPI |
| 批量导出10张 | ~30秒 | ~25秒 | 含 AI 分析时间 |

### 内存使用对比

| AI 后端 | 系统内存 | 显存 | 适用场景 |
|---------|----------|------|----------|
| 心流 API | 8GB+ | 无 | 推荐，低配置电脑 |
| Ollama (CPU) | 16GB+ | 无 | 注重隐私，离线使用 |
| Ollama (GPU) | 16GB+ | 8GB+ | 高性能本地部署 |

### 优化建议
- 心流 API 模式下无需保持 Ollama 运行，节省内存
- HEIC 转码使用缓存，第二次访问即时响应
- 大量照片分析建议分批处理（每批50-100张）
- 导出目录定期清理，防止占用过多磁盘空间
- 首次模型加载较慢（Ollama 约10-20秒），之后保持热启动

---

## 后续开发计划

### Phase 1: 核心功能 ✅ 已完成
- [x] 照片扫描与SHA-256去重
- [x] EXIF信息提取
- [x] AI分析与文案生成（Ollama + 心流 API）
- [x] 拍立得模板渲染
- [x] Web管理界面
- [x] Windows原生部署
- [x] 照片评分筛选（回忆度/美观度）
- [x] 照片排序功能（时间/回忆分/美观分）

### Phase 2: 增强功能 🚧 进行中
- [x] HEIC 格式支持 + 缓存自动清理
- [ ] 感知哈希去重（检测相似图片）
- [ ] 截图过滤优化（排除文件名含 screenshot）
- [ ] PDF批量导出
- [ ] 多种打印模板（故事卡、多图拼贴）
- [ ] 导出历史管理
- [ ] 相册智能推荐

### Phase 3: 高级功能 📋 规划中
- [ ] WebDAV支持（兼容更多NAS）
- [ ] 手机App（PWA）
- [ ] 多用户支持
- [ ] 云端备份（可选）

### 技术债务
- [ ] 添加单元测试
- [ ] 添加API集成测试
- [ ] 完善错误处理和日志
- [ ] 优化前端移动端体验
- [ ] 后端进程管理（自动重启）

---

## 参考资料

### 灵感来源
- [InkTime](https://github.com/dai-hongtao/InkTime) - 墨水屏数码相框项目

### 技术文档
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Vue3文档](https://vuejs.org/)
- [Ollama文档](https://github.com/ollama/ollama)
- [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL)

### 字体
- [霞鹜文楷](https://github.com/lxgw/LxgwWenKai) - 开源中文字体

---

## 联系信息

- **GitHub**: https://github.com/naokij/yinyi
- **问题反馈**: GitHub Issues
- **开发记录**: 本文档

---

*最后更新：2026-02-13*
*版本：v0.2.0*
