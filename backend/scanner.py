"""
照片扫描器 - 实现 SHA-256 去重
"""

import os
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Set
import piexif
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

from database import SessionLocal, Photo as PhotoModel
from config import settings


#跳过的目录名（NAS 系统目录、缩略图、回收站等）
SKIP_DIRS = {"@eaDir", "@synorec", "@tmp", "@quarantine", "@sharebin", "#recycle", "lost+found"}


# 全局扫描状态
_scanner_state = {
    "status": "idle",  # idle, scanning, completed
    "started_at": None,
    "completed_at": None,
    "lock": threading.Lock()
}


def set_scanner_status(status: str):
    """设置扫描器状态"""
    with _scanner_state["lock"]:
        _scanner_state["status"] = status
        if status == "scanning":
            _scanner_state["started_at"] = datetime.now()
            _scanner_state["completed_at"] = None
        elif status == "completed":
            _scanner_state["completed_at"] = datetime.now()


def get_scanner_status() -> dict:
    """获取扫描器状态"""
    with _scanner_state["lock"]:
        return {
            "status": _scanner_state["status"],
            "started_at": _scanner_state["started_at"],
            "completed_at": _scanner_state["completed_at"]
        }


def compute_file_hash(file_path: str) -> str:
    """计算文件 SHA-256 哈希"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def extract_exif(file_path: str) -> dict:
    """提取 EXIF 信息"""
    exif_data = {}
    try:
        img = Image.open(file_path)
        exif_dict = piexif.load(img.info.get('exif', b''))
        
        # 拍摄时间
        if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
            try:
                exif_data['taken_at'] = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            except:
                pass
        
        # 相机信息
        if piexif.ImageIFD.Make in exif_dict['0th']:
            exif_data['camera'] = exif_dict['0th'][piexif.ImageIFD.Make].decode('utf-8', errors='ignore').strip('\x00')
        if piexif.ImageIFD.Model in exif_dict['0th']:
            exif_data['lens'] = exif_dict['0th'][piexif.ImageIFD.Model].decode('utf-8', errors='ignore').strip('\x00')
        
        # GPS 信息（简化版）
        if piexif.GPSIFD.GPSLatitude in exif_dict['GPS']:
            # TODO: 解析 GPS 坐标为地址
            pass
            
    except Exception as e:
        print(f"EXIF 提取失败 {file_path}: {e}")
    
    return exif_data


def get_image_dimensions(file_path: str) -> tuple:
    """获取图片尺寸（考虑EXIF旋转）"""
    try:
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            return img.size
    except:
        return (None, None)


def is_image_file(filename: str) -> bool:
    """检查是否为支持的图片格式"""
    return filename.lower().endswith(settings.SUPPORTED_FORMATS)


def scan_directory_task(
    path: Optional[str] = None,
    recursive: bool = True,
    check_modified: bool = True
):
    """扫描目录任务（后台执行）"""
    # 设置扫描状态为进行中
    set_scanner_status("scanning")
    
    db = SessionLocal()
    
    try:
        scan_path = Path(path) if path else Path(settings.PHOTOS_DIR)
        
        if not scan_path.exists():
            print(f"扫描路径不存在: {scan_path}")
            set_scanner_status("idle")
            return
        
        print(f"[扫描] 开始扫描: {scan_path}")

        # 获取已有照片的文件哈希集合
        existing_hashes = {p.file_hash for p in db.query(PhotoModel.file_hash).filter(PhotoModel.file_hash != None).all()}
        existing_paths = {p.path for p in db.query(PhotoModel.path).all()}

        new_count = 0
        duplicate_count = 0
        updated_count = 0
        processed = 0
        last_progress = time.time()
        progress_interval = 30

        def _handle_file(full_path: str, filename: str):
            """处理单个文件：检查存在、修改、或新增"""
            nonlocal new_count, duplicate_count, updated_count, processed, last_progress
            processed += 1
            now = time.time()
            if now - last_progress >= progress_interval:
                print(f"[扫描] 已 {processed} 个文件 | 新增 {new_count} 重复 {duplicate_count} 更新 {updated_count}")
                last_progress = now

            if full_path in existing_paths:
                if not check_modified:
                    return
                existing_photo = db.query(PhotoModel).filter(PhotoModel.path == full_path).first()
                if not existing_photo:
                    return
                current_mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                if existing_photo.modified_time == current_mtime:
                    return

                print(f"[更新] 文件已更新: {filename}")
                existing_photo.status = "pending"
                existing_photo.modified_time = current_mtime
                existing_photo.file_size = os.path.getsize(full_path)
                updated_count += 1
                db.commit()
                return

            print(f"[新照片] 发现新照片: {filename}")
            file_hash = compute_file_hash(full_path)
            if file_hash in existing_hashes:
                print(f"[重复] 发现重复: {filename}")
                original = db.query(PhotoModel).filter(PhotoModel.file_hash == file_hash).first()
                photo = PhotoModel(
                    path=full_path, filename=filename, file_hash=file_hash,
                    file_size=os.path.getsize(full_path),
                    modified_time=datetime.fromtimestamp(os.path.getmtime(full_path)),
                    status="duplicate", duplicate_of=original.id if original else None
                )
                duplicate_count += 1
            else:
                exif = extract_exif(full_path)
                width, height = get_image_dimensions(full_path)
                photo = PhotoModel(
                    path=full_path, filename=filename, file_hash=file_hash,
                    file_size=os.path.getsize(full_path), width=width, height=height,
                    modified_time=datetime.fromtimestamp(os.path.getmtime(full_path)),
                    taken_at=exif.get('taken_at'), location=exif.get('location'),
                    camera=exif.get('camera'), lens=exif.get('lens'),
                    status="pending"
                )
                existing_hashes.add(file_hash)
                new_count += 1
            db.add(photo)
            if (new_count + duplicate_count + updated_count) % 10 == 0:
                db.commit()

        def _walk_and_scan(start_path: str):
            """遍历目录树扫描图片文件"""
            for root, dirs, files in os.walk(start_path, topdown=True):
                root_name = os.path.basename(root)
                if root_name in SKIP_DIRS:
                    dirs.clear()
                    continue
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if not is_image_file(f):
                        continue
                    _handle_file(os.path.join(root, f), f)

        # 优先扫描 MobileBackup 和 PhotoLibrary（新增照片的主要来源）
        scan_root = str(scan_path)
        for pri in ["MobileBackup", "PhotoLibrary"]:
            pri_path = os.path.join(scan_root, pri)
            if os.path.isdir(pri_path):
                print(f"[扫描] 优先扫描: {pri}")
                _walk_and_scan(pri_path)

        # 再扫描剩余目录
        already_scanned = [os.path.join(scan_root, d) for d in ["MobileBackup", "PhotoLibrary"]]
        print(f"[扫描] 扫描其他目录...")
        for root, dirs, files in os.walk(scan_root, topdown=True):
            if any(root.startswith(s) for s in already_scanned):
                dirs.clear()
                continue
            root_name = os.path.basename(root)
            if root_name in SKIP_DIRS:
                dirs.clear()
                continue
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if not is_image_file(f):
                    continue
                _handle_file(os.path.join(root, f), f)
        
        db.commit()
        # 设置扫描状态为完成
        set_scanner_status("completed")
        
        print(f"[完成] 扫描完成!")
        print(f"   新增: {new_count}")
        print(f"   重复: {duplicate_count}")
        print(f"   更新: {updated_count}")
        
    except Exception as e:
        print(f"[错误] 扫描失败: {e}")
        set_scanner_status("idle")
        db.rollback()
        raise
    finally:
        db.close()
