"""Desktop-level media player for GIF and video wallpapers."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QWidget

# kCGDesktopWindowLevel — behind desktop icons
_MACOS_DESKTOP_LEVEL = -2147483623


def _set_macos_desktop_level(widget: QWidget) -> None:
    """Place window at desktop level behind icons on macOS."""
    if sys.platform != "darwin":
        return
    try:
        import Cocoa

        handle = widget.windowHandle()
        if handle is None:
            return
        ns_view = Cocoa.NSView(int(handle.winId()))
        ns_window = ns_view.window()
        ns_window.setLevel_(_MACOS_DESKTOP_LEVEL)
        ns_window.setCollectionBehavior_(
            Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces
            | Cocoa.NSWindowCollectionBehaviorStationary
            | Cocoa.NSWindowCollectionBehaviorIgnoresCycle
        )
    except Exception:
        pass


def _media_html(media_path: Path, media_type: str) -> str:
    file_url = QUrl.fromLocalFile(str(media_path)).toString()
    if media_type == "gif":
        body = f'<img src="{file_url}" alt="">'
    else:
        body = f"""
<video autoplay loop muted playsinline>
  <source src="{file_url}">
</video>"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; }}
html, body {{ width:100%; height:100%; overflow:hidden; background:#000; }}
img, video {{
  width:100vw; height:100vh;
  object-fit:cover;
  display:block;
}}
</style></head>
<body>{body}</body></html>"""


class DesktopMediaWallpaper:
    """Fullscreen looping media wallpaper rendered behind desktop icons."""

    _instance: "DesktopMediaWallpaper | None" = None

    def __init__(self) -> None:
        self._windows: list[_MediaWindow] = []
        self._current_path: str | None = None
        self._media_type: str | None = None

    @classmethod
    def instance(cls) -> "DesktopMediaWallpaper":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_active(self) -> bool:
        return bool(self._windows)

    @property
    def current_path(self) -> str | None:
        return self._current_path

    def stop(self) -> None:
        for window in self._windows:
            window.cleanup()
            window.close()
        self._windows.clear()
        self._current_path = None
        self._media_type = None

    def apply(self, media_path: str | Path, media_type: str) -> tuple[bool, str]:
        path = Path(media_path).expanduser().resolve()
        if not path.is_file():
            return False, f"File not found: {path}"

        self.stop()

        if QApplication.instance() is None:
            return False, "No Qt application running"

        screens = QGuiApplication.screens()
        if not screens:
            return False, "No displays detected"

        for screen in screens:
            window = _MediaWindow(path, media_type, screen)
            window.show()
            _set_macos_desktop_level(window)
            self._windows.append(window)

        self._current_path = str(path)
        self._media_type = media_type
        label = "GIF" if media_type == "gif" else "Video"
        return True, f"{label} wallpaper playing on desktop"

    def pause_all(self) -> None:
        for window in self._windows:
            window.pause()

    def resume_all(self) -> None:
        for window in self._windows:
            window.resume()


class _MediaWindow(QWidget):
    """Per-display fullscreen media wallpaper window."""

    def __init__(self, media_path: Path, media_type: str, screen) -> None:
        super().__init__()
        self._media_type = media_type

        self.setGeometry(screen.geometry())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnBottomHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._web = QWebEngineView(self)
        self._web.setGeometry(self.rect())
        self._web.page().setBackgroundColor(Qt.GlobalColor.black)
        self._web.setHtml(_media_html(media_path, media_type), QUrl("about:blank"))

    def pause(self) -> None:
        self._web.page().runJavaScript(
            "document.querySelector('video')?.pause();"
        )

    def resume(self) -> None:
        self._web.page().runJavaScript(
            "const v=document.querySelector('video'); if(v){ v.play(); }"
        )

    def cleanup(self) -> None:
        self._web.setHtml("")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._web.setGeometry(self.rect())
