"""
照片管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db, Photo as PhotoModel, Analysis as AnalysisModel


router = APIRouter()


class PhotoResponse(BaseModel):
    id: int
    path: str
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[datetime] = None
    location: Optional[str] = None
    status: str
    memory_score: Optional[float] = None
    aesthetic_score: Optional[float] = None
    caption: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, photo):
        """从 ORM 对象创建响应，包含关联的分析数据"""
        data = {
            "id": photo.id,
            "path": photo.path,
            "filename": photo.filename,
            "width": photo.width,
            "height": photo.height,
            "taken_at": photo.taken_at,
            "location": photo.location,
            "status": photo.status,
            "memory_score": photo.analysis.memory_score if photo.analysis else None,
            "aesthetic_score": photo.analysis.aesthetic_score if photo.analysis else None,
            "caption": photo.analysis.caption if photo.analysis else None
        }
        return cls(**data)


class PhotoListResponse(BaseModel):
    total: int
    photos: List[PhotoResponse]
    page: int
    page_size: int


@router.get("/", response_model=PhotoListResponse)
async def list_photos(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=5000),
    sort_by: str = Query("taken_at", regex="^(taken_at|scanned_at|memory_score|aesthetic_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取照片列表"""
    query = db.query(PhotoModel)
    
    if status:
        query = query.filter(PhotoModel.status == status)
    
    total = query.count()
    
    # 排序
    if sort_by == "memory_score":
        query = query.outerjoin(AnalysisModel).order_by(
            AnalysisModel.memory_score.desc() if sort_order == "desc" else AnalysisModel.memory_score.asc()
        )
    elif sort_by == "aesthetic_score":
        query = query.outerjoin(AnalysisModel).order_by(
            AnalysisModel.aesthetic_score.desc() if sort_order == "desc" else AnalysisModel.aesthetic_score.asc()
        )
    else:
        order_col = getattr(PhotoModel, sort_by)
        query = query.order_by(order_col.desc() if sort_order == "desc" else order_col.asc())
    
    photos = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 转换为响应模型
    photo_responses = [PhotoResponse.from_orm(p) for p in photos]
    
    return {
        "total": total,
        "photos": photo_responses,
        "page": page,
        "page_size": page_size
    }


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """获取单张照片详情"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return PhotoResponse.from_orm(photo)


@router.get("/{photo_id}/file")
async def get_photo_file(photo_id: int, db: Session = Depends(get_db)):
    """获取照片文件（HEIC 自动转码为 JPEG）"""
    import os
    from pathlib import Path
    from starlette.responses import FileResponse as StarletteFileResponse
    
    # 导入缓存管理器
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from cache_manager import get_cache_manager

    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    if not os.path.exists(photo.path):
        raise HTTPException(status_code=404, detail="照片文件不存在")

    file_path = photo.path
    is_heic = photo.path.lower().endswith('.heic')
    cache_manager = None
    
    # 检查是否是 HEIC 格式
    if is_heic:
        cache_manager = get_cache_manager()
        cache_path = cache_manager.get_cache_path(photo_id)
        
        # 如果缓存不存在，转码
        if not cache_path.exists():
            try:
                # 确保缓存目录存在
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                
                from PIL import Image
                from pillow_heif import register_heif_opener
                
                register_heif_opener()
                
                # 打开 HEIC 并保存为 JPEG
                img = Image.open(photo.path)
                
                # 转换为 RGB（去除透明通道）
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 保存为 JPEG，质量 90%
                img.save(cache_path, 'JPEG', quality=90, optimize=True)
                
                print(f"[HEIC] 转码完成: {photo.filename} -> {cache_path}")
                
            except Exception as e:
                print(f"[HEIC] 转码失败: {photo.filename}, 错误: {e}")
                raise HTTPException(status_code=500, detail=f"HEIC 转码失败: {str(e)}")
        else:
            # 更新缓存文件访问时间（用于 LRU 策略）
            cache_manager.update_access_time(cache_path)
        
        file_path = str(cache_path)
    
    # 使用 Starlette FileResponse 但手动设置 headers
    response = StarletteFileResponse(
        path=file_path,
        media_type="image/jpeg"
    )
    # 移除 content-disposition header
    if "content-disposition" in response.headers:
        del response.headers["content-disposition"]
    
    # 异步触发缓存清理（不阻塞响应）
    if is_heic and cache_manager:
        cache_manager.cleanup_async()
    
    return response


@router.delete("/{photo_id}")
async def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """删除照片记录（不删除文件）"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 级联删除分析结果
    if photo.analysis:
        db.delete(photo.analysis)
    
    db.delete(photo)
    db.commit()
    
    return {"message": "照片记录已删除"}


@router.get("/{photo_id}/thumbnail")
async def get_thumbnail(photo_id: int, size: int = Query(300, ge=50, le=800), db: Session = Depends(get_db)):
    """获取照片缩略图"""
    # TODO: 实现缩略图生成和缓存
    pass
