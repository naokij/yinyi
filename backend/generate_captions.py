"""
为高分照片批量生成文案
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Photo, Analysis
from ai_analyzer import generate_caption, encode_image_to_base64
from dotenv import load_dotenv

load_dotenv()


def batch_generate_captions():
    """为所有高分但没有文案的照片生成文案"""
    db = SessionLocal()
    
    try:
        # 找出已分析、回忆分>=60但没有文案的照片
        photos_needing_caption = db.query(Photo, Analysis).join(Analysis).filter(
            Photo.status == 'analyzed',
            Analysis.memory_score >= 60,
            (Analysis.caption == '') | (Analysis.caption == None)
        ).all()
        
        total = len(photos_needing_caption)
        print(f'找到 {total} 张需要生成文案的高分照片')
        
        if total == 0:
            print('没有需要生成文案的照片')
            return
        
        # API 配置
        api_key = os.getenv("IFLOW_API_KEY") or ""
        base_url = os.getenv("IFLOW_BASE_URL", "https://apis.iflow.cn/v1")
        model = os.getenv("IFLOW_MODEL", "qwen3-vl-plus")
        
        success_count = 0
        fail_count = 0
        
        for idx, (photo, analysis) in enumerate(photos_needing_caption, 1):
            print(f"\n[{idx}/{total}] 处理: {photo.filename}")
            print(f"  回忆分: {analysis.memory_score}")
            
            try:
                # 编码图片
                image_base64 = encode_image_to_base64(photo.path)
                
                # 生成文案
                caption = generate_caption(
                    image_base64, 
                    analysis.description, 
                    api_key, 
                    base_url, 
                    model
                )
                
                if caption:
                    # 保存文案
                    analysis.caption = caption
                    db.commit()
                    print(f"  [OK] 文案: {caption[:40]}...")
                    success_count += 1
                else:
                    print(f"  [FAIL] 文案生成失败")
                    fail_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
                fail_count += 1
                db.rollback()
        
        print(f"\n{'='*50}")
        print(f'完成！成功: {success_count}, 失败: {fail_count}')
        
    finally:
        db.close()


if __name__ == "__main__":
    batch_generate_captions()
