"""
数据库模型和连接
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from config import settings


Base = declarative_base()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Photo(Base):
    """照片表"""
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    
    # 文件指纹
    file_hash = Column(String(64), index=True)
    phash = Column(String(32), index=True)  # 感知哈希（预留）
    
    # 文件信息
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    modified_time = Column(DateTime)
    
    # EXIF 信息
    taken_at = Column(DateTime, index=True)
    location = Column(String(255))
    camera = Column(String(100))
    lens = Column(String(100))
    
    # 状态
    status = Column(String(20), default="pending")  # pending, analyzed, duplicate, error
    duplicate_of = Column(Integer, ForeignKey("photos.id"), nullable=True)
    
    # 元数据
    scanned_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    analysis = relationship("Analysis", back_populates="photo", uselist=False)
    duplicate_photo = relationship("Photo", remote_side=[id], backref="duplicates")
    
    __table_args__ = (
        Index('idx_file_hash', 'file_hash'),
        Index('idx_status', 'status'),
        Index('idx_taken_at', 'taken_at'),
    )


class Analysis(Base):
    """AI 分析结果表"""
    __tablename__ = "analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), unique=True)
    
    # AI 分析内容
    description = Column(Text)  # 画面描述
    caption = Column(Text)      # 感性文案（核心）
    tags = Column(Text)         # 标签，JSON 格式

    # 评分
    memory_score = Column(Float)      # 回忆价值 0-10
    aesthetic_score = Column(Float)   # 美观度 0-10
    sentiment = Column(String(20))    # 情感倾向

    # InkTime 扩展字段
    photo_type = Column(Text)    # 照片类型：人物/家庭/旅行/风景等
    reason = Column(Text)        # 评分理由

    # 分析元数据
    model = Column(String(100))       # 使用的模型
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    photo = relationship("Photo", back_populates="analysis")


class Export(Base):
    """导出记录表"""
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"))
    
    # 导出信息
    template_type = Column(String(50))  # polaroid, classic, story...
    export_path = Column(String(500))
    format = Column(String(10))         # png, pdf
    
    # 导出设置
    settings = Column(Text)  # JSON 格式的导出参数
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    photo = relationship("Photo")


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
