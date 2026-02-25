"""
重新提取照片元数据
用于修复扫描时缺少 EXIF 信息的照片
"""
import sys
sys.path.insert(0, '.')

from database import get_db
from database import Photo
from scanner import extract_exif, get_image_dimensions
import os
from datetime import datetime
from pathlib import Path


def fix_metadata(batch_size: int = 100):
    db = next(get_db())
    
    # 查找缺少 taken_at 或 width/height 的照片
    photos = db.query(Photo).filter(
        (Photo.taken_at == None) | (Photo.width == None)
    ).limit(batch_size).all()
    
    if not photos:
        print("没有需要修复的照片")
        db.close()
        return 0
    
    print(f"找到 {len(photos)} 张需要修复的照片")
    
    fixed = 0
    for photo in photos:
        if not os.path.exists(photo.path):
            print(f"  跳过: 文件不存在 - {photo.filename}")
            continue
        
        try:
            # 提取 EXIF
            exif = extract_exif(photo.path)
            
            # 获取尺寸
            width, height = get_image_dimensions(photo.path)
            
            # 更新
            updated = False
            if photo.taken_at is None:
                # 优先使用 EXIF 日期
                if exif.get('taken_at'):
                    photo.taken_at = exif['taken_at']
                    updated = True
                # 否则使用文件修改时间
                else:
                    try:
                        mtime = Path(photo.path).stat().st_mtime
                        photo.taken_at = datetime.fromtimestamp(mtime)
                        updated = True
                    except:
                        pass
            if photo.width is None and width:
                photo.width = width
                photo.height = height
                updated = True
            if photo.camera is None and exif.get('camera'):
                photo.camera = exif['camera']
                updated = True
            if photo.lens is None and exif.get('lens'):
                photo.lens = exif['lens']
                updated = True
            
            if updated:
                fixed += 1
                print(f"  修复: {photo.filename} - taken_at={photo.taken_at}, size={photo.width}x{photo.height}")
            
        except Exception as e:
            print(f"  错误: {photo.filename} - {e}")
    
    db.commit()
    db.close()
    return fixed


if __name__ == "__main__":
    total_fixed = 0
    while True:
        fixed = fix_metadata(100)
        if fixed == 0:
            break
        total_fixed += fixed
        print(f"本批次修复: {fixed}, 总计: {total_fixed}\n")
    
    print(f"完成! 总共修复: {total_fixed} 张照片")
