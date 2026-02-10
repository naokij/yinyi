# Windows 迁移检查清单

## ✅ 当前电脑（Mac）完成项

- [x] 代码开发完成
- [x] Windows 配置文件创建
- [x] Windows 启动脚本创建
- [x] Windows 部署文档编写
- [x] Git 初始化脚本准备
- [x] .gitignore 配置

## 📦 需要在新电脑（Windows）上执行的步骤

### 1. 基础软件安装
- [ ] 安装 Python 3.11+ (勾选 "Add to PATH")
- [ ] 安装 Node.js 18+
- [ ] 安装 Git for Windows
- [ ] 安装 Ollama for Windows
- [ ] 验证所有软件安装成功

### 2. Git 仓库设置
- [ ] 运行 `scripts/init-git.sh` 或手动初始化
- [ ] 关联 GitHub/GitLab 远程仓库
- [ ] 推送代码

### 3. 项目配置
- [ ] 克隆/复制项目到 `C:\Projects\yinyi`
- [ ] 创建 `.env` 文件
- [ ] 下载字体文件到 `fonts/` 目录

### 4. NAS 连接
- [ ] 映射网络驱动器 `Z:` 到 `\\<NAS_IP>\homes\jiangle\Photos`
- [ ] 测试照片目录可访问
- [ ] 确认 SMB 权限正确

### 5. Ollama 模型
- [ ] 启动 Ollama: `ollama serve`
- [ ] 下载模型: `ollama pull qwen3-vl:4b`
- [ ] 验证模型: `ollama list`

### 6. 后端启动
- [ ] 创建 Python 虚拟环境: `python -m venv venv`
- [ ] 激活虚拟环境: `venv\Scripts\activate`
- [ ] 安装依赖: `pip install -r requirements.txt`
- [ ] 启动后端: `python main.py`
- [ ] 验证: 访问 http://localhost:8765/health

### 7. 前端启动
- [ ] 安装依赖: `npm install`
- [ ] 启动开发服务器: `npm run dev`
- [ ] 验证: 访问 http://localhost:8080

### 8. 功能测试
- [ ] 扫描照片
- [ ] AI 分析一张照片
- [ ] 生成拍立得预览
- [ ] 导出 PNG 文件
- [ ] 使用米家打印机打印

## 🔧 可选优化

- [ ] 设置 Ollama CPU 线程数
- [ ] 配置 Windows 防火墙规则
- [ ] 创建桌面快捷方式
- [ ] 设置开机自动启动

## 📝 新文件清单

Windows 环境新增文件：
```
yinyi/
├── .gitignore              # Git 忽略配置 ✓
├── start-windows.bat       # Windows 启动脚本 ✓
├── backend/
│   └── config_windows.py   # Windows 配置 ✓
├── docs/
│   ├── WINDOWS-DEPLOY.md   # Windows 部署指南 ✓
│   └── MIGRATION-CHECKLIST.md  # 本文件 ✓
└── scripts/
    └── init-git.sh         # Git 初始化脚本 ✓
```

## 🚀 启动命令汇总

**一键启动（推荐）：**
```powershell
cd C:\Projects\yinyi
.\start-windows.bat
```

**手动启动：**
```powershell
# 终端 1: Ollama
ollama serve

# 终端 2: 后端
cd C:\Projects\yinyi\backend
venv\Scripts\activate
python main.py

# 终端 3: 前端
cd C:\Projects\yinyi\frontend
npm run dev
```

## 📞 问题排查

如果遇到问题，检查：
1. 所有软件版本是否正确
2. 端口是否被占用 (8765, 8080, 11434)
3. NAS 网络驱动器是否正确映射
4. Ollama 服务是否正常运行
5. 后端依赖是否完整安装

详细排查步骤见：`docs/WINDOWS-DEPLOY.md`
