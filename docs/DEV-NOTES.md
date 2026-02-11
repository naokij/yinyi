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

**视觉-语言模型：Qwen3-VL:4b**
- 选择原因：
  - 中文场景理解优秀
  - 4B参数量适中，本地可运行
  - 同时支持"看懂照片"和"生成文案"
  - Ollama原生支持
- 安装：`ollama pull qwen3-vl:4b`
- 大小：约3.3GB

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
│   ├── ai_analyzer.py   # AI分析（调用Ollama）
│   ├── renderer.py      # 拍立得模板渲染
│   ├── models.py        # Pydantic schemas
│   └── routers/         # API路由
│       ├── photos.py
│       ├── analyze.py
│       ├── export.py
│       └── scanner.py
├── frontend/            # Vue3前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── stores/      # Pinia状态
│   │   └── api/         # API封装
│   └── package.json
├── fonts/               # 中文字体
│   └── LXGWWenKai-Regular.ttf  # 霞鹜文楷
├── docs/                # 文档
│   ├── WINDOWS-DEPLOY.md
│   ├── MIGRATION-CHECKLIST.md
│   └── DEV-NOTES.md     # 本文件
├── scripts/             # 工具脚本
│   └── install-deps-winget.ps1
├── start-windows.bat   # Windows启动脚本
├── install.bat         # 依赖安装脚本
├── docker-compose.yml  # Docker配置（备用）
└── README.md
```

---

## 关键配置

### 环境变量 (.env)

```env
# 照片目录（Windows示例）
PHOTOS_DIR=Z:\Photos

# 导出目录
EXPORTS_DIR=.\exports

# AI服务配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:4b

# 可选：后端配置
AI_BACKEND=ollama
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

## 开发工作流程

### 1. 环境搭建（新机器）

**Windows 11 步骤：**

```powershell
# 1. 安装基础软件（用winget）
winget install Git.Git
winget install Python.Python.3.11
winget install OpenJS.NodeJS
# Ollama需手动下载：https://ollama.com/download/windows

# 2. 下载AI模型
ollama serve          # 保持运行
ollama pull qwen3-vl:4b

# 3. 克隆项目
git clone https://github.com/naokij/yinyi.git
cd yinyi

# 4. 映射NAS照片
net use Z: \\<NAS_IP>\homes\jiangle\Photos /persistent:yes

# 5. 安装后端依赖
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 6. 安装前端依赖
cd frontend
npm install
cd ..

# 7. 启动
.\start-windows.bat
```

### 2. 日常开发

**启动服务（3个终端）：**

终端1 - Ollama:
```powershell
ollama serve
```

终端2 - 后端:
```powershell
cd yinyi\backend
venv\Scripts\activate
python main.py
```

终端3 - 前端:
```powershell
cd yinyi\frontend
npm run dev
```

**访问：**
- Web界面：http://localhost:8080
- API文档：http://localhost:8765/docs

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

---

## 遇到的问题与解决方案

### 问题1：GitHub推送失败（公司账号混淆）
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

### 问题2：Ollama模型命名
**现象：** 文档中模型名不一致（qwen3-vl:4b vs qwen3-vl-latest）
**确认：** Ollama官方确实支持`qwen3-vl:4b`（3.3GB，4.44B参数）
**修正：** 统一使用`qwen3-vl:4b`

### 问题3：前端构建后字体路径错误
**解决：** 在renderer.py中动态检测字体路径，优先使用项目fonts目录，回退到系统字体

### 问题4：Windows路径分隔符
**解决：** 使用pathlib.Path处理路径，自动适配Windows和Unix

---

## 性能基准

### Ryzen 5800H (32GB RAM) + Windows 11

| 操作 | 耗时 | 备注 |
|------|------|------|
| 扫描1000张照片 | ~1分钟 | SHA-256去重 |
| AI分析单张照片 | 2-4秒 | Qwen3-VL:4b |
| 生成拍立得图片 | <1秒 | 100×148mm@300DPI |
| 批量导出10张 | ~5秒 | 含预览生成 |

### 优化建议
- 首次模型加载较慢（约10-20秒），之后保持热启动
- 大量照片建议分批处理，避免内存峰值
- 导出目录定期清理，防止占用过多磁盘空间

---

## 后续开发计划

### Phase 1: 核心功能 ✅ 已完成
- [x] 照片扫描与SHA-256去重
- [x] EXIF信息提取
- [x] AI分析与文案生成
- [x] 拍立得模板渲染
- [x] Web管理界面
- [x] Windows原生部署

### Phase 2: 增强功能 🚧 待开发
- [ ] 感知哈希去重（检测相似图片）
- [ ] PDF批量导出
- [ ] 多种打印模板（故事卡、多图拼贴）
- [ ] 照片评分筛选（回忆度/美观度）
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

*最后更新：2025-02-10*
*版本：v0.1.0*
