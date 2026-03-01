"""
照片管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    year: Optional[int] = None,
    month: Optional[int] = None,
    memory_score_min: Optional[float] = None,
    memory_score_max: Optional[float] = None,
    aesthetic_score_min: Optional[float] = None,
    aesthetic_score_max: Optional[float] = None,
    has_caption: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100000),
    sort_by: str = Query("taken_at", regex="^(taken_at|scanned_at|memory_score|aesthetic_score)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取照片列表"""
    query = db.query(PhotoModel).outerjoin(AnalysisModel)
    
    if status:
        query = query.filter(PhotoModel.status == status)
    
    # 按年份筛选
    if year:
        query = query.filter(
            PhotoModel.taken_at.isnot(None),
            PhotoModel.taken_at >= datetime(year, 1, 1),
            PhotoModel.taken_at < datetime(year + 1, 1, 1)
        )
    
    # 按月份筛选（需要配合年份）
    if month and year:
        if month == 12:
            query = query.filter(
                PhotoModel.taken_at >= datetime(year, month, 1),
                PhotoModel.taken_at < datetime(year + 1, 1, 1)
            )
        else:
            query = query.filter(
                PhotoModel.taken_at >= datetime(year, month, 1),
                PhotoModel.taken_at < datetime(year, month + 1, 1)
            )
    
    # 按回忆分筛选
    if memory_score_min is not None:
        query = query.filter(AnalysisModel.memory_score >= memory_score_min)
    if memory_score_max is not None:
        query = query.filter(AnalysisModel.memory_score <= memory_score_max)
    
    # 按美观分筛选
    if aesthetic_score_min is not None:
        query = query.filter(AnalysisModel.aesthetic_score >= aesthetic_score_min)
    if aesthetic_score_max is not None:
        query = query.filter(AnalysisModel.aesthetic_score <= aesthetic_score_max)
    
    # 筛选有文案的照片
    if has_caption is True:
        query = query.filter(AnalysisModel.caption.isnot(None))
        query = query.filter(AnalysisModel.caption != "")
    
    total = query.count()
    
    # 排序
    if sort_by == "memory_score":
        query = query.order_by(
            AnalysisModel.memory_score.desc() if sort_order == "desc" else AnalysisModel.memory_score.asc()
        )
    elif sort_by == "aesthetic_score":
        query = query.order_by(
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


class YearStatsResponse(BaseModel):
    year: int
    count: int


class PhotoStatsResponse(BaseModel):
    total: int
    years: List[YearStatsResponse]
    analyzed_count: int
    high_memory_count: int
    high_aesthetic_count: int
    with_caption_count: int


@router.get("/stats", response_model=PhotoStatsResponse)
async def get_photo_stats(db: Session = Depends(get_db)):
    """获取照片统计信息"""
    # 获取所有有日期的照片，按年份分组
    year_stats = db.query(
        func.strftime('%Y', PhotoModel.taken_at).label('year'),
        func.count(PhotoModel.id).label('count')
    ).filter(
        PhotoModel.taken_at.isnot(None)
    ).group_by(
        func.strftime('%Y', PhotoModel.taken_at)
    ).order_by(func.strftime('%Y', PhotoModel.taken_at).desc()).all()
    
    years = [YearStatsResponse(year=int(r[0]), count=r[1]) for r in year_stats]
    
    # 统计已分析的照片数量
    analyzed_count = db.query(PhotoModel).filter(PhotoModel.status == 'analyzed').count()
    
    # 统计高分回忆分照片 (>= 80)
    high_memory_count = db.query(PhotoModel).outerjoin(AnalysisModel).filter(
        AnalysisModel.memory_score >= 80
    ).count()
    
    # 统计高分美观分照片 (>= 80)
    high_aesthetic_count = db.query(PhotoModel).outerjoin(AnalysisModel).filter(
        AnalysisModel.aesthetic_score >= 80
    ).count()
    
    # 统计有文案的照片
    with_caption_count = db.query(PhotoModel).outerjoin(AnalysisModel).filter(
        AnalysisModel.caption.isnot(None),
        AnalysisModel.caption != ""
    ).count()
    
    # 总照片数
    total = db.query(PhotoModel).count()
    
    return {
        "total": total,
        "years": years,
        "analyzed_count": analyzed_count,
        "high_memory_count": high_memory_count,
        "high_aesthetic_count": high_aesthetic_count,
        "with_caption_count": with_caption_count
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


class UpdateCaptionRequest(BaseModel):
    caption: str


@router.put("/{photo_id}/caption")
async def update_caption(photo_id: int, request: UpdateCaptionRequest, db: Session = Depends(get_db)):
    """更新照片的文案"""
    photo = db.query(PhotoModel).filter(PhotoModel.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    # 如果没有分析记录，先创建
    if not photo.analysis:
        from database import Analysis as AnalysisModel
        analysis = AnalysisModel(photo_id=photo_id)
        db.add(analysis)
        db.flush()

    # 更新文案
    photo.analysis.caption = request.caption
    db.commit()

    return {"message": "文案已更新", "caption": request.caption}
