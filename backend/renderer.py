"""
打印渲染器 - 拍立得风格模板
米家 6 寸相纸：100×148mm @ 300 DPI = 1181×1748 px
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

from config import settings


def get_font(font_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """获取字体 - 优先使用项目字体"""
    # 优先使用项目字体目录中的霞鹜文楷
    font_paths = [
        # 项目字体目录（优先）
        os.path.join(settings.FONTS_DIR, "LXGWWenKai-Regular.ttf"),
        os.path.join(settings.FONTS_DIR, "LXGWWenKai-Bold.ttf"),
        # Windows 中文字体（备用）
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simkai.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # 备用英文
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    font_path = font_paths[1] if bold and len(font_paths) > 1 else font_paths[0]
    
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                print(f"[Font] 成功加载字体: {fp}, 大小: {font_size}")
                return font
            except Exception as e:
                print(f"[Font] 加载字体失败: {fp}, {e}")
                continue
    
    # 如果都找不到，使用默认字体
    print(f"[Font] 使用默认字体，大小: {font_size}")
    return ImageFont.load_default()


def render_polaroid(
    photo_path: str,
    caption: Optional[str] = None,
    taken_at: Optional[datetime] = None,
    location: Optional[str] = None,
    output_dir: str = "./exports",
    preview: bool = False
) -> str:
    """
    渲染拍立得风格照片
    
    布局：
    - 画布：1181×1748 px (100×148mm @ 300 DPI)
    - 上白边：40 px
    - 照片区域：1000×1333 px (居中，保持 3:4 比例)
    - 下白边：375 px（用于文案和日期）
    - 左右白边：90.5 px
    """
    
    # 画布尺寸
    CANVAS_WIDTH = 1181
    CANVAS_HEIGHT = 1748
    
    # 边距
    MARGIN_TOP = 40
    MARGIN_BOTTOM = 375
    MARGIN_SIDES = 90
    
    # 照片区域
    PHOTO_WIDTH = CANVAS_WIDTH - (MARGIN_SIDES * 2)
    PHOTO_HEIGHT = CANVAS_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    
    # 创建白色画布
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color='white')
    
    # 加载并处理原图
    with Image.open(photo_path) as img:
        # 转换为 RGB（处理透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, 'white')
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            img = img.convert('RGB')
        
        # 计算裁剪区域（保持比例，居中裁剪）
        img_ratio = img.width / img.height
        target_ratio = PHOTO_WIDTH / PHOTO_HEIGHT
        
        if img_ratio > target_ratio:
            # 图片太宽，裁剪左右
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # 图片太高，裁剪上下
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # 缩放到目标尺寸
        img = img.resize((PHOTO_WIDTH, PHOTO_HEIGHT), Image.Resampling.LANCZOS)
        
        # 轻微增强对比度和饱和度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
    
    # 粘贴照片
    canvas.paste(img, (MARGIN_SIDES, MARGIN_TOP))
    
    # 添加阴影效果（轻微）
    draw = ImageDraw.Draw(canvas)
    
    # 绘制文案区域
    text_y = MARGIN_TOP + PHOTO_HEIGHT + 50
    
    # 文案
    if caption:
        font_caption = get_font(48, bold=True)  # 增大字体
        # 文本换行处理
        words = caption
        max_width = CANVAS_WIDTH - (MARGIN_SIDES * 2)
        
        # 简单处理：如果太长就截断
        bbox = draw.textbbox((0, 0), words, font=font_caption)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width:
            # 需要换行
            lines = []
            current_line = ""
            for char in words:
                test_line = current_line + char
                bbox = draw.textbbox((0, 0), test_line, font=font_caption)
                if bbox[2] - bbox[0] > max_width and current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
            
            # 绘制多行
            for line in lines[:2]:  # 最多两行
                bbox = draw.textbbox((0, 0), line, font=font_caption)
                text_width = bbox[2] - bbox[0]
                x = (CANVAS_WIDTH - text_width) // 2
                draw.text((x, text_y), line, fill='#333333', font=font_caption)
                text_y += 60  # 增大行距
        else:
            x = (CANVAS_WIDTH - text_width) // 2
            draw.text((x, text_y), words, fill='#333333', font=font_caption)
            text_y += 70  # 增大行距
    
    # 日期和地点
    text_y += 30
    info_parts = []
    if taken_at:
        info_parts.append(taken_at.strftime("%Y.%m.%d"))
    if location:
        info_parts.append(location)
    
    if info_parts:
        info_text = " · ".join(info_parts)
        font_info = get_font(28)  # 增大字体
        bbox = draw.textbbox((0, 0), info_text, font=font_info)
        text_width = bbox[2] - bbox[0]
        x = (CANVAS_WIDTH - text_width) // 2
        draw.text((x, text_y), info_text, fill='#888888', font=font_info)
    
    # 保存
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"polaroid_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)
    
    canvas.save(output_path, "PNG", quality=95)
    
    return output_path


def render_classic(
    photo_path: str,
    caption: Optional[str] = None,
    taken_at: Optional[datetime] = None,
    location: Optional[str] = None,
    output_dir: str = "./exports"
) -> str:
    """
    经典单张模板（填满画面，文字在底部黑色渐变层上）
    预留功能，Phase 2 实现
    """
    # TODO: 实现经典风格模板
    pass
