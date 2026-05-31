"""Main PyQt6 application window."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from cosmos.bridge import CosmosBridge
from cosmos.config import APP_NAME

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class CosmosWindow(QMainWindow):
    """Primary application window hosting the web UI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1080, 720)
        self.resize(1280, 820)

        self._bridge = CosmosBridge(self)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QWebEngineView(container)
        settings = self._view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        channel = QWebChannel(self._view.page())
        channel.registerObject("cosmos", self._bridge)
        self._view.page().setWebChannel(channel)

        index = WEB_ROOT / "index.html"
        self._view.load(QUrl.fromLocalFile(str(index)))

        layout.addWidget(self._view)
        self.setCentralWidget(container)

        self._apply_macos_style()

    def _apply_macos_style(self) -> None:
        if sys.platform != "darwin":
            return
        try:
            self.setUnifiedTitleAndToolBarOnMac(True)
        except Exception:
            pass


def run() -> int:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Cosmos")

    window = CosmosWindow()
    window.show()
    return app.exec()
