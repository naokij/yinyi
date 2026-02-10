# 安全注意事项

## 开源使用提醒

本项目开源，但使用时请注意以下安全事项：

### 1. 配置文件

- 使用 `.env` 文件存储敏感配置（已在 .gitignore 中排除）
- 不要提交包含以下内容的文件到 Git：
  - 数据库文件 (`.db`, `.db-journal`)
  - 导出的照片 (`exports/`)
  - 本地照片缓存
  - 环境变量文件 (`.env`)

### 2. 网络安全

- 默认仅在 `localhost` 运行，不对外暴露
- 如需远程访问，请配置：
  - HTTPS（使用 Nginx 反向代理）
  - 身份验证（Basic Auth 或 OAuth）
  - 防火墙规则

### 3. AI 服务

- Ollama 默认监听 `localhost:11434`
- 不要直接暴露 Ollama 到公网
- 如需远程使用 Ollama，配置反向代理 + 认证

### 4. 照片隐私

- 项目仅在本地处理照片，不上传到云端
- AI 分析通过本地 Ollama 完成
- 导出的打印文件保存在本地 `exports/` 目录

### 5. NAS 访问

- 使用 SMB/NFS 只读挂载照片目录
- 不要以 root 或管理员权限运行服务
- 定期检查 NAS 访问日志

### 6. 数据库

- SQLite 数据库存放在本地 `data/yinyi.db`
- 定期备份数据库文件
- 不要暴露数据库文件到网络

## 推荐的安全配置

```env
# .env 文件（不要提交到 Git）
PHOTOS_DIR=/path/to/photos
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=sqlite:///./data/yinyi.db
```

```bash
# 文件权限（Linux/Mac）
chmod 600 .env
chmod 700 data/
chmod 700 exports/
```

## 报告安全问题

如发现安全漏洞，请通过 GitHub Issues 私密报告。
