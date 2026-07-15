"""
补跑文案：为已有分析结果但缺文案的高评分照片重新生成 caption
"""
import os, sys, time, threading
sys.path.insert(0, os.path.dirname(__file__))
os.environ['ENABLE_CAPTION'] = 'true'
os.environ['ENABLE_CAPTION_THINKING'] = 'false'
os.environ['CAPTION_MIN_MEMORY'] = '80'

from database import SessionLocal, Photo, Analysis
from ai_analyzer import encode_image_to_base64, generate_caption, validate_caption

BATCH_SIZE = 5  # 并发数
SLEEP_BETWEEN = 0.5  # 请求间隔

def process_one(photo_id: int, description: str, path: str):
    try:
        img = encode_image_to_base64(path)
        if not img:
            return None
        api_key = os.getenv('IFLOW_API_KEY', '')
        base_url = os.getenv('IFLOW_BASE_URL', 'https://apihub.agnes-ai.com/v1')
        model = os.getenv('IFLOW_MODEL', 'agnes-2.0-flash')
        raw = generate_caption(img, description or '', api_key, base_url, model)
        caption = validate_caption(raw)
        return caption
    except Exception as e:
        return None

def worker(tasks, idx):
    db = SessionLocal()
    done = 0
    for photo_id, desc, path, filename in tasks:
        caption = process_one(photo_id, desc, path)
        if caption:
            a = db.query(Analysis).filter(Analysis.photo_id == photo_id).first()
            if a:
                a.caption = caption
                db.commit()
                done += 1
                print(f"[{idx}] +{done} {filename} → {caption}")
        else:
            print(f"[{idx}] - {filename} (校验未通过)")
        time.sleep(SLEEP_BETWEEN)
    db.close()
    return done

if __name__ == '__main__':
    db = SessionLocal()
    results = db.query(Photo, Analysis).join(Analysis).filter(
        Analysis.memory_score >= 80,
        (Analysis.caption == None) | (Analysis.caption == '')
    ).all()
    tasks = [(p.id, a.description, p.path, p.filename) for p, a in results]
    db.close()
    print(f"待补文案: {len(tasks)} 张")

    # 分片给多个 worker
    chunk_size = (len(tasks) + BATCH_SIZE - 1) // BATCH_SIZE
    chunks = [tasks[i:i+chunk_size] for i in range(0, len(tasks), chunk_size)]
    threads = []
    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=worker, args=(chunk, i), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    print("全部完成!")
