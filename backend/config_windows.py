"""
Windows 原生部署配置
"""

from pydantic_settings import BaseSettings
from pathlib import Path
import os
import platform


class Settings(BaseSettings):
    """应用配置 - Windows 优化版"""
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./data/yinyi.db"
    
    # 目录配置（Windows 路径支持）
    PHOTOS_DIR: str = "Z:\\Photos" if platform.system() == "Windows" else "./photos"
    EXPORTS_DIR: str = "./exports"
    FONTS_DIR: str = "./fonts"
    TEMPLATES_DIR: str = "./templates"
    
    # AI 服务配置（Windows Host Ollama）
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3-vl:4b"
    AI_BACKEND: str = "ollama"
    
    # 扫描配置
    SUPPORTED_FORMATS: tuple = ('.jpg', '.jpeg', '.png', '.heic', '.bmp', '.tiff', '.webp')
    
    # 打印模板配置（米家 6 寸：100×148mm @ 300 DPI）
    PRINT_WIDTH_MM: int = 100
    PRINT_HEIGHT_MM: int = 148
    PRINT_DPI: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def print_width_px(self) -> int:
        """打印宽度像素"""
        return int(self.PRINT_WIDTH_MM * self.PRINT_DPI / 25.4)
    
    @property
    def print_height_px(self) -> int:
        """打印高度像素"""
        return int(self.PRINT_HEIGHT_MM * self.PRINT_DPI / 25.4)
    
    @property
    def photos_dir_resolved(self) -> Path:
        """解析照片目录路径（支持 Windows UNC 路径）"""
        return Path(self.PHOTOS_DIR)


settings = Settings()
