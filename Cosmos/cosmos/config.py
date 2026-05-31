"""Application paths and constants."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Cosmos"
APP_VERSION = "1.0.0"

# ~/Library/Application Support/Cosmos/
APP_SUPPORT = Path.home() / "Library" / "Application Support" / APP_NAME
LIBRARY_DIR = APP_SUPPORT / "library"
THUMBNAILS_DIR = APP_SUPPORT / "thumbnails"
DATA_FILE = APP_SUPPORT / "library.json"
SETTINGS_FILE = APP_SUPPORT / "settings.json"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".heic", ".heif"}
SUPPORTED_GIF_EXTENSIONS = {".gif"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_GIF_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

THUMBNAIL_SIZE = (320, 180)


def ensure_dirs() -> None:
    """Create application support directories if they do not exist."""
    for path in (APP_SUPPORT, LIBRARY_DIR, THUMBNAILS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def media_type_for_path(path: str | Path) -> str:
    """Return 'image', 'gif', or 'video' for a file path."""
    ext = Path(path).suffix.lower()
    if ext in SUPPORTED_GIF_EXTENSIONS:
        return "gif"
    if ext in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    raise ValueError(f"Unsupported file type: {ext}")
