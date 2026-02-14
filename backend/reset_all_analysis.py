#!/usr/bin/env python3
"""
重置所有照片分析数据
- 删除所有分析记录
- 清空分数和评语
- 重置状态为待分析
"""

import sys
sys.path.insert(0, '.')

from database import SessionLocal, Photo as PhotoModel, Analysis as AnalysisModel
from sqlalchemy import func

def reset_all_analysis():
    db = SessionLocal()
    try:
        # 获取统计信息
        total_photos = db.query(PhotoModel).count()
        analyzed_count = db.query(PhotoModel).filter(PhotoModel.status == 'analyzed').count()
        error_count = db.query(PhotoModel).filter(PhotoModel.status == 'error').count()
        pending_count = db.query(PhotoModel).filter(PhotoModel.status == 'pending').count()
        analysis_records = db.query(AnalysisModel).count()
        
        print("=" * 60)
        print("重置照片分析数据")
        print("=" * 60)
        print()
        print(f"当前状态统计:")
        print(f"  总照片数: {total_photos}")
        print(f"  已分析:   {analyzed_count}")
        print(f"  分析失败: {error_count}")
        print(f"  待分析:   {pending_count}")
        print(f"  分析记录: {analysis_records}")
        print()
        
        # 确认操作
        confirm = input("确定要重置所有照片的分析数据吗？这将删除所有分数、评语和分析记录。(yes/no): ")
        if confirm.lower() != 'yes':
            print("操作已取消")
            return
        
        print()
        print("正在重置...")
        
        # 1. 删除所有分析记录
        deleted_analysis = db.query(AnalysisModel).delete()
        print(f"✓ 已删除 {deleted_analysis} 条分析记录")
        
        # 2. 重置所有照片状态为 pending
        updated_photos = db.query(PhotoModel).update({
            PhotoModel.status: 'pending'
        })
        print(f"✓ 已重置 {updated_photos} 张照片状态为待分析")
        
        # 3. 提交更改
        db.commit()
        
        print()
        print("=" * 60)
        print("重置完成！")
        print("=" * 60)
        print()
        print("所有照片已重置为初始状态：")
        print("  - 分析记录已清空")
        print("  - 分数和评语已删除")
        print("  - 状态重置为待分析")
        print()
        print("请在 Web 界面点击「AI 分析全部」开始重新分析")
        
    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_analysis()
