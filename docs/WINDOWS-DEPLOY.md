# 印忆 (YinYi) Windows 原生部署指南

## 🎯 适用场景

- Windows 10/11 系统
- 不需要 Docker
- 照片通过 SMB/NFS 访问 NAS
- 追求最简部署和最佳性能

## 📋 系统要求

- **操作系统**: Windows 10 (64-bit) 或 Windows 11
- **处理器**: AMD Ryzen 5800H 或同等级别
- **内存**: 16GB 以上（推荐 32GB）
- **硬盘**: SSD，剩余空间 20GB+
- **网络**: 能访问 NAS 的局域网

## 🛠️ 安装步骤

### 1. 安装基础软件

#### 1.1 Python 3.11+
1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.11.x Windows installer (64-bit)
3. **安装时务必勾选**: "Add Python to PATH"
4. 点击 "Install Now"

验证安装：
```powershell
python --version
# 应显示 Python 3.11.x
```

#### 1.2 Node.js 18+
1. 访问 https://nodejs.org/
2. 下载 LTS 版本（左侧绿色按钮）
3. 双击安装，全部默认选项

验证安装：
```powershell
node --version
# 应显示 v18.x.x 或 v20.x.x
npm --version
```

#### 1.3 Git for Windows
1. 访问 https://git-scm.com/download/win
2. 下载并安装
3. 安装时选择："Use Git from the Windows Command Prompt"

验证安装：
```powershell
git --version
```

#### 1.4 Ollama for Windows
1. 访问 https://ollama.com/download/windows
2. 下载安装包
3. 双击安装

**重要：下载模型**

打开 PowerShell 或 CMD：
```powershell
# 启动 Ollama 服务（保持此窗口运行）
ollama serve

# 在另一个窗口中下载模型
ollama pull qwen3-vl:4b

# 验证
ollama list
# 应显示 qwen3-vl:4b
```

### 2. 克隆项目

```powershell
# 进入你想存放项目的目录，例如
cd C:\Projects

# 克隆仓库
git clone https://github.com/your-username/yinyi.git
cd yinyi
```

### 3. 映射 NAS 照片目录

**方法 1：使用文件资源管理器**
1. 打开文件资源管理器
2. 在地址栏输入：`\\<NAS_IP>\homes\jiangle\Photos`
3. 右键点击 "Photos" 文件夹 → "映射网络驱动器"
4. 选择盘符（例如 Z:），勾选 "登录时重新连接"
5. 点击 "完成"

**方法 2：使用命令行**
```powershell
net use Z: \\\<NAS_IP>\homes\jiangle\Photos /persistent:yes
```

验证映射：
```powershell
Z:
dir
# 应该能看到你的照片文件
```

### 4. 配置环境变量

创建 `.env` 文件在项目根目录：

```env
# Windows 路径使用双反斜杠或原始字符串
PHOTOS_DIR=Z:\Photos
EXPORTS_DIR=.\exports
FONTS_DIR=.\fonts
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3-vl:4b
```

### 5. 安装中文字体（推荐）

下载霞鹜文楷字体：
```powershell
# 在 fonts 目录中打开 PowerShell
cd fonts

# 下载字体
Invoke-WebRequest -Uri "https://github.com/lxgw/LxgwWenKai/releases/download/v1.510/LXGWWenKai-Regular.ttf" -OutFile "LXGWWenKai-Regular.ttf"
```

或者手动下载后放入 `fonts` 文件夹。

如果没有安装，系统会使用默认字体（微软雅黑）。

### 6. 首次启动

**方法 1：使用启动脚本（推荐）**
```powershell
# 在项目根目录
cd C:\Projects\yinyi

# 运行启动脚本
.\start-windows.bat
```

**方法 2：手动启动**

打开 **3 个** PowerShell 窗口：

**窗口 1：Ollama 服务**
```powershell
ollama serve
```

**窗口 2：后端服务**
```powershell
cd C:\Projects\yinyi\backend

# 创建虚拟环境（首次）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖（首次）
pip install -r requirements.txt

# 启动后端
python main.py
```

**窗口 3：前端服务**
```powershell
cd C:\Projects\yinyi\frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

### 7. 访问应用

打开浏览器访问：
- **Web 界面**: http://localhost:8080
- **API 文档**: http://localhost:8765/docs

## 🔧 故障排除

### 问题 1：后端启动失败，提示模块未找到

**解决**：
```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### 问题 2：无法访问 NAS 照片

**检查步骤**：
1. 确认网络驱动器已映射：
   ```powershell
   net use
   # 应显示 Z: 驱动器
   ```

2. 测试访问：
   ```powershell
   Z:
   dir
   ```

3. 如果失败，检查 NAS SMB 服务是否开启

### 问题 3：Ollama 连接失败

**检查**：
```powershell
# 测试 Ollama 服务
curl http://localhost:11434/api/tags

# 如果没响应，手动启动
ollama serve
```

### 问题 4：字体显示为方块

**解决**：
- 确保 `fonts` 目录有字体文件
- 或使用 Windows 系统字体：修改 `backend/renderer.py` 中的字体路径为 `C:\Windows\Fonts\msyh.ttc`（微软雅黑）

### 问题 5：端口被占用

**检查占用**：
```powershell
# 查看 8765 端口
netstat -ano | findstr 8765

# 查看 8080 端口
netstat -ano | findstr 8080

# 结束进程（将 <PID> 替换为实际进程 ID）
taskkill /PID <PID> /F
```

## 🚀 性能优化

### 1. Ollama 使用更多 CPU 线程

在启动 Ollama 前设置环境变量：
```powershell
$env:OLLAMA_NUM_THREADS=12
ollama serve
```

### 2. 后端性能优化

修改 `backend/main.py`，增加工作进程：
```python
# 在文件末尾
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765, workers=2)
```

### 3. 使用生产模式运行前端

```powershell
cd frontend
npm run build
# 然后使用 serve 或其他静态服务器
npx serve -s dist -l 8080
```

## 📂 项目结构

```
yinyi/
├── backend/              # 后端代码
│   ├── venv/            # Python 虚拟环境
│   ├── main.py
│   ├── config_windows.py # Windows 配置
│   └── ...
├── frontend/            # 前端代码
│   ├── node_modules/    # npm 依赖
│   └── ...
├── fonts/               # 字体文件
├── data/                # 数据库
├── exports/             # 导出文件
├── photos/              # 照片目录（或映射到 Z:）
├── start-windows.bat   # Windows 启动脚本
├── .env                # 环境变量配置
└── README.md
```

## 📝 常用命令

```powershell
# 启动 Ollama
ollama serve

# 查看已安装模型
ollama list

# 删除模型
ollama rm qwen3-vl:4b

# 重新下载模型
ollama pull qwen3-vl:4b

# 测试模型
ollama run qwen3-vl:4b
>>> 描述这张图片：C:\Users\Pictures\test.jpg
```

## 🔄 更新项目

```powershell
cd C:\Projects\yinyi

# 拉取最新代码
git pull

# 更新后端依赖
cd backend
venv\Scripts\activate
pip install -r requirements.txt --upgrade
cd ..

# 更新前端依赖
cd frontend
npm install
cd ..

# 重新启动
.\start-windows.bat
```

## ❓ 需要帮助？

遇到问题可以：
1. 查看后端日志（启动窗口中的输出）
2. 查看前端日志（浏览器开发者工具 F12）
3. 检查 Ollama 日志（启动窗口）
4. 提交 Issue 到 GitHub

---

**祝你使用愉快！** 🎉
