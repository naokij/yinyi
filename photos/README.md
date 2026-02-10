# 照片目录

将你的照片放入此目录，或创建软链接指向你的照片库。

## 支持格式

- JPG / JPEG
- PNG
- HEIC (iPhone)
- RAW / CR2 / NEF (相机原片)

## 使用方法

### 方式1：直接复制
```bash
cp -r /path/to/your/photos/* ./photos/
```

### 方式2：创建软链接（推荐）
```bash
ln -s /path/to/your/photos /path/to/yinyi/photos
```

### 方式3：Docker Compose 挂载
修改 `docker-compose.yml`：
```yaml
backend:
  volumes:
    - /your/actual/photos/path:/app/photos:ro
```

## 注意事项

- 程序使用 SHA-256 哈希去重，相同文件不会重复处理
- 支持增量扫描，新增照片会自动识别
- 原始文件不会被修改，只读取
