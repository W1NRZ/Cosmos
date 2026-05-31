"""Unified wallpaper application service."""

from __future__ import annotations

from pathlib import Path

from cosmos.config import media_type_for_path
from cosmos.wallpaper.image import set_image_wallpaper
from cosmos.wallpaper.media_player import DesktopMediaWallpaper


class WallpaperService:
    """Apply backgrounds by media type using the best available macOS method."""

    def __init__(self) -> None:
        self._media = DesktopMediaWallpaper.instance()
        self._active_id: str | None = None
        self._active_path: str | None = None
        self._active_type: str | None = None

    @property
    def active_id(self) -> str | None:
        return self._active_id

    @property
    def active_path(self) -> str | None:
        return self._active_path

    @property
    def active_type(self) -> str | None:
        return self._active_type

    @property
    def is_media_playing(self) -> bool:
        return self._media.is_active

    def apply(self, item_id: str, file_path: str | Path) -> tuple[bool, str]:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            return False, f"File not found: {path}"

        try:
            media_type = media_type_for_path(path)
        except ValueError as exc:
            return False, str(exc)

        if media_type == "image":
            self._media.stop()
            ok, msg = set_image_wallpaper(path)
        elif media_type in ("gif", "video"):
            ok, msg = self._media.apply(path, media_type)
        else:
            return False, f"Unsupported media type: {media_type}"

        if ok:
            self._active_id = item_id
            self._active_path = str(path)
            self._active_type = media_type

        return ok, msg

    def stop_media(self) -> None:
        self._media.stop()

    def get_status(self) -> dict:
        return {
            "activeId": self._active_id,
            "activePath": self._active_path,
            "activeType": self._active_type,
            "mediaPlaying": self._media.is_active,
        }
