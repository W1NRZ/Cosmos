"""QWebChannel bridge between Python backend and web UI."""

from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from cosmos.library.manager import LibraryManager
from cosmos.settings import SettingsStore
from cosmos.wallpaper.service import WallpaperService


class CosmosBridge(QObject):
    """Exposed to JavaScript as `cosmos` via QWebChannel."""

    libraryChanged = pyqtSignal(str)
    wallpaperChanged = pyqtSignal(str)
    settingsChanged = pyqtSignal(str)
    toast = pyqtSignal(str, str)  # message, level

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._library = LibraryManager()
        self._wallpaper = WallpaperService()
        self._settings = SettingsStore()

    @pyqtSlot(result=str)
    def getLibrary(self) -> str:
        return json.dumps(self._library.serialize_all())

    @pyqtSlot(result=str)
    def getSettings(self) -> str:
        return json.dumps(self._settings.get())

    @pyqtSlot(result=str)
    def getWallpaperStatus(self) -> str:
        return json.dumps(self._wallpaper.get_status())

    @pyqtSlot(str, result=str)
    def importFile(self, source_path: str) -> str:
        ok, item, msg = self._library.import_file(source_path)
        if ok:
            self.libraryChanged.emit(json.dumps(self._library.serialize_all()))
            self.toast.emit(msg, "success")
            return json.dumps({"ok": True, "item": item})
        self.toast.emit(msg, "error")
        return json.dumps({"ok": False, "error": msg})

    @pyqtSlot(str, result=str)
    def applyWallpaper(self, item_id: str) -> str:
        item = self._library.get_item(item_id)
        if not item:
            msg = "Background not found"
            self.toast.emit(msg, "error")
            return json.dumps({"ok": False, "error": msg})

        ok, msg = self._wallpaper.apply(item_id, item["path"])
        if ok:
            self.wallpaperChanged.emit(json.dumps(self._wallpaper.get_status()))
            self.toast.emit(msg, "success")
            return json.dumps({"ok": True, "status": self._wallpaper.get_status()})
        self.toast.emit(msg, "error")
        return json.dumps({"ok": False, "error": msg})

    @pyqtSlot(str, result=str)
    def removeItem(self, item_id: str) -> str:
        if self._wallpaper.active_id == item_id:
            self._wallpaper.stop_media()
        ok, msg = self._library.remove_item(item_id)
        if ok:
            self.libraryChanged.emit(json.dumps(self._library.serialize_all()))
            self.wallpaperChanged.emit(json.dumps(self._wallpaper.get_status()))
            self.toast.emit(msg, "success")
            return json.dumps({"ok": True})
        self.toast.emit(msg, "error")
        return json.dumps({"ok": False, "error": msg})

    @pyqtSlot(str, str, result=str)
    def renameItem(self, item_id: str, new_name: str) -> str:
        ok, item, msg = self._library.rename_item(item_id, new_name)
        if ok:
            self.libraryChanged.emit(json.dumps(self._library.serialize_all()))
            self.toast.emit(msg, "success")
            return json.dumps({"ok": True, "item": item})
        self.toast.emit(msg, "error")
        return json.dumps({"ok": False, "error": msg})

    @pyqtSlot(str, result=str)
    def saveSettings(self, settings_json: str) -> str:
        try:
            settings = json.loads(settings_json)
            saved = self._settings.save(settings)
            self.settingsChanged.emit(json.dumps(saved))
            self.toast.emit("Settings saved", "success")
            return json.dumps({"ok": True, "settings": saved})
        except json.JSONDecodeError:
            msg = "Invalid settings payload"
            self.toast.emit(msg, "error")
            return json.dumps({"ok": False, "error": msg})

    @pyqtSlot(result=str)
    def resetSettings(self) -> str:
        saved = self._settings.reset()
        self.settingsChanged.emit(json.dumps(saved))
        self.toast.emit("Settings reset to defaults", "info")
        return json.dumps({"ok": True, "settings": saved})

    @pyqtSlot(result=str)
    def pickImportFile(self) -> str:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            None,
            "Import Background",
            str(Path.home()),
            "Media Files (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.heic "
            "*.mp4 *.mov *.m4v *.avi *.mkv *.webm);;All Files (*)",
        )
        if not path:
            return json.dumps({"ok": False, "cancelled": True})
        return self.importFile(path)

    @pyqtSlot(result=str)
    def pickImportFiles(self) -> str:
        from PyQt6.QtWidgets import QFileDialog

        paths, _ = QFileDialog.getOpenFileNames(
            None,
            "Import Backgrounds",
            str(Path.home()),
            "Media Files (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.heic "
            "*.mp4 *.mov *.m4v *.avi *.mkv *.webm);;All Files (*)",
        )
        if not paths:
            return json.dumps({"ok": False, "cancelled": True})

        imported = []
        errors = []
        for path in paths:
            ok, item, msg = self._library.import_file(path)
            if ok and item:
                imported.append(item)
            else:
                errors.append(f"{Path(path).name}: {msg}")

        self.libraryChanged.emit(json.dumps(self._library.serialize_all()))
        if imported:
            self.toast.emit(f"Imported {len(imported)} background(s)", "success")
        if errors:
            self.toast.emit(errors[0], "error")

        return json.dumps({"ok": bool(imported), "imported": imported, "errors": errors})
