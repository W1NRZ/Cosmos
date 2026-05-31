"""Generate thumbnails for library items."""

from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cosmos.config import THUMBNAIL_SIZE, media_type_for_path


def _placeholder(label: str, accent: tuple[int, int, int] = (99, 102, 241)) -> Image.Image:
    w, h = THUMBNAIL_SIZE
    img = Image.new("RGB", (w, h), (18, 18, 24))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([12, 12, w - 12, h - 12], radius=16, outline=accent, width=2)
    text = label.upper()
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2), text, fill=(220, 220, 230), font=font)
    return img


def _save_thumb(img: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    thumb = img.copy()
    thumb.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", THUMBNAIL_SIZE, (18, 18, 24))
    ox = (THUMBNAIL_SIZE[0] - thumb.width) // 2
    oy = (THUMBNAIL_SIZE[1] - thumb.height) // 2
    if thumb.mode == "RGBA":
        canvas.paste(thumb, (ox, oy), thumb)
    else:
        canvas.paste(thumb, (ox, oy))
    canvas.save(dest, "JPEG", quality=85, optimize=True)


def _video_frame_ffmpeg(source: Path) -> Image.Image | None:
    if not shutil.which("ffmpeg"):
        return None
    cmd = [
        "ffmpeg", "-y", "-ss", "1", "-i", str(source),
        "-vframes", "1", "-f", "image2pipe", "-vcodec", "png", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=20)
        if result.returncode == 0 and result.stdout:
            return Image.open(io.BytesIO(result.stdout)).convert("RGB")
    except Exception:
        pass
    return None


def generate_thumbnail(source_path: Path, dest_path: Path) -> Path:
    """Create a JPEG thumbnail for the given media file."""
    source = source_path.expanduser().resolve()
    dest = dest_path.expanduser().resolve()

    try:
        media_type = media_type_for_path(source)
    except ValueError:
        _save_thumb(_placeholder("?"), dest)
        return dest

    try:
        if media_type == "video":
            frame = _video_frame_ffmpeg(source)
            if frame is None:
                _save_thumb(_placeholder("video", (236, 72, 153)), dest)
            else:
                _save_thumb(frame, dest)
        elif media_type == "gif":
            with Image.open(source) as img:
                img.seek(0)
                _save_thumb(img.convert("RGBA"), dest)
        else:
            with Image.open(source) as img:
                _save_thumb(img.convert("RGB"), dest)
    except Exception:
        colors = {"image": (56, 189, 248), "gif": (251, 191, 36), "video": (236, 72, 153)}
        _save_thumb(_placeholder(media_type, colors.get(media_type, (99, 102, 241))), dest)

    return dest
