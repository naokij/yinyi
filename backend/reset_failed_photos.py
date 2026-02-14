from database import SessionLocal, Photo as PhotoModel

db = SessionLocal()
try:
    # 查找所有状态为 error 或 analyzing 的照片
    failed_photos = db.query(PhotoModel).filter(
        PhotoModel.status.in_(['error', 'analyzing'])
    ).all()
    
    print(f"找到 {len(failed_photos)} 张需要重新分析的照片")
    print("照片列表:")
    for photo in failed_photos[:10]:  # 只显示前10张
        print(f"  - ID {photo.id}: {photo.filename} (当前状态: {photo.status})")
    
    if len(failed_photos) > 10:
        print(f"  ... 还有 {len(failed_photos) - 10} 张")
    
    if failed_photos:
        # 重置状态为 pending
        for photo in failed_photos:
            photo.status = 'pending'
        db.commit()
        print(f"\n✓ 已重置 {len(failed_photos)} 张照片为待分析状态")
        print("请在 Web 界面点击"分析照片"按钮开始分析")
    else:
        print("\n没有需要重置的照片")
        
except Exception as e:
    print(f"错误: {e}")
    db.rollback()
finally:
    db.close()
