"""
打印渲染器 - 拍立得风格模板
米家 6 寸相纸：100×148mm @ 300 DPI = 1181×1748 px
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
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
    preview: bool = False,
    crop_x: float = 0.5,
    crop_y: float = 0.5,
    crop_scale: float = 1.0
) -> str:
    """
    渲染拍立得风格照片
    
    自动检测照片方向：
    - 竖版 (portrait): 白边在左右，照片 3:4
    - 横版 (landscape): 白边在上下，照片 4:3
    """
    
    # 加载原图检测方向（考虑EXIF旋转）
    with Image.open(photo_path) as img_orig:
        # 使用官方方法处理EXIF方向
        img_orig = ImageOps.exif_transpose(img_orig)
        orig_width, orig_height = img_orig.size
        is_landscape = orig_width > orig_height
    
    # 安全边距（打印时四边会被裁剪，约 3mm = 35px @ 300DPI）
    SAFE_MARGIN = 35
    
    if is_landscape:
        # 横版拍立得：白边在上下，画布横向，照片偏上，文字在下方紧凑排列
        CANVAS_WIDTH = 1748   # 宽度 > 高度（横向画布）
        CANVAS_HEIGHT = 1181
        
        MARGIN_TOP = 30 + SAFE_MARGIN    # 上白边 + 安全边距
        MARGIN_BOTTOM = 200 + SAFE_MARGIN # 下白边（文案区域，紧凑）+ 安全边距
        MARGIN_SIDES = 40 + SAFE_MARGIN   # 左右白边 + 安全边距
        
        PHOTO_WIDTH = CANVAS_WIDTH - (MARGIN_SIDES * 2)
        PHOTO_HEIGHT = CANVAS_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
        target_ratio = PHOTO_WIDTH / PHOTO_HEIGHT  # 4:3
    else:
        # 竖版拍立得：白边在左右（原有逻辑）
        CANVAS_WIDTH = 1181
        CANVAS_HEIGHT = 1748
        
        MARGIN_TOP = 40 + SAFE_MARGIN
        MARGIN_BOTTOM = 375 + SAFE_MARGIN   # 下白边（文案区域）+ 安全边距
        MARGIN_SIDES = 90 + SAFE_MARGIN    # 左右白边 + 安全边距
        
        PHOTO_WIDTH = CANVAS_WIDTH - (MARGIN_SIDES * 2)
        PHOTO_HEIGHT = CANVAS_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
        target_ratio = PHOTO_WIDTH / PHOTO_HEIGHT  # 3:4
    
    # 创建白色画布
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color='white')
    
    # 加载并处理原图
    with Image.open(photo_path) as img:
        # 使用 Pillow 官方方法正确处理 EXIF 方向
        img = ImageOps.exif_transpose(img)
        
        # 转换为 RGB（处理透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, 'white')
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            img = img.convert('RGB')
    
    # 计算裁剪区域（支持手动调整裁切中心）
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            # 图片太宽，裁剪左右
            new_width = int(img.height * target_ratio)
            max_left = img.width - new_width
            left = int(max_left * crop_x)
            left = max(0, min(left, max_left))
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # 图片太高，裁剪上下
            new_height = int(img.width / target_ratio)
            max_top = img.height - new_height
            top = int(max_top * crop_y)
            top = max(0, min(top, max_top))
            img = img.crop((0, top, img.width, top + new_height))
        
        # 缩放到目标尺寸
        img = img.resize((PHOTO_WIDTH, PHOTO_HEIGHT), Image.Resampling.LANCZOS)
        
        # 轻微增强对比度和饱和度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
    
    # 粘贴照片
    if is_landscape:
        canvas.paste(img, (MARGIN_SIDES, MARGIN_TOP))
    else:
        canvas.paste(img, (MARGIN_SIDES, MARGIN_TOP))
    
    # 绘制
    draw = ImageDraw.Draw(canvas)
    
    # 绘制文案区域 - 横版和竖版都在底部白边，紧凑排列
    if is_landscape:
        text_y = MARGIN_TOP + PHOTO_HEIGHT + 40  # 横版在底部白边，紧凑间距
    else:
        text_y = MARGIN_TOP + PHOTO_HEIGHT + 60  # 竖版在底部大白边
    
    # 文案
    if caption:
        font_caption = get_font(48, bold=True)
        words = caption
        max_width = CANVAS_WIDTH - (MARGIN_SIDES * 2)
        
        bbox = draw.textbbox((0, 0), words, font=font_caption)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width:
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
            
            for line in lines[:2]:
                bbox = draw.textbbox((0, 0), line, font=font_caption)
                text_width = bbox[2] - bbox[0]
                x = (CANVAS_WIDTH - text_width) // 2
                draw.text((x, text_y), line, fill='#333333', font=font_caption)
                text_y += 60
        else:
            x = (CANVAS_WIDTH - text_width) // 2
            draw.text((x, text_y), words, fill='#333333', font=font_caption)
            text_y += 70
    
    # 日期和地点
    text_y += 30
    info_parts = []
    if taken_at:
        info_parts.append(taken_at.strftime("%Y.%m.%d"))
    if location:
        info_parts.append(location)
    
    if info_parts:
        info_text = " · ".join(info_parts)
        font_info = get_font(28)
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
    
    # 粘贴照片
    canvas.paste(img, (MARGIN_SIDES, MARGIN_TOP))
    
    # 添加阴影效果（轻微）
    draw = ImageDraw.Draw(canvas)
    
    # 绘制文案区域 - 增大与照片的间距
    text_y = MARGIN_TOP + PHOTO_HEIGHT + 80
    
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
    output_dir: str = "./exports",
    preview: bool = False,
    crop_x: float = 0.5,
    crop_y: float = 0.5,
    crop_scale: float = 1.0
) -> str:
    """
    经典模板：填满画面，文字在底部黑色半透明渐变层上
    
    自动检测照片方向：
    - 竖版：照片填满画面，文字在底部
    - 横版：照片填满画面，文字在底部
    """
    
    # 画布尺寸（竖版）
    CANVAS_WIDTH = 1181
    CANVAS_HEIGHT = 1748
    
    # 安全边距（打印时四边会被裁剪，约 3mm = 35px @ 300DPI）
    SAFE_MARGIN = 35
    
    # 加载原图检测方向（考虑EXIF旋转）
    with Image.open(photo_path) as img_orig:
        img_orig = ImageOps.exif_transpose(img_orig)
        orig_width, orig_height = img_orig.size
        is_landscape = orig_width > orig_height
    
    if is_landscape:
        # 横版：交换宽高
        CANVAS_WIDTH, CANVAS_HEIGHT = CANVAS_HEIGHT, CANVAS_WIDTH
    
    # 照片区域需要留出安全边距
    photo_x = SAFE_MARGIN
    photo_y = SAFE_MARGIN
    photo_width = CANVAS_WIDTH - (SAFE_MARGIN * 2)
    photo_height = CANVAS_HEIGHT - (SAFE_MARGIN * 2)
    
    # 创建白色画布
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color='white')
    
    # 加载并处理原图
    with Image.open(photo_path) as img:
        # 使用 Pillow 官方方法正确处理 EXIF 方向
        img = ImageOps.exif_transpose(img)
        
        # 转换为 RGB（处理透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, 'white')
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            img = img.convert('RGB')
    
    # 填满整个画布（保持比例，可能裁切）- 使用带安全边距的区域
        img_ratio = img.width / img.height
        target_ratio = photo_width / photo_height
        
        if img_ratio > target_ratio:
            # 图片太宽，裁剪左右
            new_width = int(img.height * target_ratio)
            max_left = img.width - new_width
            left = int(max_left * crop_x)
            left = max(0, min(left, max_left))
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # 图片太高，裁剪上下
            new_height = int(img.width / target_ratio)
            max_top = img.height - new_height
            top = int(max_top * crop_y)
            top = max(0, min(top, max_top))
            img = img.crop((0, top, img.width, top + new_height))
        
        # 缩放到带安全边距的尺寸
        img = img.resize((photo_width, photo_height), Image.Resampling.LANCZOS)
        
        # 轻微增强
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)
    
    # 粘贴照片（带安全边距）
    canvas.paste(img, (photo_x, photo_y))
    
    # 绘制底部渐变层
    draw = ImageDraw.Draw(canvas)
    
    # 底部渐变区域高度
    gradient_height = 350 if not is_landscape else 300
    
    # 创建渐变层（从透明到黑色）
    gradient = Image.new('RGBA', (CANVAS_WIDTH, gradient_height), color=(0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    
    for y in range(gradient_height):
        alpha = int(200 * (y / gradient_height))  # 0-200 渐变
        gradient_draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(0, 0, 0, alpha))
    
    # 粘贴渐变层到底部
    canvas.paste(gradient, (0, CANVAS_HEIGHT - gradient_height), mask=gradient)
    
    # 绘制文案（在渐变层底部，白色文字）
    # 先计算文案需要的行数
    caption_lines = 1
    if caption:
        font_caption = get_font(42, bold=True)
        words = caption
        max_width = CANVAS_WIDTH - 80
        bbox = draw.textbbox((0, 0), words, font=font_caption)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width:
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
            caption_lines = min(len(lines), 2)
    
    # 文字从渐变区域底部向上计算位置
    # 预留底部边距
    bottom_margin = 40
    line_height = 55
    
    # 计算起始Y坐标（从底部往上）
    text_y = CANVAS_HEIGHT - bottom_margin - (caption_lines * line_height)
    
    # 文案
    if caption:
        font_caption = get_font(42, bold=True)
        words = caption
        max_width = CANVAS_WIDTH - 80
        
        bbox = draw.textbbox((0, 0), words, font=font_caption)
        text_width = bbox[2] - bbox[0]
        
        if text_width > max_width:
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
            
            for line in lines[:2]:
                bbox = draw.textbbox((0, 0), line, font=font_caption)
                text_width = bbox[2] - bbox[0]
                x = (CANVAS_WIDTH - text_width) // 2
                draw.text((x, text_y), line, fill='#FFFFFF', font=font_caption)
                text_y += 55
            # 文案和日期之间留出间距
            text_y += 30
        else:
            x = (CANVAS_WIDTH - text_width) // 2
            draw.text((x, text_y), words, fill='#FFFFFF', font=font_caption)
            # 文案和日期之间留出间距 - 增大间距避免重叠
            text_y += 50
    
    # 日期和地点 - 使用文案结束后的位置
    if taken_at or location:
        info_parts = []
        if taken_at:
            info_parts.append(taken_at.strftime("%Y.%m.%d"))
        if location:
            info_parts.append(location)
        
        info_text = " · ".join(info_parts)
        font_info = get_font(24)
        bbox = draw.textbbox((0, 0), info_text, font=font_info)
        text_width = bbox[2] - bbox[0]
        x = (CANVAS_WIDTH - text_width) // 2
        draw.text((x, text_y), info_text, fill='#CCCCCC', font=font_info)
    
    # 保存
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"classic_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)
    
    canvas.save(output_path, "PNG", quality=95)
    
    return output_path
