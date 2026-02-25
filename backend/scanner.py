"""
照片扫描器 - 实现 SHA-256 去重
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Set
import piexif
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

from database import SessionLocal, Photo as PhotoModel
from config import settings


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
    """获取图片尺寸"""
    try:
        with Image.open(file_path) as img:
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
    db = SessionLocal()
    
    try:
        scan_path = Path(path) if path else Path(settings.PHOTOS_DIR)
        
        if not scan_path.exists():
            print(f"扫描路径不存在: {scan_path}")
            return
        
        print(f"[扫描] 开始扫描: {scan_path}")
        
        # 获取已有照片的文件哈希集合
        existing_hashes = {p.file_hash for p in db.query(PhotoModel.file_hash).filter(PhotoModel.file_hash != None).all()}
        existing_paths = {p.path for p in db.query(PhotoModel.path).all()}
        
        new_count = 0
        duplicate_count = 0
        updated_count = 0
        
        # 遍历文件
        pattern = "**/*" if recursive else "*"
        for file_path in scan_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            if not is_image_file(file_path.name):
                continue
            
            str_path = str(file_path)
            
            # 检查路径是否已存在
            existing_photo = db.query(PhotoModel).filter(PhotoModel.path == str_path).first()
            
            if existing_photo:
                if not check_modified:
                    continue
                
                # 检查文件是否修改
                current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if existing_photo.modified_time == current_mtime:
                    continue
                
                # 文件已更新，重新处理
                print(f"[更新] 文件已更新: {file_path.name}")
                existing_photo.status = "pending"
                existing_photo.modified_time = current_mtime
                existing_photo.file_size = file_path.stat().st_size
                updated_count += 1
                db.commit()
                continue
            
            # 新文件，计算哈希
            print(f"[新照片] 发现新照片: {file_path.name}")
            file_hash = compute_file_hash(str_path)
            
            # 检查是否重复
            if file_hash in existing_hashes:
                print(f"[重复] 发现重复: {file_path.name}")
                # 找到原图
                original = db.query(PhotoModel).filter(PhotoModel.file_hash == file_hash).first()
                
                photo = PhotoModel(
                    path=str_path,
                    filename=file_path.name,
                    file_hash=file_hash,
                    file_size=file_path.stat().st_size,
                    modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    status="duplicate",
                    duplicate_of=original.id if original else None
                )
                duplicate_count += 1
            else:
                # 提取 EXIF 和图片信息
                exif = extract_exif(str_path)
                width, height = get_image_dimensions(str_path)
                
                photo = PhotoModel(
                    path=str_path,
                    filename=file_path.name,
                    file_hash=file_hash,
                    file_size=file_path.stat().st_size,
                    width=width,
                    height=height,
                    modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    taken_at=exif.get('taken_at'),
                    location=exif.get('location'),
                    camera=exif.get('camera'),
                    lens=exif.get('lens'),
                    status="pending"
                )
                existing_hashes.add(file_hash)
                new_count += 1
            
            db.add(photo)
            
            # 每 10 张提交一次
            if (new_count + duplicate_count + updated_count) % 10 == 0:
                db.commit()
        
        db.commit()
        
        print(f"[完成] 扫描完成!")
        print(f"   新增: {new_count}")
        print(f"   重复: {duplicate_count}")
        print(f"   更新: {updated_count}")
        
    except Exception as e:
        print(f"[错误] 扫描失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()
